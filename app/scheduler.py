from apscheduler.schedulers.background import BackgroundScheduler
from app.config.database import SessionLocal
from app.services.alertas import AlertasService
from app.models.usuarios import Usuarios

def evaluar_todas_las_alertas():
    """Job que corre cada 5 min - Solo evalúa, AlertasService maneja las notificaciones"""
    db = SessionLocal()
    
    try:
        usuarios = db.query(Usuarios).all()
        
        for usuario in usuarios:
            # AlertasService.evaluar_alertas() ya maneja el envío de notificaciones
            AlertasService(db).evaluar_alertas(usuario.id)
            
    finally:
        db.close()

# Inicializar scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(evaluar_todas_las_alertas, 'interval', minutes=5)