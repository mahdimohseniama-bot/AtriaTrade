import socket
import dns.resolver # اگر نصب نیست با pip install dnspython نصب می‌شود

# تنظیم یک رزولور سفارشی با DNSهای ایرانی (شکن و الکترو)
resolver = dns.resolver.Resolver()
resolver.nameservers = ['178.22.122.100', '78.157.108.10']

def patched_getaddrinfo(*args, **kwargs):
    host = args[0]
    port = args[1]
    try:
        # اگر دامنه نوبیتکس یا والکس بود از DNS سفارشی استفاده کن
        if 'nobitex' in host or 'wallex' in host:
            answers = resolver.resolve(host, 'A')
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (str(ans), port)) for ans in answers]
    except Exception as e:
        print(f"Custom DNS failed for {host}: {e}")
    # در غیر این صورت از DNS پیش‌فرض سیستم استفاده کن
    return original_getaddrinfo(*args, **kwargs)

# ذخیره متد اصلی و جایگزینی آن
original_getaddrinfo = socket.getaddrinfo
socket.getaddrinfo = patched_getaddrinfo

# حالا تست اتصال واقعی با requests
import requests
try:
    print("Trying to fetch Nobitex Orderbook with Patched DNS...")
    response = requests.get('https://api.nobitex.ir/v2/orderbook/BTCIRT', timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("🎉 SUCCESS! Connection established to Nobitex!")
        print(response.json())
except Exception as e:
    print(f"❌ Connection still failed: {e}")
