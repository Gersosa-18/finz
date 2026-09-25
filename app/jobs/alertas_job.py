from sqlalchemy.orm import Session
from app.services.alertas import AlertasService

def evaluar_alertas(db: Session):
    """
    Job que evalúa alertas activas en batch con mínima carga de base de datos.
    Recibe la DB desde el scheduler o desde un test.
    """
    service = AlertasService(db)
    return service.evaluar_alertas()
            