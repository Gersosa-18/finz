# finz/app/schemas/alertas.py
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class CampoEnum(str, Enum):
    PRECIO = "precio"
    VOLUMEN = "volumen"

class TipoCondicionEnum(str, Enum):
    MAYOR_QUE = "mayor_que"
    MENOR_QUE = "menor_que"
    IGUAL_A = "igual_a"

class AlertaBase(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10, description="Símbolo del activo financiero")
    campo: CampoEnum = Field(..., description="Campo a evaluar")
    tipo_condicion: TipoCondicionEnum = Field(..., description="Tipo de condición")
    valor: float = Field(..., gt=0, description="Valor a comparar")
    activo: Optional[bool] = True

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
                    "id": 1,
                    "user_id": 1,
                    "ticker": "AAPL",
                    "campo": "precio",
                    "tipo_condicion": "mayor_que",
                    "valor": 190.0,
                    "activo": True
                }
            ]
        }