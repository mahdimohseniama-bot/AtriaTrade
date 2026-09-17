import requests

# تست اندپوینت مستقیم روی دامنه اصلی nobitex.ir که DNS آن به درستی resolve شده است
url = "https://nobitex.ir/market/stats?srcCurrency=usdt&dstCurrency=rls"
headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36"
}

try:
    print("Connecting to Nobitex via main domain...")
    resp = requests.get(url, headers=headers, timeout=10)
    print("HTTP Status Code:", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        stats = data.get("stats", {}).get("usdt-rls", {})
        print("--> CONNECTION SUCCESSFUL! <--")
        print(f"Latest USDT/RLS: {stats.get('latest', 'N/A')} Rials")
        print(f"Day High: {stats.get('dayHigh', 'N/A')} | Day Low: {stats.get('dayLow', 'N/A')}")
    else:
        print("Response:", resp.text[:250])
except Exception as e:
    print("Connection failed:", repr(e))
