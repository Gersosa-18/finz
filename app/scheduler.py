from apscheduler.schedulers.background import BackgroundScheduler
from app.config.database import SessionLocal
from app.jobs.alertas_job import evaluar_alertas
from app.jobs.rsi_job import actualizar_rsi
def ejecutar_job_alertas():
    db = SessionLocal()
    try: 
        evaluar_alertas(db)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error en job de alertas: {e}")
    finally:
        db.close()

def ejecutar_job_rsi():
    db = SessionLocal()
    try:
        actualizar_rsi(db)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error en job RSI: {e}")
    finally:
        db.close()

# Configurar scheduler
scheduler = BackgroundScheduler(timezone='America/Argentina/Buenos_Aires')

# Alertas cada 5 min
scheduler.add_job(ejecutar_job_alertas, 'interval', minutes=5, id="job_alertas", replace_existing=True)
scheduler.add_job(ejecutar_job_rsi, "cron", minute="*", hour="11-17", day_of_week="mon-fri")