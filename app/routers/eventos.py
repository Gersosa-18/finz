# finz/app/routers/eventos.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.eventos import Evento
from app.middlewares.jwt_bearer import JWTBearer
from app.services.eventos_service import (
    sincronizar_earnings_finnhub,
    get_eventos_usuario,
)
from app.utils.auth import get_current_user_id
import os

eventos_router = APIRouter(prefix="/eventos", tags=["eventos"])


@eventos_router.get("/mis-eventos", dependencies=[Depends(JWTBearer())])
def mis_eventos(
    user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Eventos del usuario: macro (todos) + micro (sus tickers)"""
    return get_eventos_usuario(db, user_id)


@eventos_router.post("/sincronizar", dependencies=[Depends(JWTBearer())])
def sincronizar(db: Session = Depends(get_db)):
    """Sync: Solo Finnhub (micro) por ahora"""
    finnhub_key = os.getenv("FINNHUB_API_KEY")
    if not finnhub_key:
        raise HTTPException(400, "Falta API key: FINNHUB_API_KEY")

    micro = sincronizar_earnings_finnhub(db, finnhub_key)
    return {"eventos_micro": micro, "eventos_macro": "Deshabilitado"}


# @eventos_router.get("/debug")
# def debug_eventos(db: Session = Depends(get_db)):
#     from app.services.eventos_service import obtener_tickers_activos

#     tickers = obtener_tickers_activos(db)
#     eventos_existentes = db.query(Evento).count()

#     return {
#         "tickers_con_alertas": tickers,
#         "total_tickers": len(tickers),
#         "eventos_en_db": eventos_existentes,
#     }
