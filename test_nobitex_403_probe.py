import socket
import ssl
import urllib.request
import urllib.error

TARGET_IPS = [
    "185.143.233.5",
    "185.143.234.5",
    "185.143.232.5",
    "94.182.183.187",
]

URLS = [
    "https://api.nobitex.ir/",
    "https://api.nobitex.ir/v2/orderbook/BTCUSDT",
    "https://api.nobitex.ir/v2/orderbook/USDTIRT",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://nobitex.ir/",
    "Origin": "https://nobitex.ir",
    "Connection": "close",
}

_orig_getaddrinfo = socket.getaddrinfo

def run_one(ip, url):
    def custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        if host == "api.nobitex.ir":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port))]
        return _orig_getaddrinfo(host, port, family, type, proto, flags)

    socket.getaddrinfo = custom_getaddrinfo

    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    ctx = ssl.create_default_context()

    print("\n" + "="*80)
    print(f"[IP]  {ip}")
    print(f"[URL] {url}")

    try:
        with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
            status = r.status
            hdrs = dict(r.headers.items())
            body = r.read(600)
            print(f"[OK] HTTP {status}")
            print("[HDR] sample:")
            for k in sorted(hdrs.keys()):
                lk = k.lower()
                if any(x in lk for x in ["server","date","content-type","content-length","set-cookie","cf-","x-","arvan","via","location"]):
                    print(f"  {k}: {hdrs[k]}")
            print(f"[BODY] first_bytes={len(body)}")
            print(body[:300])
    except urllib.error.HTTPError as e:
        hdrs = dict(e.headers.items()) if e.headers else {}
        body = b""
        try:
            body = e.read(800) or b""
        except Exception:
            pass
        print(f"[ERR] HTTPError {e.code} {e.reason}")
        print("[HDR] sample:")
        for k in sorted(hdrs.keys()):
            lk = k.lower()
            if any(x in lk for x in ["server","date","content-type","content-length","set-cookie","cf-","x-","arvan","via","location"]):
                print(f"  {k}: {hdrs[k]}")
        print(f"[BODY] first_bytes={len(body)}")
        print(body[:350])
    except Exception as e:
        print(f"[ERR] {type(e).__name__}: {e}")

if __name__ == "__main__":
    for ip in TARGET_IPS:
        for url in URLS:
            run_one(ip, url)
