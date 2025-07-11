# fintrack/app/services/usuarios.py
from sqlalchemy.orm import Session
from app.models.usuarios import Usuarios as UsuariosModel
from app.schemas.usuarios import UsuarioCreate
from typing import List, Optional

class UsuariosService:
    
    def __init__(self, db: Session) -> None:
        self.db = db
    
    def crear_usuario(self, usuario: UsuarioCreate) -> UsuariosModel:
        """Crear un nuevo usuario en la base de datos"""
        # Verificar si el correo ya existe
        if self.verificar_correo_existe(usuario.correo):
            raise ValueError("El correo electrónico ya está registrado")
        
        nuevo_usuario = UsuariosModel(**usuario.model_dump())
        self.db.add(nuevo_usuario)
        self.db.commit()
        self.db.refresh(nuevo_usuario)
        return nuevo_usuario
    
    def obtener_todos_usuarios(self) -> List[UsuariosModel]:
        """Obtener todos los usuarios"""
        result = self.db.query(UsuariosModel).all()
        return result
    
    def obtener_usuario_por_id(self, usuario_id: int) -> Optional[UsuariosModel]:
        """Obtener un usuario específico por ID"""
        result = self.db.query(UsuariosModel).filter(UsuariosModel.id == usuario_id).first()
        return result
    
    def obtener_usuario_por_correo(self, correo: str) -> Optional[UsuariosModel]:
        """Obtener un usuario por su correo electrónico"""
        result = self.db.query(UsuariosModel).filter(UsuariosModel.correo == correo).first()
        return result
    
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
        result = self.db.query(UsuariosModel).offset(skip).limit(limit).all()
        return result