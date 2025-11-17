# finz/app/routers/usuarios.py
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.middlewares.jwt_bearer import JWTBearer
from typing import List
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.schemas.usuarios import Usuario, UsuarioCreate, UsuarioLogin
from app.services.usuarios import UsuariosService
from app.utils.auth import (crear_token_jwt, crear_refresh_token, verificar_refresh_token)

usuarios_router = APIRouter()

@usuarios_router.get('/auth/hearbeat', tags=['Usuarios'])
def hearbeat(credentials: HTTPAuthorizationCredentials = Depends(JWTBearer())):
    """Validar sesión activa"""
    return {"status": "ok"}


@usuarios_router.post('/login', tags=['Usuarios'])
def login(usuario_login: UsuarioLogin, db: Session = Depends(get_db)):
    """Login y obtención de tokens"""
    service = UsuariosService(db)
    usuario = UsuariosService(db).obtener_usuario_por_correo(usuario_login.correo)

    if not usuario or not service.verificar_password(
        usuario_login.contrasena.get_secret_value(),
        usuario.contrasena
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Correo o contraseña incorrectos"
        )
    
    # Crear ambos tokens
    user_data = {"user_id": usuario.id, "correo": usuario.correo}
    access_token = crear_token_jwt(user_data)
    refresh_token = crear_refresh_token(user_data)

    return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
    }

@usuarios_router.post('/refresh', tags=['Usuarios'])
def refresh_token(refresh_token: str = Body(..., embed=True)):
    """Renueva el access token usando un refresh"""
    try:
        # Verificar refresh token
        payload = verificar_refresh_token(refresh_token)

        # Crear nuevo access token
        user_data = {
            "user_id": payload.get("user_id"),
            "correo": payload.get("correo")
        }
        new_access_token = crear_token_jwt(user_data)

        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error al renovar token"
        )


@usuarios_router.post('/usuarios', tags=['Usuarios'], status_code=status.HTTP_201_CREATED)
def post_crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """Crear un nuevo usuario"""
    try:
        nuevo_usuario = UsuariosService(db).crear_usuario(usuario)
        return {
            "message": "Usuario creado correctamente",
            "usuario_id": nuevo_usuario.id}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# @usuarios_router.get('/usuarios', tags=['Usuarios'], response_model=List[Usuario], dependencies=[Depends(JWTBearer())])
# def get_todos_usuarios(db: Session = Depends(get_db)):
#     """Obtener todos los usuarios"""
#     return UsuariosService(db).obtener_todos_usuarios()

# @usuarios_router.get('/usuarios/{usuario_id}', tags=['Usuarios'], response_model=Usuario, dependencies=[Depends(JWTBearer())])
# def get_usuario_por_id(usuario_id: int, db: Session = Depends(get_db)):
#     """Obtener un usuario específico por ID"""
#     result = UsuariosService(db).obtener_usuario_por_id(usuario_id)
#     if not result:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
#     return result

# @usuarios_router.get('/usuarios/correo/{correo}', tags=['Usuarios'], response_model=Usuario, dependencies=[Depends(JWTBearer())])
# def get_usuario_por_correo(correo: str, db: Session = Depends(get_db)):
#     """Obtener un usuario por su correo electrónico"""
#     result = UsuariosService(db).obtener_usuario_por_correo(correo)
#     if not result:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
#     return result

# @usuarios_router.put('/usuarios/{usuario_id}', tags=['Usuarios'], dependencies=[Depends(JWTBearer())])
# def put_actualizar_usuario(usuario_id: int, usuario_data: UsuarioCreate, db: Session = Depends(get_db)):
#     """Actualizar información de un usuario"""
#     try:
#         UsuariosService(db).actualizar_usuario(usuario_id, usuario_data)
#         return {"message": "Usuario actualizado correctamente"}
#     except ValueError as e:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# @usuarios_router.delete('/usuarios/{usuario_id}', tags=['Usuarios'], dependencies=[Depends(JWTBearer())])
# def delete_usuario(usuario_id: int, db: Session = Depends(get_db)):
#     """Eliminar un usuario"""
#     try:
#         UsuariosService(db).eliminar_usuario(usuario_id)
#         return {"message": "Usuario eliminado correctamente"}
#     except ValueError as e:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# @usuarios_router.get('/usuarios/{usuario_id}/existe', tags=['Usuarios'], dependencies=[Depends(JWTBearer())])
# def get_verificar_usuario(usuario_id: int, db: Session = Depends(get_db)):
#     """Verificar si un usuario existe"""
#     existe = UsuariosService(db).verificar_usuario_existe(usuario_id)
#     return {"existe": existe}

# @usuarios_router.get('/usuarios/correo/{correo}/disponible', tags=['Usuarios'], dependencies=[Depends(JWTBearer())])
# def get_verificar_correo_disponible(correo: str, db: Session = Depends(get_db)):
#     """Verificar si un correo electrónico está disponible"""
#     disponible = UsuariosService(db).verificar_correo_disponible(correo)
#     return {"disponible": disponible}