import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import ssl

print("=" * 60)
print("🔍 BRUTE-FORCE TEST v2 (FIXED ADAPTER + DIRECT IP)")
print("=" * 60)

TLS12 = ssl.PROTOCOL_TLSv1_2

class TLS12Adapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_version'] = TLS12
        super().init_poolmanager(*args, **kwargs)

session = GAPGPTMASKTOKENmshaaiwq8nX0X
session.mount('https://', TLS12Adapter())

# ۱. تست دامنه با requests + TLS 1.2
try:
    print("\n[*] 1. Domain via requests + TLS 1.2...")
    r = session.get("https://api.nobitex.ir/v2/orderbook/BTCUSDT", timeout=10)
    print(f"🟢 SUCCESS: {r.status_code} | first bid: {r.json()['bids'][0]}")
except Exception as e:
    print(f"🔴 FAILED: {e}")

# ۲. تست IP مستقیم با Host header (سشن requests خودش SNI را از Host می‌گیرد)
try:
    print("\n[*] 2. Direct IP 185.143.233.5 + Host header...")
    r = session.get("https://185.143.233.5/v2/orderbook/BTCUSDT",
                    headers={'Host': 'api.nobitex.ir'}, timeout=10, verify=False)
    print(f"🟢 SUCCESS: {r.status_code} | first bid: {r.json()['bids'][0]}")
except Exception as e:
    print(f"🔴 FAILED: {e}")

# ۳. Resolve دستی از طریق DoH شکن (IP مستقیم سرور DNS، بدون نیاز به دامنه)
try:
    print("\n[*] 3. DoH via Shecan (178.22.122.100)...")
    r = session.get("https://178.22.122.100/dns-query?name=api.nobitex.ir&type=A",
                    headers={'Accept': 'application/dns-json'}, timeout=8, verify=False)
    ips = [a['data'] for a in r.json().get('Answer', []) if a.get('type') == 1]
    print(f"🟢 Resolved IPs: {ips}")
except Exception as e:
    print(f"🔴 FAILED: {e}")

print("=" * 60)
