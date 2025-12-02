from pydantic import BaseModel
from datetime import datetime
from typing import List

class ReporteResponse(BaseModel):
    id: int
    resumen_groq: str
    fecha_inicio: datetime
    fecha_fin: datetime
    indices: List[dict]
    sectores: List[dict]
    created_at: datetime

    class Config:
        from_attributes = True