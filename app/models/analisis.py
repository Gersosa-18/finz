from pydantic import BaseModel, Field, field_validator

class AnalisisResponse(BaseModel):
    ticker: str
    timeframe: str
    agente_tecnico: str
    agente_fundamental: str
    moderador: str
    veredicto: str 
    