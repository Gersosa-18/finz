from sqlalchemy.orm import Session
from datetime import datetime
import pytz
import math
from app.services.rsi_service import RSIService

TZ_ARG = pytz.timezone("America/Argentina/Buenos_Aires")

def esta_en_horario_mercado(ahora: datetime) -> bool:
    """Verifica si estamos en horario de mercado USA (11:30 -> 18:00) en Buenos Aires."""
    
    # No opera sabados ni domingos
    if ahora.weekday() >= 5:
        return False
    
    # Horario de mercado 11:30 - 18:00
    hora_apertura = ahora.replace(hour=11, minute=30, second=0, microsecond=0)
    hora_cierre = ahora.replace(hour=18, minute=0, second=0, microsecond=0)
    
    # Usamos <= y < para evitar la ejecución justo al milisegundo de cierre (18:00:00)
    return hora_apertura <= ahora < hora_cierre

def actualizar_rsi(db: Session):
    ahora = datetime.now(TZ_ARG)

    if not esta_en_horario_mercado(ahora):
        return

    limite_diario = 795
    usados_hoy = RSIService.obtener_conteo_uso_hoy(db)

    if usados_hoy >= limite_diario:
        return

    remaining_requests = limite_diario - usados_hoy

    hora_cierre = ahora.replace(hour=18, minute=0, second=0, microsecond=0)
    minutos_restantes = (hora_cierre - ahora).total_seconds() / 60

    if minutos_restantes <= 0:
        return

    velocidad_optima = remaining_requests / minutos_restantes
    batch_size = min(math.ceil(velocidad_optima), 5)

    candidatos = RSIService.obtener_candidatos_actualizacion(db, batch_size)
    if not candidatos:
        return

    for ticker in candidatos:
        try:
            result = RSIService.obtener_rsi_actual(ticker)
            RSIService.guardar_rsi(db, result["ticker"], result["rsi_value"])
        except Exception as e:
            print(f"❌ Error {ticker}: {e}")