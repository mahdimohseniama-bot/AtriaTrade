import pytest
import requests
from src.exchange.utils import retry_on_network_error

def test_retry_on_network_error_success_after_fail():
    attempts = 0
    
    @retry_on_network_error(max_retries=3, backoff_factor=0.01)
    def mock_api_call():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise requests.exceptions.ConnectionError("Mock Network Error")
        return "SUCCESS"
        
    result = mock_api_call()
    assert result == "SUCCESS"
    assert attempts == 3

def test_retry_on_network_error_max_retries_exceeded():
    attempts = 0
    
    @retry_on_network_error(max_retries=2, backoff_factor=0.01)
    def mock_api_call():
        nonlocal attempts
        attempts += 1
        raise requests.exceptions.Timeout("Mock Timeout")
        
    with pytest.raises(RuntimeError) as excinfo:
        mock_api_call()
        
    assert "Failed after 2 retries" in str(excinfo.value)
    assert attempts == 2

def test_retry_ignores_non_network_errors():
    attempts = 0
    
    @retry_on_network_error(max_retries=3)
    def mock_api_call():
        nonlocal attempts
        attempts += 1
        raise PermissionError("Invalid API Key")
        
    with pytest.raises(PermissionError):
        mock_api_call()
        
    # نباید تلاش مجددی صورت بگیرد
    assert attempts == 1
