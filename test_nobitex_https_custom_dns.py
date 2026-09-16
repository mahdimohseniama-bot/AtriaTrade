import socket
import ssl
import dns.resolver
import requests
import urllib3

DOMAIN = "api.nobitex.ir"
URL = f"https://{DOMAIN}/v2/orderbook/BTCIRT"
DNS_SERVER = "178.22.122.100"  # در صورت موفقیت، با DNS موفق جایگزین کن

resolver = dns.resolver.Resolver(configure=False)
resolver.nameservers = [DNS_SERVER]
resolver.timeout = 3
resolver.lifetime = 5

answers = resolver.resolve(DOMAIN, "A")
ips = [answer.to_text() for answer in answers]

print(f"Resolved through {DNS_SERVER}: {DOMAIN} -> {ips}")

original_getaddrinfo = socket.getaddrinfo

def custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host == DOMAIN:
        results = []
        for ip in ips:
            results.append(
                (
                    socket.AF_INET,
                    socket.SOCK_STREAM,
                    socket.IPPROTO_TCP,
                    "",
                    (ip, port),
                )
            )
        return results

    return original_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = custom_getaddrinfo

try:
    response = requests.get(
        URL,
        timeout=15,
        headers={
            "User-Agent": "AtriaTrade-Diagnostic/1.0",
            "Accept": "application/json",
        },
    )

    print("HTTP status:", response.status_code)
    print("Final URL:", response.url)
    print("Response preview:", response.text[:500])

except requests.exceptions.SSLError as exc:
    print("TLS/SSL ERROR:", repr(exc))
except requests.exceptions.ConnectionError as exc:
    print("CONNECTION ERROR:", repr(exc))
except requests.exceptions.Timeout as exc:
    print("TIMEOUT:", repr(exc))
except Exception as exc:
    print("OTHER ERROR:", type(exc).__name__, repr(exc))
