# finz/app/schemas/alertas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.enums.alertas import CampoEnum, TipoCondicionEnum, TipoAlertaEnum
class CondicionCompuesta(BaseModel):
    campo: CampoEnum
    tipo_condicion: TipoCondicionEnum
    valor: float

class AlertaBase(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10, description="Símbolo del activo financiero")
    campo: Optional[CampoEnum] = None
    tipo_condicion: Optional[TipoCondicionEnum] = None
    valor: Optional[float] = None
    activo: Optional[bool] = True
    valor_maximo: Optional[float] = None
    valor_minimo: Optional[float] = None
    porcentaje_cambio: Optional[float] = None
    tipo_alerta: Optional[TipoAlertaEnum] = TipoAlertaEnum.SIMPLE
    condiciones: Optional[List[CondicionCompuesta]] = None
    operador_logico: Optional[str] = "AND"

class AlertaCreate(AlertaBase):
    user_id: int = Field(..., gt=0, description="ID del usuario")

class Alerta(AlertaBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
        json_schema_extra = {
            "examples": [
                {
                    # Alerta simple (como antes)
                    "id": 1,
                    "user_id": 1,
                    "ticker": "AAPL",
                    "campo": "precio",
                    "tipo_condicion": "mayor_que",
                    "valor": 190.0,
                    "activo": True,
                    "tipo_alerta": "simple"
                },
                {
                    # Alerta de rango
                    "id": 2,
                    "user_id": 1,
                    "ticker": "NVDA",
                    "campo": "precio",
                    "tipo_alerta": "rango",
                    "valor_minimo": 120.0,
                    "valor_maximo": 130.0,
                    "activo": True
                },
                {
                    # Alerta por porcentaje
                    "id": 3,
                    "user_id": 1,
                    "ticker": "TSLA",
                    "campo": "precio",
                    "tipo_alerta": "porcentaje",
                    "valor": 250.0,  # precio base
                    "porcentaje_cambio": -5.0,  # -5% = caída
                    "activo": True
                }
            ]
        }