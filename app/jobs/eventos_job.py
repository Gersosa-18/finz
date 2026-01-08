from sqlalchemy.orm import Session
from app.services import eventos_service
def sincronizar_eventos(db: Session):
    """
    Job que sincroniza eventos
    Recibe la DB desde el scheduler
    """
    eventos_service.sincronizar_eventos(db)
