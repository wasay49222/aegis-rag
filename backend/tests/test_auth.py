import time
import pytest
from fastapi.testclient import TestClient
from app.main import app

# Create a test client that acts like a fake browser
client = TestClient(app)

# Helper to generate a unique email for every test run
def get_unique_email():
    return f"test_{int(time.time())}@aegis.com"

def test_register_user():
    """Test that we can create a new user."""
    unique_email = get_unique_email()
    response = client.post("/auth/register", json={
        "email": unique_email,
        "password": "SecurePass123!"
    })
    assert response.status_code == 200
    assert response.json()["email"] == unique_email

def test_login_user():
    """Test that we can log in and get a JWT token."""
    unique_email = get_unique_email()
    
    # 1. Register the user first
    client.post("/auth/register", json={
        "email": unique_email,
        "password": "SecurePass123!"
    })
    
    # 2. Now try to login
    response = client.post("/auth/login", json={
        "email": unique_email,
        "password": "SecurePass123!"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_protected_endpoint_no_token():
    """Test that /auth/me blocks users without a token (401)."""
    response = client.get("/auth/me")
    assert response.status_code == 401

def test_protected_endpoint_with_token():
    """Test that /auth/me works when a valid token is provided (200)."""
    unique_email = get_unique_email()
    
    # 1. Register and Login to get a token
    client.post("/auth/register", json={
        "email": unique_email,
        "password": "SecurePass123!"
    })
    login_response = client.post("/auth/login", json={
        "email": unique_email,
        "password": "SecurePass123!"
    })
    token = login_response.json()["access_token"]
    
    # 2. Send the token in the header
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/me", headers=headers)
    
    assert response.status_code == 200
    assert response.json()["email"] == unique_email