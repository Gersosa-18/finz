# finz/app/schemas/alertas.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from app.enums.alertas import CampoEnum, TipoCondicionEnum

# ========== ALERTA SIMPLE ==========
class AlertaSimpleCreate(BaseModel):
    ticker: str = Field(..., max_length=10)
    campo: CampoEnum
    tipo_condicion: TipoCondicionEnum
    valor: float
   
    @field_validator('ticker')
    def ticker_uppercase(cls, v):
        return v.strip().upper()

class AlertaSimple(AlertaSimpleCreate):
    id: int
    user_id: int
    activo: bool
    created_at: datetime
   
    class Config:
        from_attributes = True

# ========== ALERTA RANGO ==========
class AlertaRangoCreate(BaseModel):
    ticker: str = Field(..., max_length=10)
    campo: CampoEnum
    valor_minimo: float
    valor_maximo: float
   
    @field_validator('ticker')
    def ticker_uppercase(cls, v):
        return v.strip().upper()
   
    @field_validator('valor_maximo')
    def validar_rango(cls, v, info):
        if info.data.get('valor_minimo') and v <= info.data['valor_minimo']:
            raise ValueError('valor_maximo debe ser mayor que valor_minimo')
        return v

class AlertaRango(AlertaRangoCreate):
    id: int
    user_id: int
    activo: bool
    created_at: datetime
   
    class Config:
        from_attributes = True

# ========== ALERTA PORCENTAJE ==========
class AlertaPorcentajeCreate(BaseModel):
    ticker: str = Field(..., max_length=10)
    campo: CampoEnum
    porcentaje_cambio: float
   
    @field_validator('ticker')
    def ticker_uppercase(cls, v):
        return v.strip().upper()

class AlertaPorcentaje(AlertaPorcentajeCreate):
    id: int
    user_id: int
    activo: bool
    created_at: datetime
    precio_referencia: Optional[float]
   
    class Config:
        from_attributes = True

# ========== CONDICION ALERTA ==========
class CondicionAlertaCreate(BaseModel):
    campo: CampoEnum
    tipo_condicion: TipoCondicionEnum
    valor: float
    orden: int

class CondicionAlerta(CondicionAlertaCreate):
    id: int
    alerta_compuesta_id: int
    
    class Config:
        from_attributes = True

# ========== ALERTA COMPUESTA ==========
class AlertaCompuestaCreate(BaseModel):
    ticker: str = Field(..., max_length=10)
    operador_logico: str = Field(default="AND", pattern="^(AND|OR)$")
    condiciones: List[CondicionAlertaCreate] = Field(min_length=2)
   
    @field_validator('ticker')
    def ticker_uppercase(cls, v):
        return v.strip().upper()

class AlertaCompuesta(BaseModel):
    id: int
    user_id: int
    ticker: str
    activo: bool
    created_at: datetime
    operador_logico: str
    condiciones: List[CondicionAlerta]
   
    class Config:
        from_attributes = True