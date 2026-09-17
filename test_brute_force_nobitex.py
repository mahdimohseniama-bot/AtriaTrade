import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import ssl

print("=" * 60)
print("🔍 BRUTE-FORCE CONNECTION TEST (REQUESTS + TLS FORCING)")
print("=" * 60)

# ۱. تست HTTPS با کنترل کامل TLS
try:
    print("\n[*] Testing HTTPS (requests library)...")
    session = requests.Session()
    # تنظیم TLS نسخه ۱.۲
    session.mount('https://', requests.adapters.HTTPAdapter(poolmanager=PoolManager(ssl_version=ssl.PROTOCOL_TLSv1_2)))
    
    response = session.get("https://api.nobitex.ir/v2/orderbook/BTCUSDT", timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"🟢 HTTPS SUCCESS: {response.status_code}")
    print(f"   Data: {response.json()['bids'][0] if 'bids' in response.json() else 'No data'}")
except Exception as e:
    print(f"🔴 HTTPS FAILED: {e}")

# ۲. تست HTTP معمولی (بدون S)
try:
    print("\n[*] Testing HTTP (no encryption)...")
    # نوبیتکس احتمالا ریدایرکت کند یا ۴۰۳ بدهد، اما اگر کانکشن باز شود یعنی فیلترینگ فقط روی لایه TLS است
    response = requests.get("http://api.nobitex.ir/v2/orderbook/BTCUSDT", timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"🟢 HTTP SUCCESS: {response.status_code}")
except Exception as e:
    print(f"🔴 HTTP FAILED: {e}")

print("=" * 60)
