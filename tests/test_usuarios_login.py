from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_demo_ok():
    response = client.post(
        "/login",
        json={
            "correo": "demo@finz.com",
            "contrasena": "demo123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_credentials():
    response = client.post(
        "/login",
        json={
            "correo": "demo@finz.com",
            "contrasena": "malpassword"
        }
    )
    assert response.status_code == 400