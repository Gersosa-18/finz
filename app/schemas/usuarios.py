from pydantic import BaseModel, Field, EmailStr, SecretStr
from typing import Optional

class UsuarioBase(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=50)
    correo: Optional[EmailStr] = Field(None, max_length=100)

class UsuarioCreate(UsuarioBase):
    nombre: str = Field(..., min_length=2, max_length=50)
    correo: EmailStr = Field(..., max_length=100)
    contrasena: SecretStr = Field(..., min_length=6, max_length=100)

class UsuarioLogin(BaseModel):
    correo: EmailStr = Field(..., max_length=100)
    contrasena: SecretStr = Field(..., min_length=6, max_length=100)

class UsuarioUpdate(UsuarioBase):
    contrasena: Optional[SecretStr] = Field(None, min_length=6, max_length=100)

class Usuario(UsuarioBase):
    id: int
    class Config:
        from_attributes = True