# finz/app/models/alertas.py
from app.config.database import Base
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, CheckConstraint, Enum, func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.enums.alertas import CampoEnum, TipoCondicionEnum

# Modelo base con campos comunes / abstracto
class AlertaBase(Base):
    __abstract__ = True # Indicar que no cree tabla para esta clase

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    ticker = Column(String(10), nullable =False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Alerta Simple: precio > X, volumen < y
class AlertaSimple(AlertaBase):
    __tablename__ = 'alertas_simple'

    campo = Column(Enum(CampoEnum), nullable=False) # PRECIO, VOLUMEN
    tipo_condicion = Column(Enum(TipoCondicionEnum), nullable= False) # mayor_que, menor_que
    valor = Column(Float, nullable=False)

    usuario = relationship("Usuarios", backref="alertas_simple")

# Alertas de Rango: precio entre X e Y
class AlertaRango(AlertaBase):
    __tablename__ = 'alertas_rango'

    campo = Column(Enum(CampoEnum), nullable=False)
    valor_minimo = Column(Float, nullable=False)
    valor_maximo = Column(Float, nullable=False)

    __table_args__ = (
        CheckConstraint('valor_minimo < valor_maximo', name='check_rango_valido'),
    )

    usuario = relationship("Usuarios", backref="alertas_rango")

# Alerta de Porcentaje: precio cambió +5% o -10%
class AlertaPorcentaje(AlertaBase):
    __tablename__ = 'alertas_porcentaje'
    
    campo = Column(Enum(CampoEnum), nullable=False)
    porcentaje_cambio = Column(Float, nullable=False)  # +5.0 = subió 5%, -10.0 = bajó 10%
    periodo = Column(String(10), default="1d")  # 1d, 1h, 1w
    precio_referencia = Column(Float, nullable=True)  # Para tracking del cambio
    
    usuario = relationship("Usuarios", backref="alertas_porcentaje")

# Tabla para condiciones de alertas compuestas
class CondicionAlerta(Base):
    __tablename__ = 'condiciones_alerta'
    
    id = Column(Integer, primary_key=True)
    alerta_compuesta_id = Column(Integer, ForeignKey('alertas_compuesta.id'), nullable=False)
    campo = Column(Enum(CampoEnum), nullable=False)
    tipo_condicion = Column(Enum(TipoCondicionEnum), nullable=False)
    valor = Column(Float, nullable=False)
    orden = Column(Integer, nullable=False)  # Para mantener el orden

# Alerta Compuesta: (precio > X AND volumen > Y) OR (precio < Z)
class AlertaCompuesta(AlertaBase):
    __tablename__ = 'alertas_compuesta'
    
    operador_logico = Column(String(3), default="AND")  # AND, OR
    
    # Relación con las condiciones
    condiciones = relationship("CondicionAlerta", backref="alerta_compuesta", cascade="all, delete-orphan")
    usuario = relationship("Usuarios", backref="alertas_compuesta")