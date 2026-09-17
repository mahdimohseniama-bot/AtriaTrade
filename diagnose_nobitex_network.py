import socket
import requests

HOST = "api.nobitex.ir"
URL = "https://api.nobitex.ir/market/stats"
PARAMS = {"srcCurrency": "btc", "dstCurrency": "usdt"}

print("== DNS ==")
try:
    addresses = socket.getaddrinfo(HOST, 443, type=socket.SOCK_STREAM)
    ips = sorted({item[4][0] for item in addresses})
    print("Resolved:", ", ".join(ips))
except OSError as exc:
    print("DNS FAILED:", repr(exc))

print("\n== HTTPS ==")
try:
    response = requests.get(
        URL,
        params=PARAMS,
        timeout=(5, 10),
        headers={"Accept": "application/json", "User-Agent": "AtriaTrade/1.0"},
    )
    print("HTTP:", response.status_code)
    print("Body:", response.text[:300])
except requests.RequestException as exc:
    print("HTTPS FAILED:", repr(exc))
