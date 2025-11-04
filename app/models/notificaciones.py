from app.config.database import Base
from sqlalchemy import Column, Integer, String, JSON

class Suscripcion(Base):
    __tablename__ = "suscripciones_push"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    subscription_data = Column(JSON, nullable=False)