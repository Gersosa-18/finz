# finz/app/utils/auth.py
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from app.middlewares.jwt_bearer import JWTBearer
from datetime import datetime, timedelta, timezone
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY no está definida en variables de entorno")

def crear_token_jwt(data: dict) -> str:
    to_encode = data.copy()
    # CAMBIO: usar UTC
    expire = datetime.now(timezone.utc) + timedelta(minutes=10)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user_id(
        credentials: HTTPAuthorizationCredentials = Depends(JWTBearer())
) -> int:
    """Dependencia para obtener el user_id del token JWT"""
    jwt_bearer = JWTBearer()
    return jwt_bearer.get_user_id_from_token(credentials.credentials)