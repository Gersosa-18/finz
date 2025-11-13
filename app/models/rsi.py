# app/models/rsi.py
from app.config.database import Base
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship

class RSI(Base):
    __tablename__ = "rsi_history"

    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, index=True)
    rsi_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)

class SeguimientoRSI(Base):
    __tablename__ = "seguimiento_rsi"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    ticker = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'ticker', name='unique_user_ticker'),
    )