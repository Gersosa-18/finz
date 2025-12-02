# finz/app/models/reportes.py
from app.config.database import Base
from sqlalchemy import Column, Integer, DateTime, JSON, Text, func

class Reporte(Base):
    __tablename__ ="reportes"

    id = Column(Integer, primary_key=True)
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)
    resumen_groq = Column(Text, nullable=False)
    sectores_json = Column(JSON, nullable=False)
    indices_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=func.now())