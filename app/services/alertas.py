# finz/app/services/alertas.py
from sqlalchemy.orm import Session, selectinload
from typing import Optional, List, Dict, Any
from app.models.alertas import AlertaSimple, AlertaRango, AlertaPorcentaje, AlertaCompuesta, CondicionAlerta
from app.schemas.alertas import AlertaSimpleCreate, AlertaRangoCreate, AlertaPorcentajeCreate, AlertaCompuestaCreate
from app.services.precios_service import PreciosService
from fastapi import HTTPException
from app.models.notificaciones import Suscripcion
from pywebpush import webpush
import json
import os
from datetime import datetime, timedelta

class AlertasService:
    _ultima_notif = {}
   
    def __init__(self, db: Session) -> None:
        self.db = db

    # ========== MÉTODOS DE CREACIÓN ESPECÍFICOS ==========
    def crear_alerta_simple(self, alerta: AlertaSimpleCreate, user_id: int):
        """Crear alerta simple"""
        new_alerta = AlertaSimple(
            user_id=user_id,
            ticker=alerta.ticker,
            campo=alerta.campo,
            tipo_condicion=alerta.tipo_condicion,
            valor=alerta.valor
        )
        self.db.add(new_alerta)
        self.db.commit()
        return new_alerta

    def crear_alerta_rango(self, alerta: AlertaRangoCreate, user_id: int):
        """Crear alerta de rango"""
        new_alerta = AlertaRango(
            user_id=user_id,
            ticker=alerta.ticker,
            campo=alerta.campo,
            valor_minimo=alerta.valor_minimo,
            valor_maximo=alerta.valor_maximo
        )
        self.db.add(new_alerta)
        self.db.commit()
        return new_alerta

    def crear_alerta_porcentaje(self, alerta: AlertaPorcentajeCreate, user_id: int):
        """Crear alerta de porcentaje"""
        # Obtener precio actual como referencia
        precio_actual = PreciosService.obtener_dato(alerta.ticker, alerta.campo)
        
        if precio_actual is None:
            raise HTTPException(status_code=404, detail=f"Ticker {alerta.ticker} no encontrado")

        new_alerta = AlertaPorcentaje(
            user_id=user_id,
            ticker=alerta.ticker,
            campo=alerta.campo,
            porcentaje_cambio=alerta.porcentaje_cambio,
            precio_referencia=precio_actual
        )
        self.db.add(new_alerta)
        self.db.commit()
        return new_alerta

    def crear_alerta_compuesta(self, alerta: AlertaCompuestaCreate, user_id: int):
        """Crear alerta compuesta"""
        new_alerta = AlertaCompuesta(
            user_id=user_id,
            ticker=alerta.ticker,
            operador_logico=alerta.operador_logico
        )
        self.db.add(new_alerta)
        self.db.commit()
        
        # Crear condiciones
        for condicion in alerta.condiciones:
            new_condicion = CondicionAlerta(
                alerta_compuesta_id=new_alerta.id,
                campo=condicion.campo,
                tipo_condicion=condicion.tipo_condicion,
                valor=condicion.valor,
                orden=condicion.orden
            )
            self.db.add(new_condicion)
        
        self.db.commit()
        return new_alerta

    # ========== MÉTODOS DE CONSULTA ==========
    def obtener_alertas_usuario(self, user_id: int):
        """Obtener todas las alertas de un usuario optimizando la carga de condiciones"""
        alertas_simple = self.db.query(AlertaSimple).filter(AlertaSimple.user_id == user_id).all()
        alertas_rango = self.db.query(AlertaRango).filter(AlertaRango.user_id == user_id).all()
        alertas_porcentaje = self.db.query(AlertaPorcentaje).filter(AlertaPorcentaje.user_id == user_id).all()
        alertas_compuesta = (
            self.db.query(AlertaCompuesta)
            .options(selectinload(AlertaCompuesta.condiciones))
            .filter(AlertaCompuesta.user_id == user_id)
            .all()
        )
        
        return {
            "simple": alertas_simple,
            "rango": alertas_rango,
            "porcentaje": alertas_porcentaje,
            "compuesta": alertas_compuesta
        }

    def obtener_alerta_por_id(self, alerta_id: int):
        """Obtener alerta por ID (busca en todas las tablas con eager load para compuestas)"""
        for model in [AlertaSimple, AlertaRango, AlertaPorcentaje, AlertaCompuesta]:
            query = self.db.query(model)
            if model == AlertaCompuesta:
                query = query.options(selectinload(AlertaCompuesta.condiciones))
            result = query.filter(model.id == alerta_id).first()
            if result:
                return result
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    # ========== HELPER DE PRECIOS Y CACHÉ ==========
    def _obtener_dato_con_cache(self, ticker: str, campo, cache_precios: dict) -> Optional[float]:
        """
        Obtiene el valor actual de mercado asegurando caché por (ticker, campo).
        Consulta primero la memoria local del ciclo, luego el cache de precios_job y finalmente PreciosService.
        """
        campo_str = campo.value if hasattr(campo, 'value') else str(campo).lower()
        key = f"{ticker.upper()}_{campo_str}"
        
        if key in cache_precios:
            return cache_precios[key]
        
        # Intentar obtener de la caché en memoria de precios_job si el campo solicitado es precio
        if campo_str == "precio":
            try:
                from app.jobs.precios_job import get_cache
                mercado_cache = get_cache()
                if ticker.upper() in mercado_cache and mercado_cache[ticker.upper()].get("price") is not None:
                    precio_cache = mercado_cache[ticker.upper()]["price"]
                    cache_precios[key] = precio_cache
                    return precio_cache
            except Exception:
                pass

        try:
            dato = PreciosService.obtener_dato(ticker, campo_str)
            cache_precios[key] = dato
            return dato
        except Exception:
            cache_precios[key] = None
            return None

    # ========== EVALUACIÓN DE ALERTAS ==========
    def evaluar_alertas(self, user_id: Optional[int] = None, noticias_recientes: list[str] = None):
        """
        Evalúa alertas activas minimizando la carga en base de datos.
        - Si user_id es None: evalúa todas las alertas activas globales en 4 consultas batch (para scheduler).
        - Si user_id es provisto: evalúa únicamente las alertas del usuario (para endpoint REST).
        """
        cache_precios = {}
        alertas_por_usuario: Dict[int, List[dict]] = {}
        todas_activadas: List[dict] = []
        ahora = datetime.now()
        sentimiento_general = 'neutral'

        # 1. Consultas optimizadas con pushdown SQL:
        # Se filtran solo alertas activas y que NO hayan sido activadas aún (excepto rango que conmuta)
        query_simple = self.db.query(AlertaSimple).filter(
            AlertaSimple.activo.is_(True),
            AlertaSimple.activada_at.is_(None)
        )
        query_rango = self.db.query(AlertaRango).filter(
            AlertaRango.activo.is_(True)
        )
        query_porcentaje = self.db.query(AlertaPorcentaje).filter(
            AlertaPorcentaje.activo.is_(True),
            AlertaPorcentaje.activada_at.is_(None)
        )
        query_compuesta = (
            self.db.query(AlertaCompuesta)
            .options(selectinload(AlertaCompuesta.condiciones))
            .filter(
                AlertaCompuesta.activo.is_(True),
                AlertaCompuesta.activada_at.is_(None)
            )
        )

        if user_id is not None:
            query_simple = query_simple.filter(AlertaSimple.user_id == user_id)
            query_rango = query_rango.filter(AlertaRango.user_id == user_id)
            query_porcentaje = query_porcentaje.filter(AlertaPorcentaje.user_id == user_id)
            query_compuesta = query_compuesta.filter(AlertaCompuesta.user_id == user_id)

        alertas_simple = query_simple.all()
        alertas_rango = query_rango.all()
        alertas_porcentaje = query_porcentaje.all()
        alertas_compuesta = query_compuesta.all()

        total_evaluadas = len(alertas_simple) + len(alertas_rango) + len(alertas_porcentaje) + len(alertas_compuesta)

        # 2. Evaluación en memoria utilizando caché compartida
        for alerta in alertas_simple:
            if alerta.activada_at:
                continue
            try:
                if self._evaluar_alerta_simple(alerta, sentimiento_general, cache_precios):
                    item = {"id": f"simple-{alerta.id}", "mensaje": self._generar_mensaje_simple(alerta, cache_precios)}
                    alertas_por_usuario.setdefault(alerta.user_id, []).append(item)
                    todas_activadas.append(item)
                    alerta.activada_at = ahora
            except Exception:
                continue

        for alerta in alertas_rango:
            try:
                dentro_del_rango = self._evaluar_alerta_rango(alerta, cache_precios)

                # ENTRADA AL RANGO
                if dentro_del_rango and not alerta.activada_at:
                    item = {
                        "id": f"rango-entrada-{alerta.id}",
                        "mensaje": f"📊 {alerta.ticker} ENTRÓ al rango ${alerta.valor_minimo}-${alerta.valor_maximo}"
                    }
                    alertas_por_usuario.setdefault(alerta.user_id, []).append(item)
                    todas_activadas.append(item)
                    alerta.activada_at = ahora
                # SALIDA DEL RANGO
                elif not dentro_del_rango and alerta.activada_at:
                    valor_actual = self._obtener_dato_con_cache(alerta.ticker, alerta.campo, cache_precios)
                    valor_str = f"${valor_actual}" if valor_actual is not None else "N/A"
                    item = {
                        "id": f"rango-salida-{alerta.id}",
                        "mensaje": f"⚠️ {alerta.ticker} SALIÓ del rango (ahora {valor_str})"
                    }
                    alertas_por_usuario.setdefault(alerta.user_id, []).append(item)
                    todas_activadas.append(item)
                    alerta.activada_at = None # Resetear

            except Exception:
                continue

        for alerta in alertas_porcentaje:
            if alerta.activada_at:
                continue
            try:
                if self._evaluar_alerta_porcentaje(alerta, cache_precios):
                    item = {"id": f"porcentaje-{alerta.id}", "mensaje": self._generar_mensaje_porcentaje(alerta, cache_precios)}
                    alertas_por_usuario.setdefault(alerta.user_id, []).append(item)
                    todas_activadas.append(item)
                    alerta.activada_at = ahora
            except Exception:
                continue

        for alerta in alertas_compuesta:
            if alerta.activada_at:
                continue
            try:
                if self._evaluar_alerta_compuesta(alerta, cache_precios):
                    item = {"id": f"compuesta-{alerta.id}", "mensaje": self._generar_mensaje_compuesta(alerta)}
                    alertas_por_usuario.setdefault(alerta.user_id, []).append(item)
                    todas_activadas.append(item)
                    alerta.activada_at = ahora
            except Exception:
                continue

        # 3. Commit único y atómico para todas las actualizaciones del lote
        self.db.commit()

        # 4. Notificaciones push enviadas en lote
        if alertas_por_usuario:
            vapid_private_key = os.getenv("VAPID_PRIVATE_KEY")
            vapid_email = os.getenv("VAPID_EMAIL")

            # Batch query: una sola consulta para todas las suscripciones de los usuarios afectados
            usuarios_afectados = list(alertas_por_usuario.keys())
            suscripciones = (
                self.db.query(Suscripcion)
                .filter(Suscripcion.user_id.in_(usuarios_afectados))
                .all()
            )
            suscripciones_map = {s.user_id: s for s in suscripciones}

            for uid, user_alertas in alertas_por_usuario.items():
                ultima = self._ultima_notif.get(uid)
                if not ultima or (ahora - ultima) > timedelta(minutes=5):
                    suscripcion = suscripciones_map.get(uid)
                    if suscripcion and vapid_private_key and vapid_email:
                        try:
                            mensajes = [a["mensaje"] for a in user_alertas]
                            body = "\n".join(mensajes) if len(mensajes) <= 3 else f"{mensajes[0]}\n... y {len(mensajes)-1} más"
                            webpush(
                                subscription_info=suscripcion.subscription_data,
                                data=json.dumps({
                                    "title": f"🔔 {len(user_alertas)} Alerta(s) Activada(s)", 
                                    "body": body
                                }),
                                vapid_private_key=vapid_private_key,
                                vapid_claims={"sub": f"mailto:{vapid_email}"}
                            )
                            self._ultima_notif[uid] = ahora
                        except Exception as e:
                            print(f"Error enviando push a usuario {uid}: {e}")

        return {
            "alertas_evaluadas": total_evaluadas,
            "alertas_activadas": todas_activadas,
            "total_activadas": len(todas_activadas)
        }

    # ========== MÉTODOS PRIVADOS DE EVALUACIÓN ==========
    def _evaluar_alerta_simple(self, alerta, sentimiento, cache_precios):
        valor_actual = self._obtener_dato_con_cache(alerta.ticker, alerta.campo, cache_precios)
        if valor_actual is None:
            return False
        
        tipo_cond = alerta.tipo_condicion.value if hasattr(alerta.tipo_condicion, "value") else str(alerta.tipo_condicion)

        # Filtrar por sentimiento
        if sentimiento == "positivo" and tipo_cond == "menor_que":
            return False
        if sentimiento == "negativo" and tipo_cond == "mayor_que":
            return False
        
        if tipo_cond == "mayor_que":
            return valor_actual > alerta.valor
        elif tipo_cond == "menor_que":
            return valor_actual < alerta.valor
        return False

    def _evaluar_alerta_rango(self, alerta, cache_precios):
        valor_actual = self._obtener_dato_con_cache(alerta.ticker, alerta.campo, cache_precios)
        if valor_actual is None:
            return False
        return alerta.valor_minimo <= valor_actual <= alerta.valor_maximo

    def _evaluar_alerta_porcentaje(self, alerta, cache_precios):
        if not alerta.precio_referencia:
            return False
        valor_actual = self._obtener_dato_con_cache(alerta.ticker, alerta.campo, cache_precios)
        if valor_actual is None:
            return False
        
        cambio_porcentual = ((valor_actual - alerta.precio_referencia) / alerta.precio_referencia) * 100
        return abs(cambio_porcentual) >= abs(alerta.porcentaje_cambio)

    def _evaluar_alerta_compuesta(self, alerta, cache_precios):
        if not alerta.condiciones:
            return False
        
        resultados = []
        for condicion in alerta.condiciones:
            valor_actual = self._obtener_dato_con_cache(alerta.ticker, condicion.campo, cache_precios)
            if valor_actual is None:
                resultados.append(False)
                continue

            tipo_cond = condicion.tipo_condicion.value if hasattr(condicion.tipo_condicion, "value") else str(condicion.tipo_condicion)
            if tipo_cond == "mayor_que":
                resultados.append(valor_actual > condicion.valor)
            elif tipo_cond == "menor_que":
                resultados.append(valor_actual < condicion.valor)
            else:
                resultados.append(False)

        return any(resultados) if alerta.operador_logico == "OR" else all(resultados)

    # ========== GENERADORES DE MENSAJES ==========
    def _generar_mensaje_simple(self, alerta, cache_precios):
        valor_actual = self._obtener_dato_con_cache(alerta.ticker, alerta.campo, cache_precios)
        campo_str = alerta.campo.value if hasattr(alerta.campo, "value") else str(alerta.campo)

        if valor_actual is None:
            return f"{alerta.ticker} {campo_str} - Precio no disponible"
        
        tipo_cond = alerta.tipo_condicion.value if hasattr(alerta.tipo_condicion, "value") else str(alerta.tipo_condicion)
        simbolo = ">" if tipo_cond == "mayor_que" else "<"
        return f"{alerta.ticker} {campo_str} (${valor_actual}) {simbolo} ${alerta.valor}"

    def _generar_mensaje_rango(self, alerta, cache_precios):
        valor_actual = self._obtener_dato_con_cache(alerta.ticker, alerta.campo, cache_precios)
        campo_str = alerta.campo.value if hasattr(alerta.campo, "value") else str(alerta.campo)
        if valor_actual is None:
            return f"{alerta.ticker} {campo_str} - Precio no disponible"
        
        # Determinar si entró o salió
        dentro = alerta.valor_minimo <= valor_actual <= alerta.valor_maximo
        if dentro:
            return f"📊 {alerta.ticker} ENTRÓ al rango ${alerta.valor_minimo}-${alerta.valor_maximo} (${valor_actual})"
        else:
            return f"⚠️ {alerta.ticker} SALIÓ del rango (${valor_actual})"

    def _generar_mensaje_porcentaje(self, alerta, cache_precios):
        valor_actual = self._obtener_dato_con_cache(alerta.ticker, alerta.campo, cache_precios)
        campo_str = alerta.campo.value if hasattr(alerta.campo, "value") else str(alerta.campo)
        if valor_actual is None:
            return f"{alerta.ticker} {campo_str} - Precio no disponible"
        cambio = ((valor_actual - alerta.precio_referencia) / alerta.precio_referencia) * 100
        return f"{alerta.ticker} {campo_str} cambió {cambio:.1f}%"

    def _generar_mensaje_compuesta(self, alerta):
        return f"{alerta.ticker} - Alerta compuesta activada"

    # ========== GESTIÓN DE ALERTAS ==========
    def desactivar_alerta(self, alerta_id: int):
        """Desactivar alerta (busca en todas las tablas)"""
        for model in [AlertaSimple, AlertaRango, AlertaPorcentaje, AlertaCompuesta]:
            alerta = self.db.query(model).filter(model.id == alerta_id).first()
            if alerta:
                alerta.activo = False
                self.db.commit()
                return alerta
        return None

    def eliminar_alerta(self, alerta_id: int):
        """Eliminar alerta (busca en todas las tablas)"""
        for model in [AlertaSimple, AlertaRango, AlertaPorcentaje, AlertaCompuesta]:
            deleted = self.db.query(model).filter(model.id == alerta_id).delete()
            if deleted:
                self.db.commit()
                return True
        return False