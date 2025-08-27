# finz/app/routers/alertas.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from typing import List
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.alertas import (
    AlertaSimple, AlertaSimpleCreate,
    AlertaRango, AlertaRangoCreate,
    AlertaPorcentaje, AlertaPorcentajeCreate,
    AlertaCompuesta, AlertaCompuestaCreate
)
from app.services.alertas import AlertasService
from app.utils.auth import get_current_user_id
from app.utils.analisis_sentimiento import analizar_sentimiento

alertas_router = APIRouter()

# Endpoints de creación por tipo
@alertas_router.post('/alertas/simple', tags=['Alertas'], response_model=dict, status_code=201,
                     summary="Crear alerta simple")
def post_crear_alerta_simple(alerta: AlertaSimpleCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Crear alerta simple: precio > X, volumen < Y"""
    AlertasService(db).crear_alerta_simple(alerta, user_id)
    return {"message": "Alerta simple creada correctamente"}

@alertas_router.post('/alertas/rango', tags=['Alertas'], response_model=dict, status_code=201,
                     summary="Crear alerta de rango")
def post_crear_alerta_rango(alerta: AlertaRangoCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Crear alerta de rango: precio entre X e Y"""
    AlertasService(db).crear_alerta_rango(alerta, user_id)
    return {"message": "Alerta de rango creada correctamente"}

@alertas_router.post('/alertas/porcentaje', tags=['Alertas'], response_model=dict, status_code=201,
                     summary="Crear alerta de porcentaje")
def post_crear_alerta_porcentaje(alerta: AlertaPorcentajeCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Crear alerta de porcentaje: cambió +5% o -10%"""
    AlertasService(db).crear_alerta_porcentaje(alerta, user_id)
    return {"message": "Alerta de porcentaje creada correctamente"}

@alertas_router.post('/alertas/compuesta', tags=['Alertas'], response_model=dict, status_code=201,
                     summary="Crear alerta compuesta")
def post_crear_alerta_compuesta(alerta: AlertaCompuestaCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Crear alerta compuesta: múltiples condiciones con AND/OR"""
    AlertasService(db).crear_alerta_compuesta(alerta, user_id)
    return {"message": "Alerta compuesta creada correctamente"}

# Endpoints de consultas
@alertas_router.get('/alertas/mis-alertas', tags=['Alertas'])
def get_mis_alertas(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Obtener las alertas del usuario autenticado"""
    result = AlertasService(db).obtener_alertas_usuario(user_id)
    return jsonable_encoder(result)

@alertas_router.get('/alertas/{alerta_id}', tags=['Alertas'])
def get_alerta_por_id(alerta_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Obtener una alerta específica por ID (solo si pertenece al usuario)"""
    result = AlertasService(db).obtener_alerta_por_id(alerta_id)

    # Verificar que la alerta pertenece al usuario autenticado
    if not result or result.user_id != user_id:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return jsonable_encoder(result)

# Endpoints de evaluación
@alertas_router.get('/alertas/activadas', tags=['Alertas'])
def get_alertas_activadas(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Evaluar alertas activas del usuario autenticado"""
    result = AlertasService(db).evaluar_alertas(user_id)
    return result

@alertas_router.post('/alertas/evaluar-con-sentimiento', tags=['Testing'])
def post_evaluar_con_sentimiento(
    noticias: List[str],
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Evaluar alertas con análisis de sentimiento"""
    result = AlertasService(db).evaluar_alertas(user_id, noticias)
    return result

# Endpoints de gestión
@alertas_router.put('/alertas/{alerta_id}/desactivar', tags=['Alertas'])
def put_desactivar_alerta(alerta_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Desactivar una alerta específica (solo si pertenece al usuario)"""
    alerta = AlertasService(db).obtener_alerta_por_id(alerta_id)
    if not alerta or alerta.get('user_id') != user_id:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    result = AlertasService(db).desactivar_alerta(alerta_id)
    if result:
        return {"message": "Alerta desactivada correctamente"}
    return {"message": "Alerta no encontrada"}

@alertas_router.delete('/alertas/{alerta_id}', tags=['Alertas'])
def delete_alerta(alerta_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Eliminar una alerta (solo si pertenece al usuario)"""
    alerta = AlertasService(db).obtener_alerta_por_id(alerta_id)
    if not alerta or alerta.get('user_id') != user_id:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    success = AlertasService(db).eliminar_alerta(alerta_id)
    if success:
        return {"message": "Alerta eliminada correctamente"}
    return {"message": "Alerta no encontrada"}

# Endpoints de testing
@alertas_router.post('/test/sentiment', tags=['Testing'])
def test_sentiment_analysis(noticias: List[str]):
    """Endpoint para testear solo análisis de sentimiento"""
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