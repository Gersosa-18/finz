# finz/app/models/alertas.py
from app.config.database import Base
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON, CheckConstraint
from sqlalchemy.orm import relationship

class Alertas(Base):
    __tablename__ = 'alertas'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    ticker = Column(String(10), nullable=False) # AAPL, TSLA, etc.
    campo = Column(String(15), nullable=False) # precio, volumen
    tipo_condicion = Column(String(15), nullable=True) # mayor_que, menor_que
    valor = Column(Float, nullable=True)
    activo = Column(Boolean, default=True)
    valor_maximo = Column(Float, nullable=True) # Para condiciones de rango
    valor_minimo = Column(Float, nullable=True)
    porcentaje_cambio = Column(Float, nullable=True) # Para condiciones de porcentaje
    tipo_alerta = Column(String(15), nullable=True, default="simple") # simple, rango, porcentaje, compuesta
    condiciones = Column(JSON, nullable=True) # Array de condiciones para alertas compuestas
    operador_logico = Column(String(3), nullable=True, default="AND") # AND, OR para alertas compuestas
    __table_args__ = (
        CheckConstraint('valor_minimo < valor_maximo', name='check_rango_valido'),
    )
    
    usuario = relationship("Usuarios", backref="alertas")