import pytest
from app.config.database import engine, Base
from sqlalchemy.orm import Session
from tests.seeds import seed_usuario_demo

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = Session(engine)
    try:
        seed_usuario_demo(db)
    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=engine)