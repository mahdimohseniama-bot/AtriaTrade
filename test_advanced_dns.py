import urllib.request
import json
import socket
import ssl

print("=" * 60)
print("🚀 ATRIA-TRADE DEEP DNS & NETWORK PROBE")
print("=" * 60)

HOST = "api.nobitex.ir"

# Method 1: DoH (DNS over HTTPS via Cloudflare / Google)
print("\n[*] 1. Testing DNS-over-HTTPS (Bypasses Android netd)...")
doh_urls = [
    f"https://1.1.1.1/dns-query?name={HOST}&type=A",
    f"https://dns.google/resolve?name={HOST}&type=A"
]

resolved_ips = []
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

for doh in doh_urls:
    try:
        req = urllib.request.Request(doh, headers={"Accept": "application/dns-json", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for ans in data.get("Answer", []):
                if ans.get("type") == 1: # Type A record
                    resolved_ips.append(ans.get("data"))
            if resolved_ips:
                print(f"    [+] DoH Success via {doh.split('/')[2]} -> IP: {resolved_ips}")
                break
    except Exception as e:
        print(f"    [-] DoH {doh.split('/')[2]} failed: {e}")

# Method 2: Standard Socket
print(f"\n[*] 2. Testing Standard Socket gethostbyname({HOST})...")
try:
    ip = socket.gethostbyname(HOST)
    print(f"    [+] OS Resolved successfully -> IP: {ip}")
except Exception as e:
    print(f"    [-] OS gethostbyname failed -> {e}")

# Method 3: Live API Orderbook Hit
print("\n[*] 3. Testing Direct HTTPS Request to Nobitex...")
test_url = "https://api.nobitex.ir/v2/orderbook/BTCUSDT"
req = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=6) as response:
        res_data = json.loads(response.read().decode('utf-8'))
        if res_data.get("status") == "ok":
            print(f"    [+] HTTP 200 OK! Live BTCUSDT Orderbook received successfully! 🟢")
            print(f"    [+] Asks sample: {res_data.get('asks', [])[:1]}")
            print(f"    [+] Bids sample: {res_data.get('bids', [])[:1]}")
            print("\n" + "=" * 60)
            print("🎉 ALL GREEN! Nobitex connection is completely operational!")
            print("=" * 60)
except Exception as e:
    print(f"    [-] Direct API Request Failed -> {type(e).__name__}: {e}")
    print("\n" + "=" * 60)
    print("⚠️ نکته: اگر مرحله ۳ خطا داد، تنظیمات روتینگ فیلترشکن را بررسی یا موقتاً VPN را قطع کن.")
    print("=" * 60)
