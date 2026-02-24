from fastapi import APIRouter, Depends
from app.middlewares.jwt_bearer import JWTBearer
from app.services.mag7_service import get_cache

mag7 = APIRouter(prefix="/mercado", tags=["Mercado"])

@mag7.get("/ytd", dependencies=[Depends(JWTBearer())])
def ytd_mag7_vs_spy():
    return get_cache()