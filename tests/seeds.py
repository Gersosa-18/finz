from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.models.usuarios import Usuarios

pwd = CryptContext(schemes=["bcrypt"])

def seed_usuario_demo(db: Session):
    usuario = Usuarios(
        nombre="Demo",
        correo="demo@finz.com",
        contrasena=pwd.hash("demo123"),
    )
    db.add(usuario)
    db.commit()