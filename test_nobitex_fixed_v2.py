import socket
import urllib.request
import json
import ssl

# آی‌پی‌های موفق (از نظر اتصال)
TARGET_IP = "185.143.233.5"

# هویت‌سازی برای دور زدن فایروال
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9,fa;q=0.8',
    'Referer': 'https://nobitex.ir/',
    'Host': 'api.nobitex.ir',  # این حیاتی است برای سرورهای مجازی (Virtual Hosting)
    'Connection': 'keep-alive'
}

_orig_getaddrinfo = socket.getaddrinfo

def custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host == "api.nobitex.ir":
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (TARGET_IP, port))]
    return _orig_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = custom_getaddrinfo

print(f"[*] Testing with full browser headers against {TARGET_IP}...")

try:
    req = urllib.request.Request(
        "https://api.nobitex.ir/v2/orderbook/BTCUSDT",
        headers=HEADERS
    )
    
    # استفاده از تنظیمات پیش‌فرض اما با Hostname Check دقیق
    ctx = ssl.create_default_context()
    
    with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
        if response.status == 200:
            print("✅ موفقیت‌آمیز! فایروال دور زده شد.")
            data = json.loads(response.read().decode('utf-8'))
            print(f"Status: {data.get('status')}")
            print(f"Best Bid: {data['bids'][0] if 'bids' in data else 'N/A'}")
        else:
            print(f"Received status: {response.status}")
except Exception as e:
    print(f"❌ خطا: {e}")
