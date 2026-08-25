import time
import logging
from functools import wraps
from typing import Callable, Any
import requests

logger = logging.getLogger(__name__)

def retry_on_network_error(max_retries: int = 3, backoff_factor: float = 0.5):
    """
    دکوراتور برای تلاش مجدد در صورت بروز خطاهای شبکه یا قطعی موقت اینترنت.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.ConnectionError, 
                        requests.exceptions.Timeout, 
                        requests.exceptions.HTTPError) as e:
                    retries += 1
                    wait_time = backoff_factor * (2 ** (retries - 1))
                    logger.warning(
                        f"Network error in {func.__name__} (Attempt {retries}/{max_retries}): {e}. "
                        f"Retrying in {wait_time:.2f} seconds..."
                    )
                    if retries >= max_retries:
                        logger.error(f"Max retries reached for {func.__name__}. Failing.")
                        raise RuntimeError(f"Failed after {max_retries} retries due to network issues.") from e
                    time.sleep(wait_time)
                except Exception as e:
                    # خطاهای غیرشبکه‌ای (مثل کلید اشتباه) نباید Retry شوند
                    raise e
        return wrapper
    return decorator
