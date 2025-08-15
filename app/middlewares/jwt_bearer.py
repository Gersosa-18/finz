from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

SECRET_KEY = "tu_secreto_super_seguro"

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        credentials: HTTPAuthorizationCredentials | None = await super().__call__(request)
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se proporcionó token")
        if credentials.scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token inválido")
        if not self.verify_jwt(credentials.credentials):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token expirado o inválido")
        return credentials
        
    def verify_jwt(self, token: str) -> bool:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            # Acá podés validar campos del payload si querés, ej: 'sub', 'exp'
            return True
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
        except jwt.InvalidTokenError:
            return False