# app/services/weekly_data_service.py

from datetime import datetime
import yfinance as yf

from typing import Dict, Optional

class WeeklyDataServices:

    INDICES = ["SPY", "QQQ", "DIA", "IWM"]
    SECTORES = ["XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLU", "XLRE", "XLB", "XLC"]

    @staticmethod
    def obtener_cambio_semanal(ticker: str) -> Optional[Dict]:
        """Calcula el % de cambio semanal (cierre a cierre)"""
        try:
            data = yf.Ticker(ticker).history(period='1mo', interval='1wk')

            if len(data) < 2:
                return None
        
            # Código
            cierre_semana_anterior = data.iloc[-2]['Close']
            cierre_semana_actual = data.iloc[-1]['Close']
            cambio_porcentual = ((cierre_semana_actual - cierre_semana_anterior) / cierre_semana_anterior) * 100

            return {"ticker": ticker,
                    "cambio_porcentual": round(float(cambio_porcentual), 2),
                    "precio_actual": round(float(cierre_semana_actual), 2),
                    "precio_apertura": round(float(cierre_semana_anterior), 2)
            }
        
        except Exception as e:
            return None
    
    @staticmethod
    def obtener_datos_semanales() -> Dict:
        """Obtiene datos semanales de todos los índices y sectores."""

        indices_data = []
        sectores_data = []

        for ticker in WeeklyDataServices.INDICES:
            resultado = WeeklyDataServices.obtener_cambio_semanal(ticker)
            if resultado:
                indices_data.append(resultado)
        
        for ticker in WeeklyDataServices.SECTORES:
            resultado = WeeklyDataServices.obtener_cambio_semanal(ticker)
            if resultado:
                sectores_data.append(resultado)
        return {"indices": indices_data,
                "sectores": sectores_data,
                "fecha_generacion": datetime.now().strftime("%Y-%m-%d")}
        