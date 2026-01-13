# finz/app/services/alertas.py
from sqlalchemy.orm import Session
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
    def crear_alerta_simple(self, alerta: AlertaSimpleCreate, user_id: int = 1):
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

    def crear_alerta_rango(self, alerta: AlertaRangoCreate, user_id: int = 1):
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

    def crear_alerta_porcentaje(self, alerta: AlertaPorcentajeCreate, user_id: int = 1):
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
            periodo=alerta.periodo,
            precio_referencia=precio_actual
        )
        self.db.add(new_alerta)
        self.db.commit()
        return new_alerta

    def crear_alerta_compuesta(self, alerta: AlertaCompuestaCreate, user_id: int = 1):
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
        """Obtener todas las alertas de un usuario"""
        alertas_simple = self.db.query(AlertaSimple).filter(AlertaSimple.user_id == user_id).all()
        alertas_rango = self.db.query(AlertaRango).filter(AlertaRango.user_id == user_id).all()
        alertas_porcentaje = self.db.query(AlertaPorcentaje).filter(AlertaPorcentaje.user_id == user_id).all()
        alertas_compuesta = self.db.query(AlertaCompuesta).filter(AlertaCompuesta.user_id == user_id).all()
        
        return {
            "simple": alertas_simple,
            "rango": alertas_rango,
            "porcentaje": alertas_porcentaje,
            "compuesta": alertas_compuesta
        }

    def obtener_alerta_por_id(self, alerta_id: int):
        """Obtener alerta por ID (busca en todas las tablas)"""
        # Buscar en cada tipo de alerta
        for model in [AlertaSimple, AlertaRango, AlertaPorcentaje, AlertaCompuesta]:
            result = self.db.query(model).filter(model.id == alerta_id).first()
            if result:
                return result
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    # ========== EVALUACIÓN DE ALERTAS ==========
    def evaluar_alertas(self, user_id: int, noticias_recientes: list[str] = None):
        """Evaluar todas las alertas activas de un usuario"""
        alertas_activadas = []
        cache_precios = {}
        
        # Obtener todas las alertas activas
        alertas_simple = self.db.query(AlertaSimple).filter(AlertaSimple.user_id == user_id, AlertaSimple.activo == True).all()
        alertas_rango = self.db.query(AlertaRango).filter(AlertaRango.user_id == user_id, AlertaRango.activo == True).all()
        alertas_porcentaje = self.db.query(AlertaPorcentaje).filter(AlertaPorcentaje.user_id == user_id, AlertaPorcentaje.activo == True).all()
        alertas_compuesta = self.db.query(AlertaCompuesta).filter(AlertaCompuesta.user_id == user_id, AlertaCompuesta.activo == True).all()

        # Análisis de sentimiento
        sentimiento_general = 'neutral'
        # if noticias_recientes:
        #     sentimientos = [analizar_sentimiento(noticia) for noticia in noticias_recientes]
        #     positivos = sentimientos.count("positivo")
        #     negativos = sentimientos.count("negativo")
        #     if positivos > negativos:
        #         sentimiento_general = 'positivo'
        #     elif negativos > positivos:
        #         sentimiento_general = 'negativo'

        # Evaluar cada tipo de alerta con CACHE
        for alerta in alertas_simple:
            if alerta.activada_at:
                continue
            try:
                if self._evaluar_alerta_simple(alerta, sentimiento_general, cache_precios):
                    alertas_activadas.append({"id": f"simple-{alerta.id}", "mensaje": self._generar_mensaje_simple(alerta, cache_precios)})
                    alerta.activada_at = datetime.now()
            except HTTPException:
                continue

        for alerta in alertas_rango:
            try:
                dentro_del_rango = self._evaluar_alerta_rango(alerta, cache_precios)

                # ENTRADA AL RANGO
                if dentro_del_rango and not alerta.activada_at:
                    alertas_activadas.append({
                        "id": f"rango-entrada-{alerta.id}",
                        "mensaje": f"📊 {alerta.ticker} ENTRÓ al rango ${alerta.valor_minimo}-${alerta.valor_maximo}"
                    })
                    alerta.activada_at = datetime.now()
                # SALIDA DEL RANGO
                elif not dentro_del_rango and alerta.activada_at:
                    key = f"{alerta.ticker}_{alerta.campo.value}"
                    if key not in cache_precios:
                        cache_precios[key] = PreciosService.obtener_dato(alerta.ticker, alerta.campo)
                    valor_actual = cache_precios.get(key, "N/A")
                    
                    alertas_activadas.append({
                        "id": f"rango-salida-{alerta.id}",
                        "mensaje": f"⚠️ {alerta.ticker} SALIÓ del rango (ahora ${valor_actual})"
                    })
                    alerta.activada_at = None # Resetear

            except HTTPException:
                continue

        for alerta in alertas_porcentaje:
            if alerta.activada_at:
                continue
            try:
                if self._evaluar_alerta_porcentaje(alerta, cache_precios):
                    alertas_activadas.append({"id": f"porcentaje-{alerta.id}", "mensaje": self._generar_mensaje_porcentaje(alerta, cache_precios)})
                    alerta.activada_at = datetime.now()
            except HTTPException:
                continue

        for alerta in alertas_compuesta:
            if alerta.activada_at:
                continue
            try:
                if self._evaluar_alerta_compuesta(alerta, cache_precios):
                    alertas_activadas.append({"id": f"compuesta-{alerta.id}", "mensaje": self._generar_mensaje_compuesta(alerta, cache_precios)})
                    alerta.activada_at = datetime.now()
            except HTTPException:  
                continue
            
        self.db.commit()

        if alertas_activadas:
            ahora = datetime.now()
            ultima = self._ultima_notif.get(user_id)
            
            if not ultima or (ahora - ultima) > timedelta(minutes=5):
                try:
                    suscripcion = self.db.query(Suscripcion).filter(
                        Suscripcion.user_id == user_id
                    ).first()
                    
                    if suscripcion:
                        # Enviar notificación con el detalle de TODAS las alertas
                        mensajes = [a["mensaje"] for a in alertas_activadas]
                        body = "\n".join(mensajes) if len(mensajes) <= 3 else f"{mensajes[0]}\n... y {len(mensajes)-1} más"
                        
                        webpush(
                            subscription_info=suscripcion.subscription_data,
                            data=json.dumps({
                                "title": f"🔔 {len(alertas_activadas)} Alerta(s) Activada(s)", 
                                "body": body
                            }),
                            vapid_private_key=os.getenv("VAPID_PRIVATE_KEY"),
                            vapid_claims={"sub": f"mailto:{os.getenv('VAPID_EMAIL')}"}
                        )
                        self._ultima_notif[user_id] = ahora
                except Exception as e:
                    print(f"Error enviando push: {e}")

        return {
            "alertas_evaluadas": len(alertas_simple) + len(alertas_rango) + len(alertas_porcentaje) + len(alertas_compuesta),
            "alertas_activadas": alertas_activadas,
            "total_activadas": len(alertas_activadas)
        }

    # ========== MÉTODOS PRIVADOS DE EVALUACIÓN ==========
    def _evaluar_alerta_simple(self, alerta, sentimiento, cache_precios):
        key = f"{alerta.ticker}_{alerta.campo.value}"
        if key not in cache_precios:
            cache_precios[key] = PreciosService.obtener_dato(alerta.ticker, alerta.campo)
        
        valor_actual = cache_precios[key]
        if valor_actual is None:
            return False
        
        # Filtrar por sentimiento
        if sentimiento == "positivo" and alerta.tipo_condicion.value == "menor_que":
            return False
        if sentimiento == "negativo" and alerta.tipo_condicion.value == "mayor_que":
            return False
        
        if alerta.tipo_condicion.value == "mayor_que":
            return valor_actual > alerta.valor
        elif alerta.tipo_condicion.value == "menor_que":
            return valor_actual < alerta.valor
        return False

    def _evaluar_alerta_rango(self, alerta, cache_precios):
        key = f"{alerta.ticker}_{alerta.campo.value}"
        if key not in cache_precios:
            cache_precios[key] = PreciosService.obtener_dato(alerta.ticker, alerta.campo)
        valor_actual = cache_precios.get(key)
        if valor_actual is None:
            return False
        return alerta.valor_minimo <= valor_actual <= alerta.valor_maximo

    def _evaluar_alerta_porcentaje(self, alerta, cache_precios):
        key = f"{alerta.ticker}_{alerta.campo.value}"
        if key not in cache_precios:
            cache_precios[key] = PreciosService.obtener_dato(alerta.ticker, alerta.campo)
        if not alerta.precio_referencia:
            return False
        valor_actual = cache_precios.get(key)
        if valor_actual is None:
            return False
        
        cambio_porcentual = ((valor_actual - alerta.precio_referencia) / alerta.precio_referencia) * 100
        return abs(cambio_porcentual) >= abs(alerta.porcentaje_cambio)

    def _evaluar_alerta_compuesta(self, alerta, cache_precios):
        key = f"{alerta.ticker}_{alerta.campo.value}"
        if not alerta.condiciones:
            return False
        
        resultados = []
        for condicion in alerta.condiciones:
            valor_actual = PreciosService.obtener_dato(alerta.ticker, condicion.campo)
            if valor_actual is None:
                resultados.append(False)
                continue

            if condicion.tipo_condicion.value == "mayor_que":
                resultados.append(valor_actual > condicion.valor)
            elif condicion.tipo_condicion.value == "menor_que":
                resultados.append(valor_actual < condicion.valor)
            else:
                resultados.append(False)

        return any(resultados) if alerta.operador_logico == "OR" else all(resultados)

    # ========== GENERADORES DE MENSAJES ==========
    def _generar_mensaje_simple(self, alerta, cache_precios):
        key = f"{alerta.ticker}_{alerta.campo.value}"
        valor_actual = cache_precios.get(key)

        if valor_actual is None:
            return f"{alerta.ticker} {alerta.campo.value} - Precio no disponible"
        
        simbolo = ">" if alerta.tipo_condicion.value == "mayor_que" else "<"
        return f"{alerta.ticker} {alerta.campo.value} (${valor_actual}) {simbolo} ${alerta.valor}"

    def _generar_mensaje_rango(self, alerta, cache_precios):
        key = f"{alerta.ticker}_{alerta.campo.value}"
        valor_actual = cache_precios.get(key)
        if valor_actual is None:
            return f"{alerta.ticker} {alerta.campo.value} - Precio no disponible"
        
        # Determinar si entró o salió
        dentro = alerta.valor_minimo <= valor_actual <= alerta.valor_maximo
        if dentro:
            return f"📊 {alerta.ticker} ENTRÓ al rango ${alerta.valor_minimo}-${alerta.valor_maximo} (${valor_actual})"
        else:
            return f"⚠️ {alerta.ticker} SALIÓ del rango (${valor_actual})"

    def _generar_mensaje_porcentaje(self, alerta, cache_precios):
        key = f"{alerta.ticker}_{alerta.campo.value}"
        valor_actual = cache_precios.get(key)
        if valor_actual is None:
            return f"{alerta.ticker} {alerta.campo.value} - Precio no disponible"
        cambio = ((valor_actual - alerta.precio_referencia) / alerta.precio_referencia) * 100
        return f"{alerta.ticker} {alerta.campo.value} cambió {cambio:.1f}%"

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