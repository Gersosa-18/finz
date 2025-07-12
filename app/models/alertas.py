# finz/app/models/alertas.py
from app.config.database import Base
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

class Alertas(Base):
    __tablename__ = 'alertas'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    ticker = Column(String(10), nullable=False) # AAPL, TSLA, etc.
    campo = Column(String(15), nullable=False) # precio, volumen
    tipo_condicion = Column(String(15), nullable=False) # mayor_que, menor_que
    valor = Column(Float, nullable=False)
    activo = Column(Boolean, default=True)

    usuario = relationship("Usuarios", backref="alertas")