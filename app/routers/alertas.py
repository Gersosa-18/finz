# finz/app/routers/alertas.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from typing import List
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.alertas import (
    AlertaSimple, AlertaSimpleCreate,
    AlertaRango, AlertaRangoCreate,
    AlertaPorcentaje, AlertaPorcentajeCreate,
    AlertaCompuesta, AlertaCompuestaCreate
)
from app.services.alertas import AlertasService
from app.utils.auth import get_current_user_id
from app.middlewares.jwt_bearer import JWTBearer

alertas_router = APIRouter()
_cache_precios: dict = {}

# Endpoints de creación por tipo
@alertas_router.post('/simple', tags=['Alertas'], response_model=dict, status_code=201,
                     summary="Crear alerta simple")
def post_crear_alerta_simple(alerta: AlertaSimpleCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Crear alerta simple: precio > X, volumen < Y"""
    AlertasService(db).crear_alerta_simple(alerta, user_id)
    return {"message": "Alerta simple creada correctamente"}

@alertas_router.post('/rango', tags=['Alertas'], response_model=dict, status_code=201,
                     summary="Crear alerta de rango")
def post_crear_alerta_rango(alerta: AlertaRangoCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Crear alerta de rango: precio entre X e Y"""
    AlertasService(db).crear_alerta_rango(alerta, user_id)
    return {"message": "Alerta de rango creada correctamente"}

@alertas_router.post('/porcentaje', tags=['Alertas'], response_model=dict, status_code=201,
                     summary="Crear alerta de porcentaje")
def post_crear_alerta_porcentaje(alerta: AlertaPorcentajeCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Crear alerta de porcentaje: cambió +5% o -10%"""
    AlertasService(db).crear_alerta_porcentaje(alerta, user_id)
    return {"message": "Alerta de porcentaje creada correctamente"}

@alertas_router.post('/compuesta', tags=['Alertas'], response_model=dict, status_code=201,
                     summary="Crear alerta compuesta")
def post_crear_alerta_compuesta(alerta: AlertaCompuestaCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Crear alerta compuesta: múltiples condiciones con AND/OR"""
    AlertasService(db).crear_alerta_compuesta(alerta, user_id)
    return {"message": "Alerta compuesta creada correctamente"}

# Endpoints de consultas
@alertas_router.get('/tickers-seguimiento', tags=['Alertas'])
def get_tickers_seguimiento(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Tickers del usuario con precios"""
    import yfinance as yf

    alertas = AlertasService(db).obtener_alertas_usuario(user_id)
    tickers = list({a.ticker for alertas_tipo in alertas.values() for a in alertas_tipo if a.activo})

    if not tickers:
        return {"tickers": []}
    
    try:
        data = yf.download(tickers, period="1d", auto_adjust=True, progress=False)
        resultado = []
        for t in tickers:
            try:
                precio = float(data["Close"][t].dropna().iloc[-1])
                apertura = float(data["Open"][t].dropna().iloc[-1])
                cambio = round(((precio - apertura) / apertura) * 100, 2)
                entry = {"symbol": t, "price": round(precio, 2), "change": round(cambio, 2)}
                _cache_precios[t] = entry  # guardar éxito
                resultado.append(entry)
            except Exception:
                resultado.append(_cache_precios.get(t, {"symbol": t, "price": None, "change": 0}))

    except Exception:
        # yfinance falló del todo → usar caché
        resultado = [_cache_precios.get(t, {"symbol": t, "price": None, "change": 0}) for t in tickers]
            
    return {"tickers": resultado}

@alertas_router.get('/mis-alertas', tags=['Alertas'])
def get_mis_alertas(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Obtener las alertas del usuario autenticado"""
    result = AlertasService(db).obtener_alertas_usuario(user_id)
    return jsonable_encoder(result)

@alertas_router.get('/activadas', tags=['Alertas'])
def get_alertas_activadas(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Evaluar alertas activas del usuario autenticado"""
    result = AlertasService(db).evaluar_alertas(user_id)
    return result

@alertas_router.get('/{alerta_id}', tags=['Alertas'])
def get_alerta_por_id(alerta_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Obtener una alerta específica por ID (solo si pertenece al usuario)"""
    result = AlertasService(db).obtener_alerta_por_id(alerta_id)

    # Verificar que la alerta pertenece al usuario autenticado
    if not result or result.user_id != user_id:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return jsonable_encoder(result)

# Endpoints de gestión
@alertas_router.put('/{alerta_id}/desactivar', tags=['Alertas'])
def put_desactivar_alerta(alerta_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Desactivar una alerta específica (solo si pertenece al usuario)"""
    alerta = AlertasService(db).obtener_alerta_por_id(alerta_id)
    if not alerta or alerta.user_id != user_id:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    result = AlertasService(db).desactivar_alerta(alerta_id)
    if result:
        return {"message": "Alerta desactivada correctamente"}
    return {"message": "Alerta no encontrada"}

@alertas_router.delete('/{alerta_id}', tags=['Alertas'])
def delete_alerta(alerta_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Eliminar una alerta (solo si pertenece al usuario)"""
    alerta = AlertasService(db).obtener_alerta_por_id(alerta_id)
    if not alerta or alerta.user_id != user_id:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    success = AlertasService(db).eliminar_alerta(alerta_id)
    if success:
        return {"message": "Alerta eliminada correctamente"}
    return {"message": "Alerta no encontrada"}
