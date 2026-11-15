import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WallexDepthProbe")

def fetch_wallex_depth(symbol="USDTTMN"):
    url = "https://api.wallex.ir/v1/depth"
    params = {"symbol": symbol}
    logger.info(f"Fetching depth for symbol: {symbol} from {url}")
    try:
        response = requests.get(url, params=params, timeout=5)
        logger.info(f"Response Status Code: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"HTTP error {response.status_code}: {response.text}")
            return None
        data = response.json()
        result = data.get("result", {})
        
        # Wallex depth returns 'bid' and 'ask' directly inside result (or sometimes 'bids'/'asks')
        bids = result.get("bid", result.get("bids", []))
        asks = result.get("ask", result.get("asks", []))
        
        if not bids or not asks:
            logger.error(f"Empty bids or asks received: {result}")
            return None
            
        top_bid = float(bids[0][0] if isinstance(bids[0], list) else bids[0].get("price", 0))
        top_ask = float(asks[0][0] if isinstance(asks[0], list) else asks[0].get("price", 0))
        
        logger.info(f"Depth verified successfully! Top Bid: {top_bid}, Top Ask: {top_ask}")
        return {"bid": top_bid, "ask": top_ask, "bid_len": len(bids), "ask_len": len(asks)}
    except Exception as e:
        logger.error(f"Depth fetch error: {e}")
        return None

if __name__ == "__main__":
    res = fetch_wallex_depth("USDTTMN")
    assert res is not None, "Wallex depth verification failed!"
    assert res["bid"] > 0 and res["ask"] > 0, "Invalid market prices!"
    print("WALLEX_DEPTH_PROBE_PASSED")
