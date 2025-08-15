from datetime import datetime, timedelta
import jwt

SECRET_KEY = "tu_clave_secreta_aqui"
ALGORITH = "HS256"
EXPIRE_MINUTES = 60

def crear_token_jwt(data: dict) -> str:
    """Crear un jwt con expiración de 60 min"""
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITH)
    return encoded_jwt