import socket
import urllib.request
import json
import ssl

print("🔍 [1/3] تست DNS Resolution...")
try:
    ip = socket.gethostbyname("api.nobitex.ir")
    print(f"✅ دامنه api.nobitex.ir با موفقیت به IP زیر Resolve شد: {ip}")
except Exception as e:
    print(f"❌ خطای DNS: {e}")

print("\n🔍 [2/3] تست دریافت Ticker از نوبیتکس...")
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(
    "https://api.nobitex.ir/market/stats",
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
)

try:
    with urllib.request.urlopen(req, timeout=8, context=ctx) as response:
        status = response.getcode()
        body = response.read().decode('utf-8')
        data = json.loads(body)
        print(f"✅ پاسخ با کد {status} دریافت شد.")
        if "stats" in data:
            btc_irt = data["stats"].get("btc-rls", {}).get("latest", "N/A")
            print(f"📊 نمونه قیمت BTC-RLS: {btc_irt}")
        elif "status" in data:
            print(f"📊 وضعیت API: {data.get('status')}")
except Exception as e:
    print(f"❌ خطای درخواست HTTP: {e}")

print("\n🔍 [3/3] نتیجه‌گیری:")
print("اگر خطای Errno 7 (getaddrinfo) داری، Split-Tunneling وی‌پی‌ان روشن نیست یا DNS ست نشده است.")
