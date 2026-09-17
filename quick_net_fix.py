import socket
import urllib.request
import json
import sys

TARGET_HOST = "api.nobitex.ir"
TEST_URL = "https://api.nobitex.ir/v2/orderbook/BTCUSDT"

print("=" * 55)
print("🔍 ATRIA-TRADE NETWORK & DNS DIAGNOSTIC SUITE")
print("=" * 55)

# 1. System Default DNS Lookup
print(f"[*] 1. Testing Default OS DNS resolution for: {TARGET_HOST}")
try:
    resolved_ip = socket.gethostbyname(TARGET_HOST)
    print(f"    [+] SUCCESS! Resolved IP: {resolved_ip}")
except socket.gaierror as e:
    print(f"    [-] FAILED! OS DNS cannot resolve: {e}")

# 2. Testing HTTP Request directly
print(f"\n[*] 2. Testing Direct HTTPS Request to Nobitex API...")
req = urllib.request.Request(
    TEST_URL, 
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
)

try:
    with urllib.request.urlopen(req, timeout=7) as response:
        status = response.getcode()
        body = response.read().decode('utf-8')
        print(f"    [+] HTTP Response Status: {status}")
        data = json.loads(body)
        if data.get("status") == "ok":
            bids = len(data.get("bids", []))
            asks = len(data.get("asks", []))
            print(f"    [+] DATA STREAM ACTIVE! Bids: {bids}, Asks: {asks}")
            print("\n🎉 CONNECTION IS HEALTHY AND READY FOR PAPER TRADING!")
            sys.exit(0)
except Exception as e:
    print(f"    [-] HTTP Connection Failed: {type(e).__name__}: {e}")

# 3. Termux DNS Advice
print("\n" + "=" * 55)
print("🛠 ACTIONABLE DIAGNOSTIC HINTS:")
print("1. اگر فیلترشکن (v2rayNG/NekoBox) روشنه: حتماً 'Routing' رو روی 'Bypass LAN & Mainland/Iran' بذار.")
print("2. اگه فیلترشکن خاموشه یا اختلال داری، می‌تونیم DNSهای ترموکس رو با چند دستور ست کنیم.")
print("=" * 55)
