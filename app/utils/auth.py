# finz/app/utils/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.middlewares.jwt_bearer import JWTBearer
from datetime import datetime, timedelta, timezone
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY no está definida en variables de entorno")

def crear_token_jwt(data: dict) -> str:
    """Crear un token de acceso (corta duración)"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def crear_refresh_token(data: dict) -> str:
    """Crear un token de refresco (larga duración)"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verificar_refresh_token(token: str) -> dict:
    """Verifica que el refresh token sea válido"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expirado, por favor inicia sesión de nuevo"
            )
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido"
        )
    
def get_current_user_id(
        credentials: HTTPAuthorizationCredentials = Depends(JWTBearer())
) -> int:
    """Dependencia para obtener el user_id del token JWT"""
    jwt_bearer = JWTBearer()
    return jwt_bearer.get_user_id_from_token(credentials.credentials)