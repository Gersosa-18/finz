# app/routers/notificaciones.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.utils.auth import get_current_user_id
from app.schemas.notificaciones import SuscripcionPush
from app.models.notificaciones import Suscripcion
from pywebpush import webpush, WebPushException
import json 
import os

notificaciones_router = APIRouter(prefix="/notificaciones", tags=["notificaciones"])

@notificaciones_router.post("/suscribir")
def suscribir_push(
    data: SuscripcionPush,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    # Buscar si ya existe
    suscripcion = db.query(Suscripcion).filter(Suscripcion.user_id == user_id).first()
    
    if suscripcion:
        suscripcion.subscription_data = data.subscription
    else:
        suscripcion = Suscripcion(user_id=user_id, subscription_data=data.subscription)
        db.add(suscripcion)
    
    db.commit()
    return {"message": "Suscripción guardada"}

@notificaciones_router.post('/enviar/{user_id}')
def enviar_notificacion(
    user_id: int,
    titulo: str = "Finz Alert",
    mensaje: str = "Nueva alerta activada",
    db: Session = Depends(get_db)  # ← AGREGAR
):
    """Enviar push notification a un usuario"""
    suscripcion = db.query(Suscripcion).filter(Suscripcion.user_id == user_id).first()  # ← CAMBIAR
    
    if not suscripcion:  # ← CAMBIAR
        return {"error": "Usuario no suscrito"}
    
    try:
        webpush(
            subscription_info=suscripcion.subscription_data,  # ← CAMBIAR
            data=json.dumps({"title": titulo, "body": mensaje}),
            vapid_private_key=os.getenv("VAPID_PRIVATE_KEY"),
            vapid_claims={
                "sub": f"mailto:{os.getenv('VAPID_EMAIL', 'admin@finz.com')}"
            }
        )
        return {"message": "Notificación enviada"}
    except WebPushException as e:
        print(f"Error enviando push: {e}")
        return {"error": str(e)}