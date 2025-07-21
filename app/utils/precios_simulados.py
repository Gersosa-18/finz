# finz/utils/precios_simulados.py
PRECIOS_SIMULADOS = {
    # Alertas existentes que ya funcionan
    "NVDA": {"precio": 129.5, "volumen": 1200000},  # > 120 ✅
    "AAPL": {"precio": 189.75, "volumen": 980000},  # < 200 ✅  
    "TSLA": {"precio": 245.20, "volumen": 1400000}, # en rango 200-300 ✅
    
    # 🚀 CORREGIDOS PARA NUEVAS ALERTAS:
    "MSFT": {
        "precio": 420.0,           # Precio actual
        "precio_anterior": 400.0,  # Precio anterior (cambio = 5%)
        "volumen": 850000
    },
    "GOOGL": {
        "precio": 165.30,          # > 150 ✅
        "volumen": 1250000         # > 1,000,000 ✅
    },
    "AMZN": {"precio": 145.30, "volumen": 600000}
}

def obtener_dato_simulado(ticker: str, campo: str) -> float:
    return PRECIOS_SIMULADOS.get(ticker.upper(), {}).get(campo)