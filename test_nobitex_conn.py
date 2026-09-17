import socket
import urllib3
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import connection

# تنظیم DNSهای پایدار ایران و بین‌الملل برای حل NameResolutionError در ترموکس
DNS_IPS = ["178.22.122.100", "1.1.1.1", "8.8.8.8"]

def get_ip_nobitex():
    import urllib.request
    import json
    # استفاده از DoH مستقیم برای دریافت آی‌پی رسمی نوبیتکس
    doh_urls = [
        "https://1.1.1.1/dns-query?name=api.nobitex.ir&type=A",
        "https://dns.google/resolve?name=api.nobitex.ir&type=A"
    ]
    for doh in doh_urls:
        try:
            req = urllib.request.Request(doh, headers={"Accept": "application/dns-json"})
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode())
                if "Answer" in data:
                    ip = data["Answer"][-1]["data"]
                    return ip
        except Exception:
            continue
    return None

ip = get_ip_nobitex()
print(f"Resolved api.nobitex.ir to IP: {ip}")

if ip:
    # وصل شدن مستقیم با هدایت هاست نوبیتکس به آی‌پی پیدا شده
    orig_create_connection = connection.create_connection

    def patched_create_connection(address, *args, **kwargs):
        host, port = address
        if host == "api.nobitex.ir":
            return orig_create_connection((ip, port), *args, **kwargs)
        return orig_create_connection(address, *args, **kwargs)

    connection.create_connection = patched_create_connection

    url = "https://api.nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print("Status Code:", resp.status_code)
        if resp.status_code == 200:
            data = resp.json()
            stats = data.get("stats", {}).get("usdt-rls", {})
            print("SUCCESS! Nobitex Market Data Connected!")
            print(f"USDT/RLS Latest Price: {stats.get('latest', 'N/A')} RLS")
        else:
            print("Response:", resp.text[:200])
    except Exception as e:
        print("Connection error:", e)
else:
    print("Could not resolve IP via DoH, let's test direct socket.")
