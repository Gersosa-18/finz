# app/routers/rsi.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.rsi_service import RSIService
from app.schemas.rsi import ( RSIResponse, SeguimientoCreate, SeguimientoResponse, RSIConEstado)
from app.utils.auth import get_current_user_id

rsi_router = APIRouter(prefix="/rsi", tags=["RSI"])
# === ENDPOINTS DE SEGUIMIENTO ===
@rsi_router.post("/seguimientos", response_model=SeguimientoResponse, status_code=201)
def agregar_seguimiento(
    data: SeguimientoCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Agregar un ticker a mis seguimientos"""
    seguimiento = RSIService.agregar_seguimiento(db, user_id, data.ticker)
    return seguimiento

@rsi_router.delete("/seguimientos/{ticker}", status_code=204)
def eliminar_seguimiento(
    ticker: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Eliminar un ticker de mis seguimientos"""
    RSIService.eliminar_seguimiento(db, user_id, ticker)
    return None

@rsi_router.get("/seguimientos", response_model=list[SeguimientoResponse])
def listar_seguimientos(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Listar todos los tickers que sigo"""
    return RSIService.obtener_seguimientos(db, user_id)

@rsi_router.get("/mis-rsi")
def obtener_mis_rsi(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Obtener RSi de todos los tickers que sigo (desde BD)"""
    seguimientos = RSIService.obtener_seguimientos(db, user_id)

    resultados = []
    for seg in seguimientos:
        rsi_data = RSIService.obtener_rsi_con_estado(db, seg.ticker)
        resultados.append(rsi_data)
    
    return {
        "total": len(resultados),
        "tickers": resultados
    }

@rsi_router.get("/{ticker}", response_model=RSIConEstado)
def get_rsi(
    ticker: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Obtener RSI de un ticker especifico (desde BD)"""
    return RSIService.obtener_rsi_con_estado(db, ticker)

@rsi_router.post("/forzar-actualizacion")
def forzar_actualizacion(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Forzar actualización RSI (ignora horario)"""
    seguimientos = RSIService.obtener_seguimientos(db, user_id)

    for seg in seguimientos:
        try:
            result = RSIService.obtener_rsi_actual(seg.ticker)
            RSIService.guardar_rsi(db, result["ticker"], result["rsi_value"])
        except:
            pass
    
    return {"ok": True}