import pytest
from src.dashboard.auth import SecureAuthManager
from src.dashboard.server import DashboardServer

def test_public_endpoint():
    server = DashboardServer()
    res = server.get_public_status()
    assert res["online"] is True
    assert res["system"] == "AtriaTrade"

def test_protected_dashboard_summary():
    auth = SecureAuthManager()
    server = DashboardServer(auth_manager=auth)
    
    # بدون توکن معتبر
    res = server.get_dashboard_summary("fake_token")
    assert res["success"] is False
    assert "Unauthorized" in res["error"]
    
    # با توکن معتبر
    valid_token = auth.generate_token("mehdi", "read_only")
    res_ok = server.get_dashboard_summary(valid_token)
    assert res_ok["success"] is True
    assert res_ok["user"] == "mehdi"
    assert res_ok["data"]["mode"] == "PAPER_TRADING"

def test_role_based_access_control():
    auth = SecureAuthManager()
    server = DashboardServer(auth_manager=auth)
    
    read_only_token = auth.generate_token("viewer", "read_only")
    admin_token = auth.generate_token("admin_user", "admin")
    
    # کاربر معمولی نباید بتواند استیت را عوض کند
    res_forbidden = server.update_bot_state("mode", "LIVE", read_only_token)
    assert res_forbidden["success"] is False
    assert "Forbidden" in res_forbidden["error"]
    
    # کاربر ادمین باید بتواند
    res_admin = server.update_bot_state("active_positions", 2, admin_token)
    assert res_admin["success"] is True
    assert server.state_data["active_positions"] == 2
