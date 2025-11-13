import requests
import os
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.rsi import RSI

class RSIService:

    @staticmethod
    def obtener_rsi_actual(ticker: str) -> dict:
        """Obtiene RSI desde Twelve Data"""
        api_key = os.getenv('TWELVEDATA_API_KEY')
        if not api_key:
            raise HTTPException(400, "TWELVEDATA_API_KEY no configurada")
        
        url = "https://api.twelvedata.com/rsi"
        params = {
            "symbol": ticker.upper(),
            "interval": "1day",
            "time_period": 14,
            "apikey": api_key
        }

        try:
            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                raise HTTPException(503, f"Error TwelveData: {response.status_code}")
            
            data = response.json()

            # Último valor RSI
            ultimo = data["values"][0]
            rsi_value = float(ultimo["rsi"])

            return {
                "ticker": ticker.upper(),
                "rsi_value": round(rsi_value, 2),
                "timestamp": ultimo["datetime"],
                "signal": RSIService._determinar_signal(rsi_value)
            }
        
        except requests.exceptions.RequestException as e:
            raise HTTPException(503, f"Error conectando con Twelve Data: {str(e)}")
    
    @staticmethod
    def _determinar_signal(rsi_value: float) -> str:
        """Determina la señal del rsi"""
        if rsi_value > 70:
            return "sobrecompra"
        elif rsi_value > 60:
            return "acercandose a sobrecompra"
        elif rsi_value < 40:
            return "acercandose a sobreventa"
        elif rsi_value < 30:
            return "sobreventa"
        else:
            return "neutral"

    @staticmethod
    def guardar_rsi(db: Session, ticker: str, rsi_value: float):
        """Guarda RSI en BD (opcional)"""
        rsi_record = RSI(ticker=ticker, rsi_value=rsi_value)
        db.add(rsi_record)
        db.commit()
        return rsi_record
    
    @staticmethod
    def agregar_seguimiento(db: Session, user_id: int, ticker: str):
        """Agregar ticker a seguimiento del usuario"""
        from app.models.rsi import SeguimientoRSI
        
        ticker = ticker.upper()

        # Verificar si ya existe
        existe = db.query(SeguimientoRSI)\
        .filter(SeguimientoRSI.user_id == user_id)\
        .filter(SeguimientoRSI.ticker == ticker)\
        .first()

        if existe:
            raise HTTPException(400, f"Ya estás siguiendo {ticker}")
        
        seguimiento = SeguimientoRSI(user_id=user_id, ticker=ticker)
        db.add(seguimiento)
        db.commit()
        db.refresh(seguimiento)
        return seguimiento
    
    @staticmethod
    def eliminar_seguimiento(db: Session, user_id: int, ticker: str):
        """Eliminar ticker de seguimientos"""
        from app.models.rsi import SeguimientoRSI

        ticker = ticker.upper()

        seguimiento = db.query(SeguimientoRSI)\
        .filter(SeguimientoRSI.user_id == user_id)\
            .filter(SeguimientoRSI.ticker == ticker)\
            .first()
        
        if not seguimiento:
            raise HTTPException(404, f"No estás siguiendo {ticker}")
        
        db.delete(seguimiento)
        db.commit()
        return True
    
    @staticmethod
    def obtener_seguimientos(db: Session, user_id: int):
        """Obtener todos los tickers de el usuario"""
        from app.models.rsi import SeguimientoRSI

        return db.query(SeguimientoRSI)\
        .filter(SeguimientoRSI.user_id == user_id)\
        .all()
    
    @staticmethod
    def obtener_rsi_con_estado(db: Session, ticker: str, max_age_minutes: int = 10):
        """Obtiene RSI desde BD con información de próxima actualización"""
        ticker = ticker.upper()

        # Buscar ultimo RSI
        ultimo_registro = db.query(RSI)\
        .filter(RSI.ticker == ticker)\
        .order_by(RSI.timestamp.desc())\
        .first()

        # Calcular proxima act
        proxima_actualizacion = RSIService._calcular_proxima_actualizacion()

        if ultimo_registro:
            edad = datetime.now() - ultimo_registro.timestamp
            tiene_datos_frescos = edad < timedelta(minutes=max_age_minutes)

            return {
                "ticker": ticker,
                "rsi_value": ultimo_registro.rsi_value if tiene_datos_frescos else None,
                "timestamp": ultimo_registro.timestamp if tiene_datos_frescos else None,
                "signal": RSIService._determinar_signal(ultimo_registro.rsi_value) if tiene_datos_frescos else None,
                "proxima_actualizacion": proxima_actualizacion,
                "tiene_datos": tiene_datos_frescos
            }
        else:
            return {
                "ticker": ticker,
                "rsi_value": None,
                "timestamp": None,
                "signal": None,
                "proxima_actualizacion": proxima_actualizacion,
                "tiene_datos": False
            }
        
    @staticmethod
    def _calcular_proxima_actualizacion():
        """Calcular cuando sera la proxima act"""
        import pytz

        tz_arg = pytz.timezone('America/Argentina/Buenos_Aires')
        ahora = datetime.now(tz_arg)

        # Horario mercado: 11:30 - 18:00
        hora_apertura = ahora.replace(hour=11, minute=30, second=0, microsecond=0)
        hora_cierre = ahora.replace(hour=18, minute=0, second=0, microsecond=0)

        # Fin de semana
        if ahora.weekday() >= 5:
            dias_hasta_lunes = 7 - ahora.weekday()
            proxima = (ahora + timedelta(days=dias_hasta_lunes)).replace(hour=11, minute=30)
            return f"Mercado cerrado - próxima: {proxima.strftime('%d/%m %H:%M')}"
        
        # Antes de apertura
        if ahora < hora_apertura:
            return f"Mercado cerrado - abre a las {hora_apertura.strftime('%H:%M')}"
        
        # Después de apertura
        if ahora > hora_cierre:
            proxima = (ahora + timedelta(days=1)).replace(hour=11, minute=30)
            return f"Mercado cerrado - próxima: {proxima.strftime('%d/%m %H:%M')}"
        
        minutos_hasta_proxima = 10 - (ahora.minute % 10)
        proxima = ahora + timedelta(minutes=minutos_hasta_proxima)
        return f"{proxima.strftime('%H:%M')} (en {minutos_hasta_proxima} min)"
    
    @staticmethod
    def obtener_todos_los_tickers_seguidos(db: Session):
        """Lista única de tickers que algún usuario sigue"""
        from app.models.rsi import SeguimientoRSI

        result = db.query(SeguimientoRSI.ticker)\
            .distinct()\
            .all()
        
        return [r[0] for r in result]