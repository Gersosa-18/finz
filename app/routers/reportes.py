from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.reportes_service import ReportesService
from app.schemas.reportes import ReporteResponse
from app.middlewares.jwt_bearer import JWTBearer
from typing import List

reportes_router = APIRouter(prefix="/reportes", tags=["Reportes"])

@reportes_router.post("/generar-semanal", response_model=ReporteResponse, status_code=201, dependencies=[Depends(JWTBearer())])
def generar_reporte_semanal(db: Session = Depends(get_db)):
    """Generar y guardar reporte semanal"""
    service = ReportesService(db)
    resultado = service.generar_y_guardar_reporte()
    return resultado

@reportes_router.get("/semanal-actual", response_model=List[ReporteResponse], dependencies=[Depends(JWTBearer())])
def obtener_reportes(db: Session = Depends(get_db)):
    """Obtener todos los reportes ordenados por fecha"""
    service = ReportesService(db)
    resultado = service.obtener_datos_todos_reportes()
    return resultado