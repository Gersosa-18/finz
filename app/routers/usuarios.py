# finz/app/routers/usuarios.py
from fastapi import APIRouter, Depends, HTTPException
from app.middlewares.jwt_bearer import JWTBearer
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.schemas.usuarios import Usuario, UsuarioCreate, UsuarioLogin
from app.services.usuarios import UsuariosService
from app.services.auth import crear_token_jwt

usuarios_router = APIRouter()

@usuarios_router.post('/login', tags=['Usuarios'])
def login(usuario_login: UsuarioLogin, db: Session = Depends(get_db)):
    service = UsuariosService(db)
    usuario = UsuariosService(db).obtener_usuario_por_correo(usuario_login.correo)
    if not usuario or not service.verificar_password(usuario_login.contrasena.get_secret_value(), usuario.contrasena):
        raise HTTPException(status_code=400, detail="Correo o contraseña incorrectos")
    
    token = crear_token_jwt({"user_id": usuario.id, "correo": usuario.correo})
    return {"access_token": token, "token_type": "bearer"}

@usuarios_router.post('/usuarios', tags=['Usuarios'], response_model=dict, status_code=201)
def post_crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """Crear un nuevo usuario"""
    try:
        nuevo_usuario = UsuariosService(db).crear_usuario(usuario)
        return JSONResponse(status_code=201, content={"message": "Usuario creado correctamente", "usuario_id": nuevo_usuario.id})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@usuarios_router.get('/usuarios', tags=['Usuarios'], response_model=List[Usuario], dependencies=[Depends(JWTBearer())])
def get_todos_usuarios(db: Session = Depends(get_db)):
    """Obtener todos los usuarios"""
    result = UsuariosService(db).obtener_todos_usuarios()
    return JSONResponse(status_code=200, content=jsonable_encoder(result))

@usuarios_router.get('/usuarios/{usuario_id}', tags=['Usuarios'], response_model=Usuario, dependencies=[Depends(JWTBearer())])
def get_usuario_por_id(usuario_id: int, db: Session = Depends(get_db)):
    """Obtener un usuario específico por ID"""
    result = UsuariosService(db).obtener_usuario_por_id(usuario_id)
    if not result:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return JSONResponse(status_code=200, content=jsonable_encoder(result))

@usuarios_router.get('/usuarios/correo/{correo}', tags=['Usuarios'], response_model=Usuario, dependencies=[Depends(JWTBearer())])
def get_usuario_por_correo(correo: str, db: Session = Depends(get_db)):
    """Obtener un usuario por su correo electrónico"""
    result = UsuariosService(db).obtener_usuario_por_correo(correo)
    if not result:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return JSONResponse(status_code=200, content=jsonable_encoder(result))

@usuarios_router.put('/usuarios/{usuario_id}', tags=['Usuarios'], response_model=dict, dependencies=[Depends(JWTBearer())])
def put_actualizar_usuario(usuario_id: int, usuario_data: UsuarioCreate, db: Session = Depends(get_db)):
    """Actualizar información de un usuario"""
    try:
        UsuariosService(db).actualizar_usuario(usuario_id, usuario_data)
        return JSONResponse(status_code=200, content={"message": "Usuario actualizado correctamente"})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@usuarios_router.delete('/usuarios/{usuario_id}', tags=['Usuarios'], response_model=dict, dependencies=[Depends(JWTBearer())])
def delete_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Eliminar un usuario"""
    try:
        UsuariosService(db).eliminar_usuario(usuario_id)
        return JSONResponse(status_code=200, content={"message": "Usuario eliminado correctamente"})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@usuarios_router.get('/usuarios/{usuario_id}/existe', tags=['Usuarios'], response_model=dict, dependencies=[Depends(JWTBearer())])
def get_verificar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Verificar si un usuario existe"""
    existe = UsuariosService(db).verificar_usuario_existe(usuario_id)
    return JSONResponse(status_code=200, content={"existe": existe})

@usuarios_router.get('/usuarios/correo/{correo}/disponible', tags=['Usuarios'], response_model=dict, dependencies=[Depends(JWTBearer())])
def get_verificar_correo_disponible(correo: str, db: Session = Depends(get_db)):
    """Verificar si un correo electrónico está disponible"""
    disponible = UsuariosService(db).verificar_correo_disponible(correo)
    return JSONResponse(status_code=200, content={"disponible": disponible})