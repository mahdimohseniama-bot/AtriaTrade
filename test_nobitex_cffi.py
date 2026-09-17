from curl_cffi import requests

TARGET_IP = "185.143.233.5"
URL = "https://api.nobitex.ir/v2/orderbook/BTCUSDT"

# در curl_cffi کلید resolve به صورت دیکشنری {hostname: ip_or_port_spec} پذیرفته می‌شود
resolve_dict = {"api.nobitex.ir": TARGET_IP}

print(f"[*] Testing with curl_cffi (Chrome 120 impersonation) against {TARGET_IP}...")

try:
    r = requests.get(
        URL,
        impersonate="chrome120",
        resolve=resolve_dict,
        headers={
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8",
            "Referer": "https://nobitex.ir/",
        },
        timeout=10
    )
    print(f"Status Code: {r.status_code}")
    if r.status_code == 200:
        print("✅ پیروزی بزرگ! WAF ابرآروان دور زده شد!")
        print("Data sample:", r.text[:250])
    else:
        print("⚠️ Response Status:", r.status_code)
        print("Response sample:", r.text[:300])
except Exception as e:
    print(f"❌ Error: {e}")
