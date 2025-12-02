from sqlalchemy.orm import Session
from app.models.reportes import Reporte
from app.services.groq_service import GroqService
from app.services.weekly_data_service import WeeklyDataServices

class ReportesService:
    def __init__(self, db: Session):
        self.db = db
        self.groq = GroqService()

    def generar_y_guardar_reporte(self):
        """Generar reporte con Groq y guardar en BD"""
        datos = WeeklyDataServices.obtener_datos_semanales()
        resumen = self.groq.generar_resumen_semanal(datos)
        nuevo_reporte = Reporte(
            fecha_inicio=datos['fecha_inicio'],
            fecha_fin=datos['fecha_fin'],
            resumen_groq=resumen,
            indices_json=datos['indices'],
            sectores_json=datos['sectores']
        )
        self.db.add(nuevo_reporte)
        self.db.commit()
        self.db.refresh(nuevo_reporte)
        return nuevo_reporte
    
    def obtener_datos_todos_reportes(self):
        """Obtener todos los reportes ordenados por fecha (más recien)"""
        reportes = self.db.query(Reporte).order_by(Reporte.created_at.desc()).all()
        return reportes