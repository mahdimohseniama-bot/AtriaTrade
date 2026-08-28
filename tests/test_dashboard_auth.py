import pytest
from src.dashboard.auth import SecureAuthManager


def test_token_generation_and_authentication():
    auth = SecureAuthManager(token_ttl_hours=1)
    token = auth.generate_token_for_user(username="mehdi_admin", role="admin")

    assert isinstance(token, str)
    assert len(token) > 20

    is_valid, user, role = auth.authenticate_token(token, client_ip="192.168.1.100")
    assert is_valid is True
    assert user == "mehdi_admin"
    assert role == "admin"


def test_invalid_token_fails():
    auth = SecureAuthManager()
    auth.generate_token_for_user(username="viewer", role="read_only")

    is_valid, user, role = auth.authenticate_token("wrong_invalid_token_12345", client_ip="192.168.1.50")
    assert is_valid is False
    assert user is None
    assert role is None


def test_rate_limiting_and_lockout():
    auth = SecureAuthManager(max_failed_attempts=3, lockout_minutes=5)
    ip = "10.0.0.99"

    for _ in range(3):
        auth.authenticate_token("wrong_token", client_ip=ip)

    assert auth.is_locked_out(ip) is True

    valid_token = auth.generate_token_for_user("user1", "read_only")
    is_valid, _, _ = auth.authenticate_token(valid_token, client_ip=ip)
    assert is_valid is False


def test_token_expiration():
    auth = SecureAuthManager(token_ttl_hours=-1)
    token = auth.generate_token_for_user("expired_user", "read_only")

    is_valid, user, role = auth.authenticate_token(token)
    assert is_valid is False
    assert user is None


def test_token_revocation():
    auth = SecureAuthManager()
    token = auth.generate_token_for_user("revokable_user", "admin")

    is_valid, _, _ = auth.authenticate_token(token)
    assert is_valid is True

    revoked = auth.revoke_token(token)
    assert revoked is True

    is_valid, _, _ = auth.authenticate_token(token)
    assert is_valid is False
