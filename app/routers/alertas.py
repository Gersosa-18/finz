# fintrack/app/routers/alertas.py
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.alertas import Alerta, AlertaCreate
from app.services.alertas import AlertasService

alertas_router = APIRouter()

@alertas_router.post('/alertas', tags=['Alertas'], response_model=dict, status_code=201)
def post_crear_alerta(alerta: AlertaCreate, db: Session = Depends(get_db)):
    """Crear una nueva alerta"""
    AlertasService(db).crear_alerta(alerta)
    return JSONResponse(status_code=201, content={"message": "Alerta creada correctamente"})

@alertas_router.get('/alertas/usuario/{user_id}', tags=['Alertas'], response_model=List[Alerta])
def get_alertas_usuario(user_id: int, db: Session = Depends(get_db)):
    """Obtener todas las alertas de un usuario"""
    result = AlertasService(db).obtener_alertas_usuario(user_id)
    return JSONResponse(status_code=200, content=jsonable_encoder(result))

@alertas_router.get('/activadas/{user_id}', tags=['Alertas'], response_model=dict)
def get_alertas_activadas(user_id: int, db: Session = Depends(get_db)):
    """Evaluar alertas activas de un usuario"""
    result = AlertasService(db).evaluar_alertas(user_id)
    return JSONResponse(status_code=200, content=result)

# Endpoints adicionales que podrías agregar:
@alertas_router.get('/alertas/{alerta_id}', tags=['Alertas'], response_model=Alerta)
def get_alerta_por_id(alerta_id: int, db: Session = Depends(get_db)):
    """Obtener una alerta específica por ID"""
    result = AlertasService(db).obtener_alerta_por_id(alerta_id)
    return JSONResponse(status_code=200, content=jsonable_encoder(result))

@alertas_router.put('/alertas/{alerta_id}/desactivar', tags=['Alertas'], response_model=dict)
def put_desactivar_alerta(alerta_id: int, db: Session = Depends(get_db)):
    """Desactivar una alerta específica"""
    AlertasService(db).desactivar_alerta(alerta_id)
    return JSONResponse(status_code=200, content={"message": "Alerta desactivada correctamente"})

@alertas_router.delete('/alertas/{alerta_id}', tags=['Alertas'], response_model=dict)
def delete_alerta(alerta_id: int, db: Session = Depends(get_db)):
    """Eliminar una alerta"""
    AlertasService(db).eliminar_alerta(alerta_id)
    return JSONResponse(status_code=200, content={"message": "Alerta eliminada correctamente"})