# finz/app/services/precios_service.py
import yfinance as yf
from typing import Optional
from fastapi import HTTPException

class PreciosService:
    
    @staticmethod
    def obtener_dato(ticker: str, campo: str) -> Optional[float]:
        """Obtiene precio o volumen real de Yahoo Finance"""
        # Validar entrada vacía
        if not ticker or not ticker.strip():
            raise HTTPException(status_code=400, detail="Ticker vacío")
        
        try:
            info = yf.Ticker(ticker.upper()).info
            # Verificaciones
            if not info or 'regularMarketPrice' not in info:
                raise HTTPException(status_code=404, detail=f"Ticker {ticker} no encontrado")
            
            if campo.lower() == "precio":
                return info.get("currentPrice") or info.get("regularMarketPrice")
            elif campo.lower() == "volumen":
                return info.get("regularMarketVolume") or info.get("volume")
            else:
                raise HTTPException(status_code=400, detail=f"Campo '{campo}' invalido")
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Error obteniendo datos: {str(e)}")
