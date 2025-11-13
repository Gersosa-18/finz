from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
from app.config.database import SessionLocal
from app.services.alertas import AlertasService
from app.services.rsi_service import RSIService
from app.models.usuarios import Usuarios

def esta_en_horario_mercado() -> bool:
    """Verifica si estamos en horario de mercado USA (11:30 -> 18:00)"""
    tz_arg = pytz.timezone('America/Argentina/Buenos_Aires')
    ahora = datetime.now(tz_arg)
    print(f"⏰ Chequeo RSI - Hora actual: {ahora}")

    #  No opera sabados ni domingos
    if ahora.weekday() >= 5:
        return False
    
    # Horario de mercado 11:30 - 18:00
    hora_apertura = ahora.replace(hour=11, minute=30, second=0)
    hora_cierre = ahora.replace(hour=18, minute=0, second=0)
    
    return hora_apertura <= ahora <= hora_cierre

def actualizar_rsi_seguidos():
    print(f"✅ Ejecutando RSI a las {datetime.now().strftime('%H:%M:%S')}")
    if not esta_en_horario_mercado():
        print(f"Fuera de horario de mercado - RSI no actualizado")
        return

    db = SessionLocal()
    try:
        """Obtener tickers unicos que alguien sigue"""
        tickers_seguidos = RSIService.obtener_todos_los_tickers_seguidos(db)

        if not tickers_seguidos:
            print("No hay tickers seguidos por usuarios")
            return
        print(f"Actualizando RSI para {len(tickers_seguidos)}")

        exitosos = 0
        errores = 0

        for ticker in tickers_seguidos:
            try:
                result = RSIService.obtener_rsi_actual(ticker)

                RSIService.guardar_rsi(db, result["ticker"], result["rsi_value"])

                print(f"  ✅ {ticker}: RSI={result['rsi_value']} ({result['signal']})")
                exitosos += 1
             
            except Exception as e:
                print(f"  ❌ {ticker}: Error - {str(e)}")
                errores += 1
        
        print(f"Actualización comletada: {exitosos} OK, {errores} errores")
    except Exception as e:
        print(f" Error en actualizacion RSI {e}")
    finally:
        db.close()

def evaluar_todas_las_alertas():
    """Job que corre cada 5 min - Solo evalúa, AlertasService maneja las notificaciones"""
    db = SessionLocal()
    
    try:
        usuarios = db.query(Usuarios).all()
        
        for usuario in usuarios:
            # AlertasService.evaluar_alertas() ya maneja el envío de notificaciones
            AlertasService(db).evaluar_alertas(usuario.id)
            
    finally:
        db.close()

# Configurar scheduler
scheduler = BackgroundScheduler(timezone='America/Argentina/Buenos_Aires')

# Alertas cada 5 min
scheduler.add_job(evaluar_todas_las_alertas, 'interval', minutes=5)

# RSI cada 10 min
scheduler.add_job(
    actualizar_rsi_seguidos,
    CronTrigger(
        minute="*/10",
        hour="11-18",
        timezone="America/Argentina/Buenos_Aires"
    )
)