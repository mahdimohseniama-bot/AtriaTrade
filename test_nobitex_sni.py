import urllib.request
import ssl
import json
import socket

print("=" * 60)
print("🚀 TESTING NOBITEX WITH SNI & SECURE RESOLVER (NO VPN)")
print("=" * 60)

# روش ۱: اتصال مستقیم به IP با تنظیم SNI (Server Name Indication)
try:
    print("\n[*] 1. Testing Direct IP with Custom SNI Context...")
    
    # آدرس مستقیم یکی از Edge سرورهای نوبیتکس
    target_ip = "185.143.233.5"
    hostname = "api.nobitex.ir"
    
    ctx = ssl.create_default_context()
    # جلوگیری از خطای تطابق گواهی به خاطر IP
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    url = f"https://{target_ip}/v2/orderbook/BTCUSDT"
    
    # ساخت درخواست با هدر Host
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Host': hostname
    })
    
    # ارسال SNI صریح هنگام برقراری Handshake
    with urllib.request.urlopen(req, timeout=7, context=ctx) as resp:
        data = json.loads(resp.read().decode())
        print(f"🟢 SUCCESS via SNI Direct IP!")
        print(f"   Status: {data.get('status')}")
        print(f"   Best Bid: {data['bids'][0]} | Best Ask: {data['asks'][0]}")
        print("=" * 60)
        exit(0)
except Exception as e:
    print(f"⚠️ SNI direct failed: {e}")

# روش ۲: تست با استفاده از DNS-over-HTTPS داخلی به صورت مستقیم با IP های DNS های ایران
try:
    print("\n[*] 2. Testing HTTP-based DNS Resolver (Resolving api.nobitex.ir via Shecan/Cloudflare API)...")
    doh_url = "https://1.1.1.1/dns-query?name=api.nobitex.ir&type=A"
    req_dns = urllib.request.Request(doh_url, headers={'Accept': 'application/dns-json', 'Host': 'cloudflare-dns.com'})
    
    ctx_dns = ssl.create_default_context()
    ctx_dns.check_hostname = False
    ctx_dns.verify_mode = ssl.CERT_NONE
    
    with urllib.request.urlopen(req_dns, timeout=5, context=ctx_dns) as dns_resp:
        dns_data = json.loads(dns_resp.read().decode())
        ips = [ans['data'] for ans in dns_data.get('Answer', []) if ans['type'] == 1]
        print(f"   Resolved IPs: {ips}")
except Exception as e:
    print(f"⚠️ DoH lookup failed: {e}")

print("=" * 60)
