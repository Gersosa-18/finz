# finz/app/services/usuarios.py
from sqlalchemy.orm import Session
from app.models.usuarios import Usuarios as UsuariosModel
from app.schemas.usuarios import UsuarioCreate
from typing import List, Optional
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UsuariosService:
    
    def __init__(self, db: Session) -> None:
        self.db = db
    
    def crear_usuario(self, usuario: UsuarioCreate) -> UsuariosModel:
        """Crear un nuevo usuario en la base de datos"""
        # Verificar si el correo ya existe
        if self.verificar_correo_existe(usuario.correo):
            raise ValueError("El correo electrónico ya está registrado")
        contrasena_str = usuario.contrasena.get_secret_value()
        hashed_password = pwd_context.hash(contrasena_str)

        nuevo_usuario = UsuariosModel(
            nombre=usuario.nombre,
            correo=usuario.correo,
            contrasena=hashed_password
        )
        self.db.add(nuevo_usuario)
        self.db.commit()
        self.db.refresh(nuevo_usuario)
        return nuevo_usuario
    
    def obtener_todos_usuarios(self) -> List[UsuariosModel]:
        return self.db.query(UsuariosModel).all()
    
    def obtener_usuario_por_id(self, usuario_id: int) -> Optional[UsuariosModel]:
        """Obtener un usuario específico por ID"""
        return self.db.query(UsuariosModel).filter(UsuariosModel.id == usuario_id).first()
        
    
    def obtener_usuario_por_correo(self, correo: str) -> Optional[UsuariosModel]:
        """Obtener un usuario por su correo electrónico"""
        return self.db.query(UsuariosModel).filter(UsuariosModel.correo == correo).first()
    
    def actualizar_usuario(self, usuario_id: int, usuario_data: UsuarioCreate) -> UsuariosModel:
        """Actualizar información de un usuario"""
        usuario = self.db.query(UsuariosModel).filter(UsuariosModel.id == usuario_id).first()
        
        if not usuario:
            raise ValueError("Usuario no encontrado")
        
        # Verificar si el nuevo correo ya existe (si se está actualizando)
        if usuario_data.correo and usuario_data.correo != usuario.correo:
            if self.verificar_correo_existe(usuario_data.correo):
                raise ValueError("El correo electrónico ya está registrado")
        
        # Actualizar los campos
        usuario.nombre = usuario_data.nombre
        usuario.correo = usuario_data.correo
        
        if usuario_data.contrasena:
            contrasena_str = usuario_data.contrasena.get_secret_value()
            usuario.contrasena = pwd_context.hash(contrasena_str)

        self.db.commit()
        self.db.refresh(usuario)
        return usuario
    
    def eliminar_usuario(self, usuario_id: int) -> bool:
        """Eliminar un usuario"""
        usuario = self.db.query(UsuariosModel).filter(UsuariosModel.id == usuario_id).first()
        if not usuario:
            raise ValueError("Usuario no encontrado")
        self.db.delete(usuario)
        self.db.commit()
        return True
    
    def verificar_usuario_existe(self, usuario_id: int) -> bool:
        """Verificar si un usuario existe"""
        result = self.db.query(UsuariosModel).filter(UsuariosModel.id == usuario_id).first()
        return result is not None
    
    def verificar_correo_existe(self, correo: str) -> bool:
        """Verificar si un correo electrónico ya está registrado"""
        result = self.db.query(UsuariosModel).filter(UsuariosModel.correo == correo).first()
        return result is not None
    
    def verificar_correo_disponible(self, correo: str) -> bool:
        """Verificar si un correo electrónico está disponible"""
        return not self.verificar_correo_existe(correo)
    
    def buscar_usuarios_por_nombre(self, nombre: str) -> List[UsuariosModel]:
        """Buscar usuarios por nombre (búsqueda parcial)"""
        result = self.db.query(UsuariosModel).filter(
            UsuariosModel.nombre.ilike(f"%{nombre}%")
        ).all()
        return result
    
    def contar_usuarios(self) -> int:
        """Contar el total de usuarios registrados"""
        return self.db.query(UsuariosModel).count()
    
    def obtener_usuarios_paginados(self, skip: int = 0, limit: int = 10) -> List[UsuariosModel]:
        """Obtener usuarios con paginación"""
        return self.db.query(UsuariosModel).offset(skip).limit(limit).all()
    
    def verificar_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica que la contraseña en texto plano coincida con el hash guardado"""
        return pwd_context.verify(plain_password, hashed_password)