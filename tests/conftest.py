import pytest
import os
from dotenv import load_dotenv

load_dotenv('.env.test', override=True)

from sqlalchemy.orm import Session
from app.config.database import engine, Base
from tests.seeds import seed_usuario_demo

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    db_url = os.getenv('DATABASE_URL')
    
    if 'supabase' in db_url.lower():
        raise Exception("❌ ¡Error! Intentando usar SB")
    
    Base.metadata.create_all(bind=engine)
    
    db = Session(engine)
    try:
        seed_usuario_demo(db)
    finally:
        db.close()
    
    yield
    
    Base.metadata.drop_all(bind=engine)
    engine.dispose()  