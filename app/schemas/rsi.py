# app/schemas/rsi.py
from pydantic import BaseModel, Field
from datetime import datetime

class RSIResponse(BaseModel):
    ticker: str
    rsi_value: float
    timestamp: datetime
    signal: str

    class Config:
        from_attributes = True
    
class RSIHistory(BaseModel):
    ticker: str
    data: list[dict]

class SeguimientoCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)

class SeguimientoResponse(BaseModel):
    id: int
    ticker: str
    created_at: datetime

    class Config:
        from_attributes =True
    
class RSIConEstado(BaseModel):
    ticker: str
    rsi_value: float | None = None
    timestamp: datetime | None = None
    signal: str | None | None
    proxima_actualizacion: str
    tiene_datos: bool
    es_dato_en_vivo: bool