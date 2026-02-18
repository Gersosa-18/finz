import yfinance as yf
from app.config.database import SessionLocal
from app.models.alertas import AlertaSimple, AlertaRango, AlertaPorcentaje, AlertaCompuesta

_precios_cache: dict = {}

def actualizar_precios_cache():
    db = SessionLocal()
    try:
        tickers = set()
        for model in [AlertaSimple, AlertaRango, AlertaPorcentaje, AlertaCompuesta]:
            for a in db.query(model).filter(model.activo == True).all():
                tickers.add(a.ticker)
        
        if not tickers:
            return

        for t in tickers:
            try:
                info = yf.Ticker(t).info
                precio = info.get("currentPrice") or info.get("regularMarketPrice")
                if not precio:
                    continue
                apertura = info.get("regularMarketOpen", precio)
                _precios_cache[t] = {
                    "symbol": t,
                    "price": round(precio, 2),
                    "change": round(((precio - apertura) / apertura) * 100, 2)
                }
            except:
                pass
    finally:
        db.close()

def get_cache() -> dict:
    return _precios_cache
