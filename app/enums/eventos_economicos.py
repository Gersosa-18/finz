# app/enums/eventos_economicos.py
from enum import Enum

class ImpactoEvento(str, Enum):
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"