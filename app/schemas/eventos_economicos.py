# finz/app/schemas/eventos_economicos.py
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
from app.enums.eventos_economicos import ImpactoEvento

class EventoEconomicoBase(BaseModel):
    fecha: date = Field(..., description="Fecha del evento")
    pais: str = Field(..., min_length=2, max_length=50)
    evento: str = Field(..., min_length=5, max_length=200)
    impacto: ImpactoEvento
    activos_afectados: str = Field(..., min_length=1, max_length=300)

class EventoEconomicoCreate(EventoEconomicoBase):
    pass

class EventoEconomico(EventoEconomicoBase):
    id: int

    class Config:
        from_attributes = True
        json_schema_extra = {
            "examples": [
                {
                    "id": 1,
                    "fecha": "2025-07-20",
                    "pais": "EE.UU.",
                    "evento": "Decisión de tasas de la Fed",
                    "impacto": "alto",
                    "activos_afectados": "NASDAQ, SP500, USD"
                },
                {
                    "id": 2,
                    "fecha": "2025-07-22",
                    "pais": "EE.UU.",
                    "evento": "Reporte de empleo no agrícola",
                    "impacto": "medio",
                    "activos_afectados": "NASDAQ, SP500, bonos"
                }
            ]
        }