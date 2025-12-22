from sqlalchemy.orm import Session
from app.models.usuarios import Usuarios
from app.services.alertas import AlertasService
def evaluar_alertas(db: Session):
    """
    Job que evalúa alertas.
    Recibe la DB desde el scheduler o desde un test.
    """
    usuarios = db.query(Usuarios).all()

    service = AlertasService(db)
    for usuario in usuarios:
        # AlertasService maneja lógica interna y notificaciones
        service.evaluar_alertas(usuario.id)
            