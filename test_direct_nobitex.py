import socket
import requests

NOBITEX_IP = "185.143.234.235"
TARGET_HOST = "api.nobitex.ir"

# Patch DNS resolution فقط برای همین دامنه
_old_getaddrinfo = socket.getaddrinfo

def custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host == TARGET_HOST:
        return _old_getaddrinfo(NOBITEX_IP, port, family, type, proto, flags)
    return _old_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = custom_getaddrinfo

session = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; Termux) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}

url = f"https://{TARGET_HOST}/market/stats?srcCurrency=btc&dstCurrency=rls"
print(f"[*] DNS patched: {TARGET_HOST} -> {NOBITEX_IP}")
print(f"[*] GET {url}")

try:
    # verify=True نگه می‌داریم تا TLS/SNI طبیعی باشد (بدون خطاهای CERT_NONE)
    r = session.get(url, headers=headers, timeout=15)
    print(f"[+] HTTP {r.status_code}")

    # اگر WAF HTML برگرداند، همین‌جا معلوم می‌شود
    ct = (r.headers.get("content-type") or "").lower()
    if "application/json" not in ct:
        print("[!] Non-JSON response (likely WAF / HTML). Preview:")
        print(r.text[:400])
        raise SystemExit(2)

    data = r.json()
    print("[+] JSON keys:", list(data.keys()))

    if data.get("status") == "ok":
        stats = data.get("stats", {}).get("btc-rls", {})
        print("==========================================")
        print("SUCCESS: Nobitex market stats received")
        print(f"BTC-RLS latest : {stats.get('latest')}")
        print(f"BTC-RLS dayLow : {stats.get('dayLow')}")
        print(f"BTC-RLS dayHigh: {stats.get('dayHigh')}")
        print("==========================================")
    else:
        print("[!] API returned non-ok status:")
        print(data)

except requests.exceptions.SSLError as e:
    print("[-] SSL error:", e)
    print("    This usually means certificate/SNI mismatch or interception.")
except Exception as e:
    print(f"[-] Request failed: {type(e).__name__} -> {e}")
