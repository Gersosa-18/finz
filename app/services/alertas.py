from sqlalchemy.orm import Session
from app.models.alertas import Alertas as AlertasModel
from app.schemas.alertas import AlertaCreate, TipoCondicionEnum
from app.utils.precios_simulados import obtener_dato_simulado

class AlertasService:
   
    def __init__(self, db: Session) -> None:
        self.db = db
   
    def crear_alerta(self, alerta: AlertaCreate):
        """Crear una nueva alerta en la base de datos"""
        new_alerta = AlertasModel(**alerta.model_dump())
        self.db.add(new_alerta)
        self.db.commit()
        self.db.refresh(new_alerta)
        return new_alerta
   
    def obtener_alertas_usuario(self, user_id: int):
        """Obtener todas las alertas de un usuario específico"""
        result = self.db.query(AlertasModel).filter(AlertasModel.user_id == user_id).all()
        return result
   
    def evaluar_alertas(self, user_id: int):
        """Evaluar alertas activas de un usuario y retornar las que se activaron"""
        alertas_activas = self.db.query(AlertasModel).filter(
            AlertasModel.user_id == user_id,
            AlertasModel.activo == True
        ).all()
    
        alertas_activadas = []
    
        for alerta in alertas_activas:
            valor_actual = obtener_dato_simulado(alerta.ticker, alerta.campo)
            if valor_actual is None:
                continue

            if self._evaluar_condicion_alerta(alerta):
                # Armamos un mensaje descriptivo para la UX
                if alerta.tipo_condicion == TipoCondicionEnum.MAYOR_QUE:
                    simbolo = ">"
                elif alerta.tipo_condicion == TipoCondicionEnum.MENOR_QUE:
                    simbolo = "<"
                elif alerta.tipo_condicion == TipoCondicionEnum.IGUAL_A:
                    simbolo = "≈"
                else:
                    simbolo = "?"

                mensaje = (
                    f"{alerta.ticker} {alerta.campo} actual (${valor_actual}) "
                    f"{simbolo} ${alerta.valor}"
                )

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
        
        # Aplicar condición
        if alerta.tipo_condicion == "mayor_que":
            return valor_actual > alerta.valor
        elif alerta.tipo_condicion == "menor_que":
            return valor_actual < alerta.valor
        elif alerta.tipo_condicion == "igual_a":
            return abs(valor_actual - alerta.valor) < 0.01
        
        return False
   
    # Métodos adicionales que podrías necesitar
    def obtener_alerta_por_id(self, alerta_id: int):
        """Obtener una alerta específica por ID"""
        result = self.db.query(AlertasModel).filter(AlertasModel.id == alerta_id).first()
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