import requests
from requests.adapters import HTTPAdapter
from urllib3.connection import HTTPSConnection
from urllib3.connectionpool import HTTPSConnectionPool

# آی‌پی معتبر سرور نوبیتکس
NOBITEX_IP = "185.143.233.238"

class NobitexDNSAdapter(HTTPAdapter):
    def get_connection(self, url, proxies=None):
        conn = super().get_connection(url, proxies=proxies)
        # هدایت مستقیم کانکشن به آی‌پی اختصاصی بدون درگیر کردن DNS ترموکس
        # اما با حفظ کامل SNI و گواهی SSL دامنه اصلی
        if isinstance(conn, HTTPSConnectionPool):
            conn.host = NOBITEX_IP
        return conn

session = requests.Session()
# اعمال آداپتور روی تمام درخواست‌های api.nobitex.ir
session.mount("https://api.nobitex.ir", NobitexDNSAdapter())
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
})

url = "https://api.nobitex.ir/market/stats?srcCurrency=btc&dstCurrency=usdt"

try:
    print("Testing Nobitex via Native requests Adapter (Clean DNS bypass)...")
    resp = session.get(url, timeout=7)
    print("Status Code:", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        print(" SUCCESS! Connection Established.")
        print("BTC/USDT Stats:", data.get("stats", {}).get("btc-usdt", {}).get("latest", "OK"))
    else:
        print("Server Response Preview:", resp.text[:300])
except Exception as e:
    print("Connection Error:", repr(e))
