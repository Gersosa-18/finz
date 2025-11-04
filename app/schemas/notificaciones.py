from pydantic import BaseModel

class SuscripcionPush(BaseModel):
    subscription: dict