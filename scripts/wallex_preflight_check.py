import os
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("WALLEX_API_KEY", "")
BASE_URL = os.getenv("WALLEX_BASE_URL", "https://api.wallex.ir")

print("[PREFLIGHT] Starting Wallex Live Preflight Check...")
print(f"[PREFLIGHT] Base URL: {BASE_URL}")

# Check 1: DNS & Public Endpoint Latency (Orderbook / Ticker)
print("\n[CHECK 1/3] Testing Wallex API Connectivity & Latency...")
start_time = time.time()
try:
    resp = requests.get(f"{BASE_URL}/v1/markets", timeout=10)
    latency_ms = (time.time() - start_time) * 1000
    if resp.status_code == 200:
        data = resp.json()
        total_markets = len(data.get("result", {}).get("symbols", {}))
        print(f"  [PASS] Network OK! Latency: {latency_ms:.1f} ms")
        print(f"  [INFO] Active Markets Found: {total_markets}")
    else:
        print(f"  [FAIL] HTTP Status: {resp.status_code}")
except requests.exceptions.RequestException as e:
    print(f"  [CRITICAL] Network Connection Failed: {e}")
    sys.exit(1)

# Check 2: API Key Configuration
print("\n[CHECK 2/3] Checking API Key Configuration...")
if not API_KEY or API_KEY == "your_wallex_api_key_here":
    print("  [WARN] WALLEX_API_KEY is not configured in .env file.")
    print("  [INFO] Market data fetch is functional. Private balance/orders require API key.")
else:
    masked_key = API_KEY[:4] + "..." + API_KEY[-4:] if len(API_KEY) > 8 else "***"
    print(f"  [PASS] API Key detected: {masked_key}")

# Check 3: Private Account Balance Verification (If Key Exists)
print("\n[CHECK 3/3] Testing Account Access & Permissions...")
if API_KEY and API_KEY != "your_wallex_api_key_here":
    headers = {"X-API-Key": API_KEY}
    try:
        acc_resp = requests.get(f"{BASE_URL}/v1/account/balances", headers=headers, timeout=10)
        if acc_resp.status_code == 200:
            bal_data = acc_resp.json()
            print("  [PASS] Authentication successful! Account balances accessible.")
        elif acc_resp.status_code in [401, 403]:
            print(f"  [FAIL] Authentication failed (HTTP {acc_resp.status_code}). Verify your WALLEX_API_KEY.")
        else:
            print(f"  [WARN] Unexpected response: HTTP {acc_resp.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"  [CRITICAL] Account API request failed: {e}")
else:
    print("  [SKIP] Skipping balance check (No API Key).")

print("\n[PREFLIGHT] Diagnostic complete.\n")
