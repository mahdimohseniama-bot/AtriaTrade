import socket
import requests

# کش آی‌پی‌ها برای حداکثر سرعت
IP_CACHE = {}

def doh_resolve(hostname):
    if hostname in IP_CACHE:
        return IP_CACHE[hostname]
    # استفاده از DoH مستقیم کلودفلر یا شکن
    doh_urls = [
        f"https://1.1.1.1/dns-query?name={hostname}&type=A",
        f"https://dns.google/resolve?name={hostname}&type=A"
    ]
    for url in doh_urls:
        try:
            # ارسال درخواست DoH با هدر استاندارد DNS JSON
            res = requests.get(url, headers={"accept": "application/dns-json"}, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if "Answer" in data:
                    for ans in data["Answer"]:
                        if ans.get("type") == 1: # رکورد A
                            ip = ans.get("data")
                            IP_CACHE[hostname] = ip
                            return ip
        except Exception:
            continue
    return hostname

_orig_getaddrinfo = socket.getaddrinfo

def custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    try:
        # اگر هاست یک دامنه است، با DoH آی‌پی واقعی‌اش را استخراج کن
        if host == "api.nobitex.ir" or not host.replace('.', '').isdigit():
            resolved_ip = doh_resolve(host)
            if resolved_ip != host:
                return _orig_getaddrinfo(resolved_ip, port, family, type, proto, flags)
    except Exception:
        pass
    return _orig_getaddrinfo(host, port, family, type, proto, flags)

# اعمال پچ
socket.getaddrinfo = custom_getaddrinfo

# تست مستقیم ارتباط با سرور نوبیتکس
urls = [
    ("Market Stats", "https://api.nobitex.ir/market/stats"),
    ("Orderbook BTC", "https://api.nobitex.ir/v2/orderbook/BTCUSDT"),
    ("Public Status", "https://api.nobitex.ir/status")
]

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
}

print("[*] تست اتصال با DoH (DNS over HTTPS)...")

for title, url in urls:
    try:
        res = requests.get(url, headers=headers, timeout=10)
        print(f"[{title}] -> Status: {res.status_code}")
        if res.status_code == 200:
            print(f"  ✅ پاسخ موفق: {res.text[:120]}...\n")
        else:
            print(f"  ⚠️ پاسخ سرور: {res.status_code} | {res.text[:120]}\n")
    except Exception as e:
        print(f"  ❌ خطای ارتباط: {e}\n")
