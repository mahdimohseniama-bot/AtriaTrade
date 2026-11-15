import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WallexPublicProbe")

def test_wallex_public_endpoints():
    url = "https://api.wallex.ir/v1/markets"
    logger.info("Connecting to Wallex public markets endpoint...")
    try:
        response = requests.get(url, timeout=5)
        logger.info(f"Status Code: {response.status_code}")
        data = response.json()
        if response.status_code == 200 and "result" in data:
            logger.info("Successfully fetched public markets from Wallex!")
            symbols = list(data["result"].get("symbols", {}).keys())[:5]
            logger.info(f"Sample symbols available: {symbols}")
            return True
        else:
            logger.error(f"Unexpected response structure: {data}")
            return False
    except Exception as e:
        logger.error(f"Failed to connect to Wallex public endpoint: {e}")
        return False

if __name__ == "__main__":
    success = test_wallex_public_endpoints()
    assert success, "Wallex public endpoints probe failed!"
    print("WALLEX_PUBLIC_PROBE_PASSED")
