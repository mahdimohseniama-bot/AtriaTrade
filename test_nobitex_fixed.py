import socket
import urllib.request
import json
import ssl

print("=" * 60)
print("🚀 TESTING NOBITEX WITH SOCKET DNS INJECTION (NO VPN)")
print("=" * 60)

# لیست آی‌پی‌های سرورهای نوبیتکس
NOBITEX_IPS = [
    "185.143.233.5",
    "185.143.234.5",
    "94.182.183.187",
    "185.143.232.5"
]

# ذخیره تابع اصلی
_orig_getaddrinfo = socket.getaddrinfo

for ip in NOBITEX_IPS:
    print(f"\n[*] Testing with Injected IP: {ip} ...")
    
    # اورراید کردن رزولور برای دامنه api.nobitex.ir
    def custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        if host == "api.nobitex.ir":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (ip, port))]
        return _orig_getaddrinfo(host, port, family, type, proto, flags)

    socket.getaddrinfo = custom_getaddrinfo
    
    try:
        req = urllib.request.Request(
            "https://api.nobitex.ir/v2/orderbook/BTCUSDT",
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        ctx = ssl.create_default_context()
        
        with urllib.request.urlopen(req, timeout=6, context=ctx) as response:
            if response.status == 200:
                raw_data = response.read().decode('utf-8')
                data = json.loads(raw_data)
                print(f"🟢🟢 SUCCESS WITH IP {ip}!")
                print(f"   Status: {data.get('status')}")
                bids = data.get('bids', [])
                asks = data.get('asks', [])
                if bids and asks:
                    print(f"   Best Bid (خرید): {bids[0]}")
                    print(f"   Best Ask (فروش): {asks[0]}")
                print("\n🎉 اتصال کاملاً مستقیم و بدون فیلترشکن برقرار شد!")
                print("=" * 60)
                exit(0)
    except Exception as e:
        print(f"   🔴 Failed with IP {ip}: {e}")

print("\n⚠️ هیچ‌کدام از IPها پاسخ ندادند.")
print("=" * 60)
