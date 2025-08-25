from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY no está definida en variables de entorno")

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        credentials = await super().__call__(request)
        if not credentials or credentials.scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token inválido")
        
        if not self.verify_jwt(credentials.credentials):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token inválido")
        
        return credentials
        
    def verify_jwt(self, token: str) -> bool:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if 'exp' not in payload:
                return False
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False
        except Exception:
            return False