from sqlalchemy.orm import Session
from app.services.reportes_service import ReportesService
def sincronizar_reportes(db: Session):
    """
    Job que sincroniza reportes
    Recibe la DB desde el scheduler
    """
    service = ReportesService(db)
    service.generar_y_guardar_reporte()
    