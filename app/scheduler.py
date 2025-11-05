from apscheduler.schedulers.background import BackgroundScheduler
from app.config.database import SessionLocal
from app.services.alertas import AlertasService
from app.models.usuarios import Usuarios
from app.models.notificaciones import Suscripcion
from pywebpush import webpush
import json
import os

def evaluar_todas_las_alertas():
    """Job que corre cada 5 min"""
    db = SessionLocal()
    
    try:
        usuarios = db.query(Usuarios).all()
        
        for usuario in usuarios:
            resultado = AlertasService(db).evaluar_alertas(usuario.id)
            
            if resultado["alertas_activadas"]:
                suscripcion = db.query(Suscripcion).filter(
                    Suscripcion.user_id == usuario.id
                ).first()
                
                if suscripcion:
                    try:
                        webpush(
                            subscription_info=suscripcion.subscription_data,
                            data=json.dumps({
                                "title": "🔔 Finz",
                                "body": f"{len(resultado['alertas_activadas'])} alerta(s)"
                            }),
                            vapid_private_key=os.getenv("VAPID_PRIVATE_KEY"),
                            vapid_claims={"sub": f"mailto:{os.getenv('VAPID_EMAIL')}"}
                        )
                    except:
                        pass
    finally:
        db.close()

# Inicializar scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(evaluar_todas_las_alertas, 'interval', minutes=5)