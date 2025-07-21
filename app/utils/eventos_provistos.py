# finz/app/utils/eventos_provistos.py
from datetime import date, timedelta
from app.enums.eventos_economicos import ImpactoEvento

def get_eventos_hoy():
    """Eventos de hoy - datos simulados MVP"""
    return [
        {
            "fecha": date.today(),
            "pais": "EE.UU.",
            "evento": "Índice de Precios al Consumidor (IPC)",
            "impacto": ImpactoEvento.ALTO,
            "activos_afectados": "SP500, NASDAQ, USD"
        }
    ]

def get_eventos_manana():
    """Eventos de mañana"""
    return [
        {
            "fecha": date.today() + timedelta(days=1),
            "pais": "EE.UU.",
            "evento": "Decisión de tasas Fed",
            "impacto": ImpactoEvento.ALTO,
            "activos_afectados": "SP500, NASDAQ, USD"
        }
    ]

def hay_eventos_alto_impacto():
    """Verifica si hay eventos de alto impacto hoy"""
    eventos = get_eventos_hoy()
    return any(e["impacto"] == ImpactoEvento.ALTO for e in eventos)