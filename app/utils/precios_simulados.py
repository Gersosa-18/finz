# fintrack/utils/precios_simulados.py
PRECIOS_SIMULADOS = {
    "NVDA": {"precio": 129.5, "volumen": 1200000},
    "AAPL": {"precio": 189.75, "volumen": 980000},
    "TSLA": {"precio": 245.20, "volumen": 1400000},
    "MSFT": {"precio": 378.20, "volumen": 850000},
    "GOOGL": {"precio": 142.80, "volumen": 750000},
    "AMZN": {"precio": 145.30, "volumen": 600000}
}

def obtener_dato_simulado(ticker: str, campo: str) -> float:
    return PRECIOS_SIMULADOS.get(ticker.upper(), {}).get(campo)