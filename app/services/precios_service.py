# finz/app/services/precios_service.py
import logging
import time
from typing import Optional, Dict, Any, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import yfinance as yf
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Rotación de User-Agents realistas para evitar bloqueos y rate-limits
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

class PreciosService:
    """
    Servicio resiliente de cotizaciones con arquitectura multi-capa 
    (Chart API v8, fast_info, history y caché LKG) contra bloqueos de Yahoo Finance.
    """

    _session: Optional[requests.Session] = None
    _user_agent_index: int = 0
    _lkg_cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def _get_session(cls) -> requests.Session:
        if cls._session is None:
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=0.3,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET"],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            cls._session = session
        return cls._session

    @classmethod
    def _get_headers(cls) -> Dict[str, str]:
        ua = USER_AGENTS[cls._user_agent_index % len(USER_AGENTS)]
        cls._user_agent_index += 1
        return {
            "User-Agent": ua,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
            "Referer": "https://finance.yahoo.com/",
            "Origin": "https://finance.yahoo.com",
        }

    @classmethod
    def _fetch_direct_chart(cls, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Consulta la API de Chart v8 de Yahoo Finance.
        Esta API NO requiere cookies de consentimiento ni crumbs.
        """
        endpoints = [
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=2d",
            f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=2d",
        ]
        session = cls._get_session()

        for url in endpoints:
            try:
                resp = session.get(url, headers=cls._get_headers(), timeout=4.5)
                if resp.status_code == 200:
                    data = resp.json()
                    chart_result = data.get("chart", {}).get("result")
                    if chart_result and len(chart_result) > 0:
                        meta = chart_result[0].get("meta", {})
                        price = meta.get("regularMarketPrice")
                        if price is not None:
                            prev_close = (
                                meta.get("chartPreviousClose")
                                or meta.get("previousClose")
                                or price
                            )
                            change = 0.0
                            if prev_close and prev_close > 0:
                                change = round(((price - prev_close) / prev_close) * 100, 2)
                            volume = meta.get("regularMarketVolume")
                            return {
                                "symbol": ticker,
                                "price": round(float(price), 2),
                                "change": change,
                                "volume": int(volume) if volume is not None else None,
                                "open": meta.get("regularMarketOpen"),
                                "previous_close": round(float(prev_close), 2) if prev_close else None,
                                "source": "yahoo_chart_api",
                                "updated_at": time.time(),
                            }
                elif resp.status_code == 404:
                    # Ticker no existe o está deslistado
                    logger.warning(f"Ticker '{ticker}' no encontrado en Yahoo Chart API (404)")
                    return None
            except Exception as e:
                logger.debug(f"Error consultando endpoint {url} para {ticker}: {e}")
                continue
        return None

    @classmethod
    def _fetch_fast_info(cls, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Consulta yfinance utilizando fast_info, que no invoca el módulo quoteSummary susceptible a crumb 401.
        """
        try:
            t = yf.Ticker(ticker)
            fi = t.fast_info
            price = getattr(fi, "last_price", None)
            if price is None:
                price = getattr(fi, "lastPrice", None)
            if price is not None and price > 0:
                prev_close = getattr(fi, "previous_close", None) or getattr(fi, "regularMarketPreviousClose", None) or price
                change = 0.0
                if prev_close and prev_close > 0:
                    change = round(((price - prev_close) / prev_close) * 100, 2)
                vol = getattr(fi, "last_volume", None) or getattr(fi, "lastVolume", None)
                return {
                    "symbol": ticker,
                    "price": round(float(price), 2),
                    "change": change,
                    "volume": int(vol) if vol is not None else None,
                    "open": getattr(fi, "open", None),
                    "previous_close": round(float(prev_close), 2) if prev_close else None,
                    "source": "yfinance_fast_info",
                    "updated_at": time.time(),
                }
        except Exception as e:
            logger.debug(f"Error en fast_info para {ticker}: {e}")
        return None

    @classmethod
    def _fetch_history(cls, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Consulta yfinance history como último recurso online (usa endpoints de series temporales sin crumb).
        """
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d", interval="1d")
            if hist is not None and not hist.empty:
                last_row = hist.iloc[-1]
                price = float(last_row["Close"])
                prev_close = float(hist.iloc[-2]["Close"]) if len(hist) > 1 else price
                change = round(((price - prev_close) / prev_close) * 100, 2) if prev_close > 0 else 0.0
                vol = int(last_row["Volume"]) if "Volume" in last_row else None
                return {
                    "symbol": ticker,
                    "price": round(price, 2),
                    "change": change,
                    "volume": vol,
                    "open": float(last_row["Open"]) if "Open" in last_row else None,
                    "previous_close": round(prev_close, 2),
                    "source": "yfinance_history",
                    "updated_at": time.time(),
                }
        except Exception as e:
            logger.debug(f"Error en history para {ticker}: {e}")
        return None

    @classmethod
    def obtener_precio_completo(cls, ticker: str) -> Dict[str, Any]:
        """
        Obtiene el precio completo y métricas con fallback multi-capa y caché LKG.
        Garantiza que la API no devuelva null ni se caiga si Yahoo bloquea peticiones en Render.
        """
        if not ticker or not ticker.strip():
            raise HTTPException(status_code=400, detail="Ticker vacío")

        ticker_clean = ticker.strip().upper()

        # 1. Intentar API directa de Yahoo (sin crumb)
        datos = cls._fetch_direct_chart(ticker_clean)

        # 2. Intentar yfinance fast_info
        if not datos:
            datos = cls._fetch_fast_info(ticker_clean)

        # 3. Intentar yfinance history
        if not datos:
            datos = cls._fetch_history(ticker_clean)

        # 4. Si se obtuvo exitosamente en vivo, actualizar caché LKG
        if datos and datos.get("price") is not None:
            cls._lkg_cache[ticker_clean] = datos
            return datos

        # 5. Fallback a LKG (Last Known Good) Cache si Yahoo bloqueó o falló
        if ticker_clean in cls._lkg_cache:
            lkg = cls._lkg_cache[ticker_clean].copy()
            lkg["source"] = "lkg_cache"
            logger.warning(
                f"Yahoo bloqueado o sin respuesta para {ticker_clean}. "
                f"Retornando precio LKG en caché: ${lkg.get('price')}"
            )
            return lkg

        # 6. Fallback final seguro si nunca antes se consultó con éxito
        logger.error(f"No fue posible obtener cotización para {ticker_clean} (sin LKG disponible)")
        return {
            "symbol": ticker_clean,
            "price": None,
            "change": 0.0,
            "volume": None,
            "source": "unavailable",
            "updated_at": time.time(),
        }

    @classmethod
    def obtener_dato(cls, ticker: str, campo: Any) -> Optional[float]:
        """
        Método de compatibilidad para AlertasService y jobs.
        Retorna float para 'precio' o 'volumen'.
        """
        if not ticker or not ticker.strip():
            raise HTTPException(status_code=400, detail="Ticker vacío")

        campo_str = campo.value if hasattr(campo, "value") else str(campo).lower()
        info = cls.obtener_precio_completo(ticker)

        precio = info.get("price")
        volumen = info.get("volume")

        if campo_str == "precio":
            if precio is not None:
                return float(precio)
            raise HTTPException(
                status_code=404,
                detail=f"No se pudo obtener precio para ticker '{ticker}'. Servicio no disponible temporalmente.",
            )
        elif campo_str == "volumen":
            if volumen is not None:
                return float(volumen)
            raise HTTPException(
                status_code=404,
                detail=f"No se pudo obtener volumen para ticker '{ticker}'. Servicio no disponible temporalmente.",
            )
        else:
            raise HTTPException(status_code=400, detail=f"Campo '{campo}' inválido")

    @classmethod
    def get_lkg_cache(cls) -> Dict[str, Dict[str, Any]]:
        """Retorna el estado actual del caché Last Known Good"""
        return cls._lkg_cache

    @classmethod
    def set_lkg(cls, ticker: str, data: Dict[str, Any]):
        """Permite precargar o actualizar una entrada LKG"""
        cls._lkg_cache[ticker.strip().upper()] = data
