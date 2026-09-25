import logging
from typing import Dict, Any
from app.config.database import SessionLocal
from app.models.alertas import AlertaSimple, AlertaRango, AlertaPorcentaje, AlertaCompuesta
from app.services.precios_service import PreciosService

logger = logging.getLogger(__name__)

# Caché en memoria para acceso ultrarrápido desde endpoints REST y schedulers
_precios_cache: Dict[str, Dict[str, Any]] = {}

def actualizar_precios_cache():
    """
    Job programado para refrescar los precios de todos los tickers con alertas activas.
    Utiliza el pipeline resiliente de PreciosService sin sufrir fallos de Yahoo crumb.
    """
    db = SessionLocal()
    try:
        tickers = set()
        for model in [AlertaSimple, AlertaRango, AlertaPorcentaje, AlertaCompuesta]:
            for a in db.query(model).filter(model.activo == True).all():
                if a.ticker:
                    tickers.add(a.ticker.strip().upper())
        
        if not tickers:
            return

        for t in tickers:
            try:
                data = PreciosService.obtener_precio_completo(t)
                precio = data.get("price")
                if precio is not None:
                    _precios_cache[t] = {
                        "symbol": t,
                        "price": precio,
                        "change": data.get("change", 0.0),
                    }
                else:
                    # Si falla la llamada en vivo, preservar el valor anterior en caché si existía
                    if t not in _precios_cache or _precios_cache[t].get("price") is None:
                        logger.warning(f"No se pudo inicializar precio para '{t}' en caché")
            except Exception as e:
                logger.error(f"Error actualizando caché para '{t}': {e}")
    finally:
        db.close()

def get_cache() -> Dict[str, Dict[str, Any]]:
    """Retorna el diccionario de caché de precios en memoria"""
    return _precios_cache

def obtener_precio_ticker(ticker: str) -> Dict[str, Any]:
    """
    Obtiene el precio de un ticker específico desde caché o en caliente si no existe.
    Garantiza que el frontend nunca reciba price: null si el ticker es válido.
    """
    t_clean = ticker.strip().upper()
    cached = _precios_cache.get(t_clean)
    if cached and cached.get("price") is not None:
        return cached

    # Resolver en caliente y alimentar caché
    data = PreciosService.obtener_precio_completo(t_clean)
    precio = data.get("price")
    item = {
        "symbol": t_clean,
        "price": precio,
        "change": data.get("change", 0.0),
    }
    if precio is not None:
        _precios_cache[t_clean] = item
    return item
