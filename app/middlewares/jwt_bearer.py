# finz/app/middlewares/jwt_bearer.py
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY no está definida en variables de entorno")


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = False):
        # Desactivamos auto_error para controlar la excepción nosotros mismos y emitir 401 en vez de 403
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        credentials: Optional[HTTPAuthorizationCredentials] = await super().__call__(request)

        # 1. Cabecera ausente o incompleta
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No autenticado. Token ausente",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 2. Esquema incorrecto
        if credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Esquema de autenticación inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 3. Validación y extracción del payload
        payload = self.verify_jwt(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado o inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Cachear payload en el request para reutilización sin re-decodificar
        request.state.jwt_payload = payload
        return credentials

    def verify_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if "exp" not in payload or payload.get("type") != "access":
                return None
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None

    def get_user_id_from_token(self, token: str) -> int:
        """Extrae el user_id del token asegurando siempre respuesta 401 ante fallos"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token no contiene user_id",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return int(user_id)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Error procesando token",
                headers={"WWW-Authenticate": "Bearer"},
            )