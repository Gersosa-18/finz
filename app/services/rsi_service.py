import requests
import os
from datetime import datetime, timedelta, date
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.models.rsi import RSI, SeguimientoRSI # Asegurando imports
# Asumiendo que el archivo de modelos rsi.py ya tiene la clase SeguimientoRSI

class RSIService:
    
    # --- MÉTODOS DE OPTIMIZACIÓN DE RATE LIMIT ---
    
    @staticmethod
    def obtener_conteo_uso_hoy(db: Session) -> int:
        """Cuenta cuántas peticiones exitosas (guardadas en RSI history) hicimos hoy."""
        # Se asume que cada registro exitoso en RSI history es una petición a la API
        hoy = datetime.now().date()
        # Filtramos por la fecha de la columna timestamp
        return db.query(RSI).filter(func.date(RSI.timestamp) == hoy).count()

    @staticmethod
    def obtener_candidatos_actualizacion(db: Session, limite: int) -> list[str]:
        """
        Estrategia LRU (Least Recently Used):
        Devuelve los 'limite' tickers seguidos, ordenados por su última actualización 
        (los más viejos o los que nunca se han actualizado, primero).
        """
        # Consulta SQL optimizada:
        # 1. LEFT JOIN: Une los tickers seguidos (SeguimientoRSI) con la última fecha de RSI (MAX(timestamp)).
        # 2. ORDER BY ... ASC NULLS FIRST: Ordena de la fecha más antigua a la más reciente. Los tickers 
        #    que no tienen registro (NULL) van primero, asegurando que se actualicen inmediatamente.
        sql_query = text("""
            WITH ultima_actualizacion AS (
                SELECT ticker, MAX(timestamp) as last_update
                FROM rsi_history
                GROUP BY ticker
            )
            SELECT DISTINCT s.ticker
            FROM seguimiento_rsi s
            LEFT JOIN ultima_actualizacion r ON s.ticker = r.ticker
            ORDER BY r.last_update ASC NULLS FIRST, s.ticker
            LIMIT :limite
        """)
        
        # Ejecutar la consulta
        result = db.execute(sql_query, {"limite": limite}).fetchall()
        
        # Extraer el ticker del resultado (solo la primera columna [0])
        return [row[0] for row in result]

    # --- MÉTODOS EXISTENTES ---

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
                # TwelveData devuelve mensajes de error útiles en el JSON
                error_msg = response.json().get("message", f"Error TwelveData: {response.status_code}")
                raise HTTPException(503, error_msg)
            
            data = response.json()
            values = data.get("values")
            if not values:
                raise HTTPException(
                    503,
                    f"TwelveData no devolvío valores para {ticker}: {data}"
                )

            # Último valor RSI
            ultimo = values[0]
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
        if rsi_value >= 70:
            return "sobrecompra"
        elif rsi_value > 60:
            return "acercandose a sobrecompra"
        elif rsi_value <= 30:
            return "sobreventa"
        elif rsi_value < 40:
            return "acercandose a sobreventa"
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

        return db.query(SeguimientoRSI)\
        .filter(SeguimientoRSI.user_id == user_id)\
        .all()
    
    @staticmethod
    def obtener_rsi_con_estado(db: Session, ticker: str):
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
            es_dato_en_vivo = edad < timedelta(minutes=15)

            return {
                "ticker": ticker,
                "rsi_value": ultimo_registro.rsi_value,
                "timestamp": ultimo_registro.timestamp,
                "signal": RSIService._determinar_signal(ultimo_registro.rsi_value),
                "proxima_actualizacion": proxima_actualizacion,
                "tiene_datos": True,
                "es_dato_en_vivo": es_dato_en_vivo
            }
        else:
            return {
                "ticker": ticker,
                "rsi_value": None,
                "timestamp": None,
                "signal": None,
                "proxima_actualizacion": proxima_actualizacion,
                "tiene_datos": False,
                "es_dato_en_vivo": False
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
        if ahora >= hora_cierre:
            # Si ya es 18:00:00 o más tarde
            proxima = (ahora + timedelta(days=1)).replace(hour=11, minute=30)
            # Ajustar al próximo lunes si es viernes
            if ahora.weekday() == 4: # Viernes
                 proxima = (ahora + timedelta(days=3)).replace(hour=11, minute=30)
            return f"Mercado cerrado - próxima: {proxima.strftime('%d/%m %H:%M')}"
        
        # Durante horario de mercado, la próxima es en el próximo minuto.
        return f"Actualización continua (cada 1 min)"

    @staticmethod
    def obtener_todos_los_tickers_seguidos(db: Session):
        """Lista única de tickers que algún usuario sigue (Método obsoleto en el nuevo job inteligente)"""

        result = db.query(SeguimientoRSI.ticker)\
            .distinct()\
            .all()
        
        return [r[0] for r in result]