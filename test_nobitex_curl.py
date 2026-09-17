import subprocess
import json

TARGET_IP = "185.143.233.5"
URL = "https://api.nobitex.ir/v2/orderbook/BTCUSDT"

# اجرای curl با تزریق IP به عنوان resolve تا هدر TLS و Host دقیقاً مرورگری باشد
cmd = [
    "curl", "-s", "-i",
    "--resolve", f"api.nobitex.ir:443:{TARGET_IP}",
    "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "-H", "Accept: application/json, text/plain, */*",
    "-H", "Accept-Language: fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
    "-H", "Origin: https://nobitex.ir",
    "-H", "Referer: https://nobitex.ir/",
    URL
]

print(f"[*] Testing cURL resolve impersonation against {TARGET_IP}...")
result = subprocess.run(cmd, capture_output=True, text=True)

output = result.stdout
headers_part = output.split("\r\n\r\n")[0] if "\r\n\r\n" in output else output[:500]
body_part = output.split("\r\n\r\n")[1] if "\r\n\r\n" in output else ""

print("\n--- Response Headers ---")
print(headers_part)

print("\n--- Response Body Sample (first 300 chars) ---")
print(body_part[:300])

if "bids" in body_part:
    print("\n✅ فوق‌العاده! موفقیت کامل! دیتای Orderbook با موفقیت دریافت شد!")
