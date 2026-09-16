import dns.resolver

DOMAIN = "api.nobitex.ir"

DNS_SERVERS = [
    "178.22.122.100",
    "78.157.108.10",
    "10.202.10.202",
    "8.8.8.8",
    "1.1.1.1",
]

for server in DNS_SERVERS:
    print(f"\n=== DNS {server} ===")

    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [server]
    resolver.timeout = 3
    resolver.lifetime = 5

    try:
        answers = resolver.resolve(DOMAIN, "A")
        ips = [answer.to_text() for answer in answers]
        print(f"OK: {DOMAIN} -> {ips}")
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}")
