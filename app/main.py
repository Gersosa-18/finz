# finz/app/main.py
from fastapi import FastAPI
from app.config.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from app.routers.alertas import alertas_router
from app.routers.usuarios import usuarios_router
from app.routers.eventos_economicos import eventos_router
# from fastapi.staticfiles import StaticFiles
app = FastAPI()
app.title = "Finz API"
app.version = "1.0.0"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alertas_router)
app.include_router(usuarios_router)
app.include_router(eventos_router)
Base.metadata.create_all(bind=engine)