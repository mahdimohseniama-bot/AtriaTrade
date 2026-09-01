import pytest
from fastapi.testclient import TestClient
from src.web.server import WebServer

def test_web_server_auth_disabled_by_default():
    server = WebServer(api_token=None)
    client = TestClient(server.app)
    
    # Endpoints should work without token
    res = client.get("/api/status")
    assert res.status_code == 200
    
    res = client.post("/api/pause")
    assert res.status_code == 200
    assert res.json()["state"] == "paused"

def test_web_server_auth_enabled_blocks_unauthorized():
    token = "atria_super_secret_token_123"
    server = WebServer(api_token=token)
    client = TestClient(server.app)
    
    # Public route remains accessible
    res = client.get("/api/status")
    assert res.status_code == 200
    
    # Protected route without auth should return 401
    res_pause = client.post("/api/pause")
    assert res_pause.status_code == 401
    
    # Protected route with wrong token should return 401
    res_panic_wrong = client.post("/api/panic", headers={"Authorization": "Bearer wrong_token"})
    assert res_panic_wrong.status_code == 401

def test_web_server_auth_enabled_accepts_valid_token():
    token = "atria_super_secret_token_123"
    server = WebServer(api_token=token)
    client = TestClient(server.app)
    
    # 1. Bearer Header
    res_pause = client.post("/api/pause", headers={"Authorization": f"Bearer {token}"})
    assert res_pause.status_code == 200
    assert res_pause.json()["state"] == "paused"
    
    # 2. X-API-Key Header
    res_resume = client.post("/api/resume", headers={"X-API-Key": token})
    assert res_resume.status_code == 200
    assert res_resume.json()["state"] == "running"
    
    # 3. Query Param
    res_panic = client.post(f"/api/panic?token={token}")
    assert res_panic.status_code == 200
    assert res_panic.json()["action"] == "panic_triggered"
