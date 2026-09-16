import dns.resolver

DOMAIN = "api.nobitex.ir"

DNS_SERVERS = [
    "185.55.226.26",
    "185.55.225.25",
    "217.218.155.155",
    "217.218.127.127",
    "5.202.100.100",
    "5.200.200.200",
    "10.202.10.202",
    "178.22.122.100",
    "78.157.108.10",
]

for server in DNS_SERVERS:
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [server]
    resolver.timeout = 2
    resolver.lifetime = 4

    try:
        answers = resolver.resolve(DOMAIN, "A")
        ips = [a.to_text() for a in answers]
        print(f"{server}: OK -> {ips}")
    except Exception as exc:
        print(f"{server}: {type(exc).__name__}: {exc}")
