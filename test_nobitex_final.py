from curl_cffi import requests

# ارسال مستقیم درخواست به آی‌پی سرور نوبیتکس
# و تزریق نام دامنه در هدر Host
url = "https://185.143.233.238/v2/orderbook/USDTIRT"

headers = {
    "Host": "api.nobitex.ir",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    print("Testing Nobitex via Direct IP connection with Host Header + Chrome Impersonation...")
    
    # استفاده از افکت چرخشی مرورگر بدون درگیر شدن با سیستم رزولوشن دامنه‌ها
    resp = requests.get(
        url, 
        headers=headers, 
        impersonate="chrome120", 
        verify=False,  # برای جلوگیری از خطای تطبیق نام دامنه روی آی‌پی عددی در لایه SSL
        timeout=10
    )
    
    print("HTTP Status Code:", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        print("\n==========================================")
        print(" SUCCESS! CONNECTED VIA DIRECT IP & HOST HEADER!")
        bids = data.get("bids", [])
        asks = data.get("asks", [])
        if bids and asks:
            print(f" Best Buy (Bid): {bids[0][0]} Rials")
            print(f" Best Sell (Ask): {asks[0][0]} Rials")
        print("==========================================\n")
    else:
        print("Response Snippet:", resp.text[:300])
except Exception as e:
    print("Connection failed:", repr(e))
