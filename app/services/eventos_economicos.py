# finz/app/services/eventos_economicos.py
from datetime import date, timedelta
from typing import List
from sqlalchemy.orm import Session
from app.models.eventos_economicos import EventoEconomico
from app.schemas.eventos_economicos import EventoEconomicoCreate
from app.enums.eventos_economicos import ImpactoEvento
from fastapi import HTTPException

class EventosEconomicosService:
    
    def __init__(self, db: Session, usar_simulados: bool = True):
        self.db = db
        self.usar_simulados = usar_simulados
    
    def get_eventos_hoy(self) -> List[dict]:
        """Obtener eventos de hoy"""
        if self.usar_simulados:
            from app.utils.eventos_provistos import get_eventos_hoy
            return get_eventos_hoy()
        
        # Cuando integres la API/BD real, usar esto:
        eventos_db = self.db.query(EventoEconomico).filter(
            EventoEconomico.fecha == date.today()
        ).all()
        return [self._modelo_to_dict(e) for e in eventos_db]
    
    def get_eventos_manana(self) -> List[dict]:
        """obtener eventos de mañana"""
        if self.usar_simulados:
            from app.utils.eventos_provistos import get_eventos_manana
            return get_eventos_manana()
        
        eventos_db = self.db.query(EventoEconomico).filter(
            EventoEconomico.fecha == date.today() + timedelta(days=1)
        ).all()
        return [self._modelo_to_dict(e) for e in eventos_db]
    
    def hay_eventos_alto_impacto_hoy(self) -> bool:
        """Verificar si hay eventos de alto impacto hoy"""
        if self.usar_simulados:
            from app.utils.eventos_provistos import hay_eventos_alto_impacto
            return hay_eventos_alto_impacto()
        
        eventos = self.get_eventos_hoy()
        return any(evento["impacto"] == ImpactoEvento.ALTO for evento in eventos)
    
    def _modelo_to_dict(self, evento: EventoEconomico) -> dict:
        """Convertir modelo de BD a dict para consistencia"""
        return {
            "fecha": evento.fecha,
            "pais": evento.pais,
            "evento": evento.evento,
            "impacto": evento.impacto,
            "activos_afectados": evento.activos_afectados
        }
    
    def get_evento_por_id(self, evento_id: int) -> EventoEconomico:
        """Obtener un evento por ID"""
        evento = self.db.query(EventoEconomico).filter(EventoEconomico.id == evento_id).first()
        if not evento:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
        return evento
    
    def crear_evento(self, evento_data: EventoEconomicoCreate) -> EventoEconomico:
        """Crear un nuevo evento económico - Solo para APIs/Scripts"""
        nuevo_evento = EventoEconomico(**evento_data.model_dump())
        self.db.add(nuevo_evento)
        self.db.commit()
        self.db.refresh(nuevo_evento)
        return nuevo_evento