# finz/app/services/eventos_service.py
from sqlalchemy.orm import Session
from app.models.eventos import Evento
from app.models.alertas import (
    AlertaSimple,
    AlertaRango,
    AlertaPorcentaje,
    AlertaCompuesta,
)
from app.enums.eventos import ImpactoEvento, TipoEvento
from datetime import date, datetime, timedelta
import requests


def obtener_tickers_activos(db: Session):
    """Tickers con alertas activas"""
    tickers = set()
    for modelo in [AlertaSimple, AlertaRango, AlertaPorcentaje, AlertaCompuesta]:
        for alerta in db.query(modelo).filter(modelo.activo == True).all():
            tickers.add(alerta.ticker)
    return list(tickers)


# def sincronizar_eventos_fmp(db: Session, fmp_key: str):
#     """Eventos MACRO desde FMP Economics Calendar"""
#     url = "https://financialmodelingprep.com/api/v3/economic_calendar"
#     params = {
#         "apikey": fmp_key,
#         "from": date.today().isoformat(),
#         "to": (date.today() + timedelta(days=30)).isoformat(),
#     }

#     response = requests.get(url, params=params)
#     # LOGS PARA DEBUG:
#     print(f"Response status: {response.status_code}")
#     print(f"Response content: {response.json()}")

#     if response.status_code != 200:
#         return 0

#     eventos_raw = response.json()
#     eventos_filtrados = [
#         e for e in eventos_raw if e.get("country") == "US" and e.get("impact") == "High"
#     ]
#     print(f"Total eventos: {len(eventos_raw)}")
#     print(f"Eventos US High impact: {len(eventos_filtrados)}")

#     eventos_creados = 0
#     for (
#         evento
#     ) in eventos_filtrados:  # YA ESTÁN FILTRADOS, no hace falta volver a filtrar
#         try:
#             fecha = datetime.strptime(evento["date"], "%Y-%m-%d %H:%M:%S")
#             descripcion = evento["event"][:200]

#             # No duplicar
#             if (
#                 db.query(Evento)
#                 .filter(Evento.fecha == fecha, Evento.descripcion == descripcion)
#                 .first()
#             ):
#                 continue

#             db.add(
#                 Evento(
#                     fecha=fecha,
#                     ticker=None,  # Macro = sin ticker
#                     tipo=(
#                         TipoEvento.FOMC
#                         if "fed" in descripcion.lower()
#                         else TipoEvento.OTRO
#                     ),
#                     descripcion=descripcion,
#                     impacto=ImpactoEvento.HIGH,
#                 )
#             )
#             eventos_creados += 1

#         except Exception as e:
#             print(f"Error procesando evento: {evento}, Error: {e}")
#             continue

#     db.commit()
#     return eventos_creados


def sincronizar_earnings_finnhub(db: Session, finnhub_key: str):
    """Eventos MICRO desde Finnhub (solo tickers con alertas)"""
    tickers = obtener_tickers_activos(db)
    if not tickers:
        return 0

    eventos_creados = 0
    url = "https://finnhub.io/api/v1/calendar/earnings"

    for ticker in tickers:
        params = {
            "token": finnhub_key,
            "symbol": ticker,
            "from": date.today().isoformat(),
            "to": (date.today() + timedelta(days=60)).isoformat(),
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            continue

        for earning in response.json().get("earningsCalendar", []):
            fecha = datetime.strptime(earning["date"], "%Y-%m-%d")

            # No duplicar
            if (
                db.query(Evento)
                .filter(
                    Evento.fecha == fecha,
                    Evento.ticker == ticker,
                    Evento.tipo == TipoEvento.EARNINGS,
                )
                .first()
            ):
                continue

            db.add(
                Evento(
                    fecha=fecha,
                    ticker=ticker,  # Micro con ticker específico
                    tipo=TipoEvento.EARNINGS,
                    descripcion=f"{ticker} Earnings Report",
                    impacto=ImpactoEvento.HIGH,
                )
            )
            eventos_creados += 1

    db.commit()
    return eventos_creados


def get_eventos_usuario(db: Session, user_id: int):
    """Eventos del usuario: MACRO (todos) + MICRO (sus tickers)"""
    from app.services.alertas import AlertasService

    # Usar servicio existente
    alertas_service = AlertasService(db)
    alertas_usuario = alertas_service.obtener_alertas_usuario(user_id)

    # Extraer ticker activos del usuario
    tickers_usuario = set()
    for tipo_alertas in alertas_usuario.values():
        for alerta in tipo_alertas:
            if alerta.activo:
                tickers_usuario.add(alerta.ticker)

    # Próximos 7 días
    fecha_limite = date.today() + timedelta(days=7)

    # MACRO (ticker=None) + MICRO (sus tickers)
    eventos = (
        db.query(Evento)
        .filter(Evento.fecha <= fecha_limite, Evento.fecha >= date.today())
        .filter(
            (Evento.ticker.is_(None))  # Eventos macro
            | (
                Evento.ticker.in_(tickers_usuario) if tickers_usuario else False
            )  # Sus micro
        )
        .all()
    )

    macro = [e for e in eventos if e.ticker is None]
    micro = [e for e in eventos if e.ticker is not None]

    return {
        "macro": [
            {"descripcion": e.descripcion, "fecha": e.fecha.strftime("%Y-%m-%d")}
            for e in macro
        ],
        "micro": [
            {
                "ticker": e.ticker,
                "descripcion": e.descripcion,
                "fecha": e.fecha.strftime("%Y-%m-%d"),
            }
            for e in micro
        ],
        "tus_tickers": list(tickers_usuario),
    }
