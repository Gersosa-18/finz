# finz/app/routers/eventos_economicos.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.eventos_economicos import EventosEconomicosService
from app.schemas.eventos_economicos import EventoEconomicoCreate, EventoEconomico

eventos_router = APIRouter()

@eventos_router.get('/eventos/hoy', tags=['Eventos'])
def get_eventos_hoy(db: Session = Depends(get_db)):
    """Obtener eventos económicos de hoy"""
    service = EventosEconomicosService(db, usar_simulados=True)
    eventos = service.get_eventos_hoy()
    return {
        "fecha": "hoy",
        "eventos": eventos,
        "hay_alto_impacto": service.hay_eventos_alto_impacto_hoy(),
        "total": len(eventos)
    }

@eventos_router.get('/eventos/manana', tags=['Eventos'])
def get_eventos_manana_endpoint(db: Session = Depends(get_db)):
    """Obtener eventos económicos de mañana"""
    service = EventosEconomicosService(db, usar_simulados=True)
    eventos = service.get_eventos_manana()
    return {
        "fecha": "mañana",
        "eventos": eventos,
        "total": len(eventos)
    }


@eventos_router.get('/eventos/impacto-alto', tags=['Eventos'])
def get_hay_alto_impacto(db: Session = Depends(get_db)):
    """Verificar si hay eventos de alto impacto hoy"""
    service = EventosEconomicosService(db, usar_simulados=True)
    return {
        "hay_eventos_alto_impacto": service.hay_eventos_alto_impacto_hoy()
    }

# *************** POST para APIs/Scripts automáticos *************** 
@eventos_router.post('/eventos', tags=['Eventos'], response_model=EventoEconomico)
def crear_evento(
    evento: EventoEconomicoCreate,
    db: Session = Depends(get_db)
):
    """
    Crear evento económico - Solo para APIs/Scripts automáticos
    No para usuarios finales
    """
    try:
        service = EventosEconomicosService(db, usar_simulados=False)
        nuevo_evento = service.crear_evento(evento)
        return nuevo_evento
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creando evento: {str(e)}")