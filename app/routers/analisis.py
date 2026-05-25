from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from app.services.analisis_service import AnalisisService
from app.utils.auth import get_current_user_id
import base64

analisis_router = APIRouter(prefix="/analisis", tags=["Analisis"])

MIME_PERMITIDOS = {"image/png", "image/jpeg", "image/jpg", "image/webp"}

@analisis_router.post("/chart")
async def analizar_chart(
    ticker: str = Form(...),
    timeframe: str = Form(...),
    imagen: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    observacion: str = Form(default="")
):
    """
    Análisis multi-agente de un chart.
    - Agente 1 (técnico): lee el chart con visión
    - Agente 2 (fundamental): lee datos de yfinance
    - Agente 3 (moderador): sintetiza y emite veredicto
    """
    if imagen.content_type not in MIME_PERMITIDOS:
        raise HTTPException(status_code=400, detail=f"Formato no soportado: {imagen.content_type}")
 
    if timeframe not in ("semanal", "mensual"):
        raise HTTPException(status_code=400, detail="timeframe debe ser 'semanal' o 'mensual'")
 
    contenido = await imagen.read()
    imagen_base64 = base64.b64encode(contenido).decode("utf-8")
 
    try:
        service = AnalisisService()
        resultado = service.analizar(
            ticker=ticker.strip().upper(),
            timeframe=timeframe,
            imagen_base64=imagen_base64,
            media_type=imagen.content_type,
            observacion=observacion,
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
