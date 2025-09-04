# app/enums/eventos_economicos.py
from enum import Enum

class TipoEvento(str, Enum):
    FOMC = "FOMC" # Decisión de la FED
    EARNINGS = "EARNINGS" # Resultados
    DIVIDEND = "DIVIDEND" # Pago de dividendos
    SPLIT = "SPLIT" # Split/reverse split
    OTRO = "OTRO" # Otro

class ImpactoEvento(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"