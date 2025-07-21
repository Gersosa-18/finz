from app.config.database import Base
from app.enums.eventos_economicos import ImpactoEvento
from sqlalchemy import Column, Integer, String, Date, Enum

class EventoEconomico(Base):
    __tablename__ = "eventos_economicos"
    id = Column(Integer, primary_key=True)
    fecha = Column(Date, nullable=False)
    pais = Column(String(50), nullable=False)
    evento = Column(String(200), nullable=False)
    impacto = Column(Enum(ImpactoEvento), nullable=False)
    activos_afectados = Column(String(300), nullable=False)