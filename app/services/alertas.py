from sqlalchemy.orm import Session
from app.models.alertas import Alertas as AlertasModel
from app.schemas.alertas import AlertaCreate, TipoCondicionEnum
from app.utils.precios_simulados import obtener_dato_simulado
from fastapi import HTTPException
from app.utils.analisis_sentimiento import analizar_sentimiento

class AlertasService:
   
    def __init__(self, db: Session) -> None:
        self.db = db
   
    def crear_alerta(self, alerta: AlertaCreate):
        """Crear una nueva alerta en la base de datos"""
        new_alerta = AlertasModel(**alerta.model_dump())

        if alerta.tipo_alerta == "rango":
            new_alerta.tipo_condicion = None
            new_alerta.valor = None
        elif alerta.tipo_alerta == "porcentaje":
            new_alerta.tipo_condicion = None
            new_alerta.valor_minimo = None
            new_alerta.valor_maximo = None
        elif alerta.tipo_alerta == "compuesta":
            new_alerta.tipo_condicion = None
            new_alerta.valor = None
            new_alerta.valor_minimo = None
            new_alerta.valor_maximo = None
            new_alerta.porcentaje_cambio = None

        self.db.add(new_alerta)
        self.db.commit()
        self.db.refresh(new_alerta)
        return new_alerta
   
    def obtener_alertas_usuario(self, user_id: int):
        """Obtener todas las alertas de un usuario específico"""
        result = self.db.query(AlertasModel).filter(AlertasModel.user_id == user_id).all()
        return result
   
    def evaluar_alertas(self, user_id: int, noticias_recientes: list[str] = None):
        """Evaluar alertas activas de un usuario y retornar las que se activaron"""
        alertas_activas = self.db.query(AlertasModel).filter(
            AlertasModel.user_id == user_id,
            AlertasModel.activo == True
        ).all()

        alertas_activadas = []

        # Análisis de sentimiento
        sentimiento_general = 'neutral'
        if noticias_recientes:
            sentimientos = [analizar_sentimiento(noticia) for noticia in noticias_recientes]
            positivos = sentimientos.count("positivo")
            negativos = sentimientos.count("negativo")
            if positivos > negativos:
                sentimiento_general = 'positivo'
            elif negativos > positivos:
                sentimiento_general = 'negativo'

        for alerta in alertas_activas:
            if self._evaluar_condicion_alerta(alerta) and self._filtrar_por_sentimiento(alerta, sentimiento_general):
                # Generar mensaje según tipo de alerta
                if alerta.tipo_alerta == "simple":
                    valor_actual = obtener_dato_simulado(alerta.ticker, alerta.campo)
                    simbolo = ">" if alerta.tipo_condicion == "mayor_que" else "<" if alerta.tipo_condicion == "menor_que" else "≈"
                    mensaje = f"{alerta.ticker} {alerta.campo} (${valor_actual}) {simbolo} ${alerta.valor}"
                
                elif alerta.tipo_alerta == "rango":
                    valor_actual = obtener_dato_simulado(alerta.ticker, alerta.campo)
                    mensaje = f"{alerta.ticker} {alerta.campo} (${valor_actual}) en rango ${alerta.valor_minimo}-${alerta.valor_maximo}"
                
                elif alerta.tipo_alerta == "porcentaje":
                    valor_actual = obtener_dato_simulado(alerta.ticker, alerta.campo)
                    cambio = ((valor_actual - alerta.valor) / alerta.valor) * 100
                    mensaje = f"{alerta.ticker} {alerta.campo} cambió {cambio:.1f}% (${alerta.valor} → ${valor_actual})"
                
                elif alerta.tipo_alerta == "compuesta":
                    condiciones_texto = []
                    for c in alerta.condiciones:
                        valor = obtener_dato_simulado(alerta.ticker, c["campo"])
                        simbolo = ">" if c["tipo_condicion"] == "mayor_que" else "<" if c["tipo_condicion"] == "menor_que" else "≈"
                        condiciones_texto.append(f"{c['campo']} {simbolo} {c['valor']}")
                    operador = " Y " if alerta.operador_logico == "AND" else " O "
                    mensaje = f"{alerta.ticker}: {operador.join(condiciones_texto)}"
                
                else:
                    mensaje = f"{alerta.ticker} - Alerta activada"

                alertas_activadas.append({
                    "id": alerta.id,
                    "mensaje": mensaje
                })

        return {
            "alertas_evaluadas": len(alertas_activas),
            "alertas_activadas": alertas_activadas,
            "total_activadas": len(alertas_activadas)
        }



    def _evaluar_condicion_alerta(self, alerta: AlertasModel) -> bool:
        """Evaluar si una alerta debe activarse"""
        # Obtener valor actual del ticker
        valor_actual = obtener_dato_simulado(alerta.ticker, alerta.campo)
        
        # Si no hay datos para ese ticker/campo, no activar
        if valor_actual is None:
            return False
        
        # evaluar si es compuesta
        if alerta.tipo_alerta == "compuesta":
            return self._evaluar_alerta_compuesta(alerta)

        # evaluar si es tipo rango
        if alerta.tipo_alerta == "rango":
            if alerta.valor_minimo is None or alerta.valor_maximo is None:
                return False
            return alerta.valor_minimo <= valor_actual <= alerta.valor_maximo

        # evaluar si es porcentaje
        if alerta.tipo_alerta == "porcentaje":
            if alerta.valor is None or alerta.porcentaje_cambio is None:
                return False
            cambio_porcentual = ((valor_actual - alerta.valor) / alerta.valor) * 100
            return cambio_porcentual <= alerta.porcentaje_cambio # Ej: -5% = caída

        # evaluar simple
        if alerta.tipo_condicion == "mayor_que":
            return valor_actual > alerta.valor
        elif alerta.tipo_condicion == "menor_que":
            return valor_actual < alerta.valor
        elif alerta.tipo_condicion == "igual_a":
            return abs(valor_actual - alerta.valor) < 0.01
        
        return False
    

    def _evaluar_alerta_compuesta(self, alerta: AlertasModel) -> bool:
        """Evaluar alerta compuesta con múltiples condiciones"""
        if not alerta.condiciones:
            return False
    
        resultados = []

        for condicion in alerta.condiciones:
            valor_actual = obtener_dato_simulado(alerta.ticker, condicion["campo"])
            if valor_actual is None:
                resultados.append(False)
                continue

            # Evaluar cada condicion
            if condicion["tipo_condicion"] == "mayor_que":
                resultados.append(valor_actual > condicion["valor"])
            elif condicion["tipo_condicion"] == "menor_que":
                resultados.append(valor_actual < condicion["valor"])
            elif condicion["tipo_condicion"] == "igual_a":
                resultados.append(abs(valor_actual - condicion["valor"]) < 0.01)
            else:
                resultados.append(False)

        # Aplicar operador lógico
        if alerta.operador_logico == "OR":
            return any(resultados) # Al menos una es true
        else:
            return all(resultados)
        

   
    # Métodos adicionales que podrías necesitar
    def obtener_alerta_por_id(self, alerta_id: int):
        result = self.db.query(AlertasModel).filter(AlertasModel.id == alerta_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="Alerta no encontrada")
        return result
   
    def desactivar_alerta(self, alerta_id: int):
        """Desactivar una alerta específica"""
        alerta = self.db.query(AlertasModel).filter(AlertasModel.id == alerta_id).first()
        if alerta:
            alerta.activo = False
            self.db.commit()
        return alerta
   
    def eliminar_alerta(self, alerta_id: int):
        """Eliminar una alerta"""
        self.db.query(AlertasModel).filter(AlertasModel.id == alerta_id).delete()
        self.db.commit()
        return
    
    def _filtrar_por_sentimiento(self, alerta: AlertasModel, sentimiento: str) -> bool:
        if sentimiento == "neutral":
            return True
        if (alerta.tipo_condicion == "menor_que" and sentimiento == "positivo"):
            return False
        if (alerta.tipo_condicion == "mayor_que" and sentimiento == "negativo"):
            return False
        return True