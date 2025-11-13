# finz/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers.alertas import alertas_router
from app.routers.usuarios import usuarios_router
from app.routers.eventos import eventos_router
from app.routers.notificaciones import notificaciones_router
from app.routers.rsi import rsi_router
from app.middlewares.error_handler import (
    http_exception_handler,
    general_exception_handler,
)
from app.scheduler import scheduler
import os

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
app = FastAPI()
app.title = "Finz API"
app.version = "1.0.0"

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Error handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(
    RequestValidationError,
    lambda req, exc: JSONResponse(
        status_code=422, content={"error": "Validación", "details": exc.errors()}
    ),
)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(alertas_router, prefix="/alertas")
app.include_router(usuarios_router)
app.include_router(eventos_router)
app.include_router(notificaciones_router)
app.include_router(rsi_router)
# Base.metadata.create_all(bind=engine)

# En main.py, agrega esto:

@app.on_event("startup")
async def startup_event():
    from app.config.database import engine, Base
    Base.metadata.create_all(bind=engine)
    scheduler.start()
    print("🚀 Scheduler de alertas iniciado")

@app.on_event("shutdown") 
async def shutdown_event():
    scheduler.shutdown()
    print("🛑 Scheduler detenido")

@app.get("/")
async def root():
    return {"message": "Finz API", "status": "ok"}