# finz/app/models/usuarios.py
from app.config.database import Base
from sqlalchemy import Column, Integer, String

class Usuarios(Base):

    __tablename__ = "usuarios"

    id = Column(Integer, primary_key = True)
    nombre= Column(String(25))
    correo= Column(String(100))
    contrasena= Column(String(255))