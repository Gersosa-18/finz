# fintrack/app/schemas/usuarios.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50)
    correo: EmailStr = Field(..., max_length=100)
class UsuarioCreate(UsuarioBase):
    pass

class Usuario(UsuarioBase):
    id: int
   
    class Config:
        from_attributes = True