import math
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import pytz
from app.config.database import SessionLocal
from app.services.alertas import AlertasService
from app.services.rsi_service import RSIService
from app.models.usuarios import Usuarios

def esta_en_horario_mercado() -> bool:
    """Verifica si estamos en horario de mercado USA (11:30 -> 18:00) en Buenos Aires."""
    tz_arg = pytz.timezone('America/Argentina/Buenos_Aires')
    ahora = datetime.now(tz_arg)
    
    # No opera sabados ni domingos
    if ahora.weekday() >= 5:
        return False
    
    # Horario de mercado 11:30 - 18:00
    hora_apertura = ahora.replace(hour=11, minute=30, second=0, microsecond=0)
    hora_cierre = ahora.replace(hour=18, minute=0, second=0, microsecond=0)
    
    # Usamos <= y < para evitar la ejecución justo al milisegundo de cierre (18:00:00)
    return hora_apertura <= ahora < hora_cierre

def actualizar_rsi_inteligente():
    """
    Algoritmo de distribución de carga para RSI.
    Corre cada 1 minuto. Calcula dinámicamente cuántas peticiones gastar 
    para no exceder el límite diario de 800 requests.
    """
    tz_arg = pytz.timezone("America/Argentina/Buenos_Aires")
    ahora = datetime.now(tz_arg)
    
    print(f"⏰ Chequeo RSI inteligente - Hora actual: {ahora.strftime('%H:%M:%S')}")

    # 1. Chequeo Básico de Horario
    if not esta_en_horario_mercado():
        print("Fuera de horario de mercado - RSI no actualizado")
        return

    db = SessionLocal()
    try:
        # 2. Calcular Presupuesto Restante
        limite_diario = 795  # Dejamos 5 de margen de seguridad (Límite: 800)
        usados_hoy = RSIService.obtener_conteo_uso_hoy(db)

        if usados_hoy >= limite_diario:
            print("⚠️ Límite diario de requests alcanzado. Pausando hasta mañana.")
            return
        
        remaining_requests = limite_diario - usados_hoy
        
        # Calcular minutos restantes hasta el cierre (18:00)
        hora_cierre = ahora.replace(hour=18, minute=0, second=0, microsecond=0)
        minutos_restantes = (hora_cierre - ahora).total_seconds() / 60

        if minutos_restantes <= 0:
            print("Mercado acaba de cerrar.")
            return
        
        # 3. Calcular Velocidad de Crucero (Requests por minuto permitidos)
        velocidad_optima = remaining_requests / minutos_restantes
        
        # Redondeamos hacia arriba para no desperdiciar el presupuesto
        batch_size = math.ceil(velocidad_optima)
        # Límite de seguridad: Nunca exceder 5 req/min (para respetar el límite de 8/min de la API)
        batch_size = min(batch_size, 5) 

        print(f"📊 Estado: Usados {usados_hoy}/800 | Restan {int(minutos_restantes)} min | Batch óptimo: {batch_size} req/min")

        # 4. Obtener los tickers que llevan más tiempo esperando (LRU)
        candidatos = RSIService.obtener_candidatos_actualizacion(db, batch_size)
        
        if not candidatos:
            print("💤 No hay tickers seguidos para actualizar.")
            return
        
        print(f"🔄 Actualizando {len(candidatos)} tickers más 'hambrientos'.")

        # 5. Ejecutar Actualizaciones
        exitosos = 0
        errores = 0
        for ticker in candidatos:
            try:
                result = RSIService.obtener_rsi_actual(ticker)
                RSIService.guardar_rsi(db, result["ticker"], result["rsi_value"])
                print(f"   ✅ {ticker}: RSI={result['rsi_value']} ({result['signal']})")
                exitosos += 1
            except Exception as e:
                print(f"   ❌ Error {ticker}: {str(e)}")
                errores += 1
                
        print(f"Actualización completada: {exitosos} OK, {errores} errores.")

    except Exception as e:
        print(f" Error general en actualizacion RSI: {e}")

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

# RSI Inteligente: Ejecutar CADA MINUTO durante el horario de mercado
scheduler.add_job(
    actualizar_rsi_inteligente,
    CronTrigger(
        minute="*",      
        hour="11-17",     
        day_of_week="mon-fri", 
        timezone="America/Argentina/Buenos_Aires"
    )
)
