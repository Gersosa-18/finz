# finz/app/models/eventos.py
from app.config.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Enum
from app.enums.eventos import TipoEvento, ImpactoEvento

class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True)
    fecha = Column(DateTime, nullable=False)
    ticker = Column(String(10), nullable=True)   # NULL = evento macro (ej: Fed)
    tipo = Column(Enum(TipoEvento), nullable=False)  # FOMC, EARNINGS, DIVIDEND, SPLIT
    descripcion = Column(String(200), nullable=False)
    impacto = Column(Enum(ImpactoEvento), nullable=True)  # LOW, MEDIUM, HIGH
