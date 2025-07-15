# finz/app/routers/alertas.py
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.alertas import Alerta, AlertaCreate
from app.services.alertas import AlertasService

from app.utils.analisis_sentimiento import analizar_sentimiento

alertas_router = APIRouter()

@alertas_router.post('/alertas', tags=['Alertas'], response_model=dict, status_code=201,
                     summary="Crear una alerta simple")
def post_crear_alerta(alerta: AlertaCreate, db: Session = Depends(get_db)):
    """Crear una nueva alerta"""
    AlertasService(db).crear_alerta(alerta)
    return JSONResponse(status_code=201, content={"message": "Alerta creada correctamente"})

@alertas_router.post('/alertas/avanzadas', tags=['Alertas'], response_model=dict, status_code=201,
                     summary="Crear una alerta avanzada",
                     description="Tipos: simple, rango, porcentaje, compuesta")
def post_crear_alerta_avanzada(alerta: AlertaCreate, db: Session = Depends(get_db)):
    """ Crear una alerta avanzada con validaciones específicas """
    if alerta.tipo_alerta == "simple":
        if alerta.valor is None or alerta.campo is None or alerta.tipo_condicion is None:
            return JSONResponse(
                status_code=400, 
                content={"message": "Para alertas simples, se requiere valor, campo y tipo de condición."}
            )
    elif alerta.tipo_alerta == "rango":
        if alerta.valor_minimo is None or alerta.valor_maximo is None:
            return JSONResponse(
                status_code=400,
                content={"message": "Para alertas de rango, se requiere valor mínimo y máximo."}
            )
        # ¿Qué validación adicional falta aquí?
        if alerta.valor_minimo >= alerta.valor_maximo:
            return JSONResponse(
                status_code=400,
                content={"message": "El valor mínimo debe ser menor que el máximo."}
            )
    elif alerta.tipo_alerta == "porcentaje":
        if alerta.porcentaje_cambio is None or alerta.valor is None:
            return JSONResponse(
                status_code=400,
                content={"message": "Para alertas de porcentaje, se requiere porcentaje de cambio y valor base."}
            )
        # Validación adicional del signo del porcentaje (opcional)
        if alerta.porcentaje_cambio > 0:
            return JSONResponse(
                status_code=400,
                content={"message": "Para alertas de caída, use porcentaje negativo (ej: -5). Para subida, use positivo."}
            )

    elif alerta.tipo_alerta == "compuesta":
        if not alerta.condiciones or len(alerta.condiciones) < 2:
            return JSONResponse(
                status_code=400, 
                content={"message": "Cada condición compuesta debe tener campo, valor y tipo de condición."}
            )
        # Validar cada condición
        for condicion in alerta.condiciones:
            if not all(k in condicion.model_dump() for k in ['campo', 'valor', 'tipo_condicion']):
                return JSONResponse(
                    status_code=400,
                    content={"message": "Cada condición compuesta debe tener ticker, campo, valor y tipo de condición."}
            )
    else:
        return JSONResponse(
            status_code=400, 
            content={"message": "Tipo de alerta no válido."}
        )
    result = AlertasService(db).crear_alerta(alerta)
    return JSONResponse(status_code=201, content={"message": "Alerta avanzada creada correctamente"})

@alertas_router.post('/alertas/evaluar-con-sentimiento', tags=['Testing'], response_model=dict)
def post_evaluar_con_sentimiento(
    user_id: int,
    noticias: List[str],
    db: Session = Depends(get_db)
):
    """Evaluar alertas con análisis de sentimiento"""
    result = AlertasService(db).evaluar_alertas(user_id, noticias)
    return JSONResponse(status_code=200, content=result)

@alertas_router.post('/test/sentiment', tags=['Testing'], response_model=dict)
def test_sentiment_analysis(noticias: List[str]):
    "Endpoint para testear solo análisis de sentimiento"

    resultados = []
    for noticia in noticias:
        sentimiento = analizar_sentimiento(noticia)
        resultados.append({
            "texto": noticia,
            "sentimiento": sentimiento
        })
    
    # Calcular sentimiento general
    sentimientos = [r["sentimiento"] for r in resultados]
    positivos = sentimientos.count("positivo")
    negativos = sentimientos.count("negativo")
    neutral = sentimientos.count("neutral")

    if positivos > negativos:
        general = "positivo"
    elif negativos > positivos:
        general = "negativo"
    else:
        general = "neutral"
    
    return {
        "analisis_individual": resultados,
        "sentimiento_general": general,
        "resumen": {
            "positivos": positivos,
            "negativos": negativos,
            "neutros": neutral,
            "total": len(noticias)
        }
    }

@alertas_router.get('/alertas/usuario/{user_id}', tags=['Alertas'], response_model=List[Alerta])
def get_alertas_usuario(user_id: int, db: Session = Depends(get_db)):
    """Obtener todas las alertas de un usuario"""
    result = AlertasService(db).obtener_alertas_usuario(user_id)
    return JSONResponse(status_code=200, content=jsonable_encoder(result))

@alertas_router.get('/activadas/{user_id}', tags=['Alertas'], response_model=dict)
def get_alertas_activadas(user_id: int, db: Session = Depends(get_db)):
    """Evaluar alertas activas de un usuario"""
    result = AlertasService(db).evaluar_alertas(user_id)
    return JSONResponse(status_code=200, content=result)

# Endpoints adicionales que podrías agregar:
@alertas_router.get('/alertas/{alerta_id}', tags=['Alertas'], response_model=Alerta)
def get_alerta_por_id(alerta_id: int, db: Session = Depends(get_db)):
    """Obtener una alerta específica por ID"""
    result = AlertasService(db).obtener_alerta_por_id(alerta_id)
    return JSONResponse(status_code=200, content=jsonable_encoder(result))

@alertas_router.put('/alertas/{alerta_id}/desactivar', tags=['Alertas'], response_model=dict)
def put_desactivar_alerta(alerta_id: int, db: Session = Depends(get_db)):
    """Desactivar una alerta específica"""
    AlertasService(db).desactivar_alerta(alerta_id)
    return JSONResponse(status_code=200, content={"message": "Alerta desactivada correctamente"})

@alertas_router.delete('/alertas/{alerta_id}', tags=['Alertas'], response_model=dict)
def delete_alerta(alerta_id: int, db: Session = Depends(get_db)):
    """Eliminar una alerta"""
    AlertasService(db).eliminar_alerta(alerta_id)
    return JSONResponse(status_code=200, content={"message": "Alerta eliminada correctamente"})