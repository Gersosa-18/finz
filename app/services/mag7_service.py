import yfinance as yf
from datetime import date

TICKERS = ["NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA"]
BENCHMARK = "SPY"
_cache: dict = {}

def _calcular_ytd(ticker: str) -> dict | None:
    try:
        data = yf.Ticker(ticker).history(start=f"{date.today().year}-01-01")
        if len(data) < 2:
            return None
        first = float(data.iloc[0]["Close"])
        last = float(data.iloc[-1]["Close"])
        return {
            "ticker": ticker,
            "ytd": round(((last - first) / first) * 100, 2),
            "price": round(last, 2),
        }
    except:
        return None

def actualizar_cache():
    resultados = [r for t in TICKERS + [BENCHMARK] if (r := _calcular_ytd(t))]
    mag7 = [r for r in resultados if r["ticker"] != BENCHMARK]
    if mag7:
        resultados.append({
            "ticker": "MAG7~",
            "ytd": round(sum(r["ytd"] for r in mag7) / len(mag7), 2),
            "price": None,
        })
    spy_row = [r for r in resultados if r["ticker"] == BENCHMARK]
    rest = sorted([r for r in resultados if r["ticker"] != BENCHMARK], key=lambda x: x["ytd"], reverse=True)
    _cache["data"] = spy_row + rest
    _cache["year"] = date.today().year

def get_cache() -> dict:
    return _cache