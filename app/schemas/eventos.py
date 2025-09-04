# finz/app/schemas/eventos.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.enums.eventos import TipoEvento, ImpactoEvento

class EventoBase(BaseModel):
    fecha: datetime
    ticker: Optional[str] = None
    tipo: TipoEvento
    descripcion: str
    impacto: Optional[ImpactoEvento] = None

class EventoCreate(EventoBase):
    pass

class EventoResponse(EventoBase):
    id: int
    
    class Config:
        from_attributes = True

class RiesgoResponse(BaseModel):
    ticker: str
    fecha: str
    riesgo: str  # "ALTO", "MEDIO", "BAJO", "SIN_RIESGO"
    eventos: List[str]  # Lista de descripciones