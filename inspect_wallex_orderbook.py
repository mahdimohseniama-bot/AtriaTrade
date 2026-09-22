import json
from datetime import datetime

import requests


BASE_URL = "https://api.wallex.ir"
SYMBOLS = ("BTCUSDT", "ETHUSDT")
DEPTH_LEVELS = 5
TIMEOUT = 10


def extract_side(result, singular, plural):
    side = result.get(singular)
    if side is None:
        side = result.get(plural)
    return side or []


def parse_level(level):
    if isinstance(level, dict):
        price = level.get("price", level.get("rate"))
        quantity = level.get(
            "quantity",
            level.get(
                "amount",
                level.get("volume"),
            ),
        )
    elif isinstance(level, (list, tuple)) and len(level) >= 2:
        price, quantity = level[0], level[1]
    else:
        raise ValueError(f"Unsupported order-book level: {level!r}")

    if price is None or quantity is None:
        raise ValueError(f"Missing price/quantity in level: {level!r}")

    price = float(price)
    quantity = float(quantity)

    if price <= 0 or quantity < 0:
        raise ValueError(
            f"Invalid price/quantity: price={price}, quantity={quantity}"
        )

    return price, quantity


def inspect_symbol(symbol):
    url = f"{BASE_URL}/v1/depth"
    response = requests.get(
        url,
        params={"symbol": symbol},
        timeout=TIMEOUT,
    )

    print("\n" + "=" * 72)
    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] "
        f"{symbol} | HTTP {response.status_code}"
    )
    print(f"URL: {response.url}")

    response.raise_for_status()
    payload = response.json()

    result = payload.get("result", payload)
    if not isinstance(result, dict):
        raise TypeError(
            f"Expected result to be dict, got {type(result).__name__}"
        )

    print(f"Top-level keys: {list(payload.keys())}")
    print(f"Result keys: {list(result.keys())}")

    bids = extract_side(result, "bid", "bids")
    asks = extract_side(result, "ask", "asks")

    print(f"Bid levels: {len(bids)}")
    print(f"Ask levels: {len(asks)}")

    print("\nRaw first 2 bid levels:")
    print(json.dumps(bids[:2], ensure_ascii=False, indent=2))

    print("\nRaw first 2 ask levels:")
    print(json.dumps(asks[:2], ensure_ascii=False, indent=2))

    if not bids or not asks:
        raise ValueError("Order book has an empty bid or ask side")

    parsed_bids = [parse_level(level) for level in bids[:DEPTH_LEVELS]]
    parsed_asks = [parse_level(level) for level in asks[:DEPTH_LEVELS]]

    best_bid = parsed_bids[0][0]
    best_ask = parsed_asks[0][0]

    bid_qty = sum(quantity for _, quantity in parsed_bids)
    ask_qty = sum(quantity for _, quantity in parsed_asks)

    spread = best_ask - best_bid
    mid = (best_bid + best_ask) / 2
    spread_ratio = spread / mid if mid > 0 else float("inf")

    bid_ask_ratio = bid_qty / ask_qty if ask_qty > 0 else float("inf")
    normalized_imbalance = (
        (bid_qty - ask_qty) / (bid_qty + ask_qty)
        if bid_qty + ask_qty > 0
        else 0.0
    )
    bid_share = (
        bid_qty / (bid_qty + ask_qty)
        if bid_qty + ask_qty > 0
        else 0.0
    )

    print("\nParsed first 5 bids:")
    for index, (price, quantity) in enumerate(parsed_bids, start=1):
        print(f"  B{index}: price={price} quantity={quantity}")

    print("\nParsed first 5 asks:")
    for index, (price, quantity) in enumerate(parsed_asks, start=1):
        print(f"  A{index}: price={price} quantity={quantity}")

    print("\nCalculated metrics:")
    print(f"  best_bid              = {best_bid}")
    print(f"  best_ask              = {best_ask}")
    print(f"  spread_absolute       = {spread:.8f}")
    print(f"  spread_percent        = {spread_ratio * 100:.5f}%")
    print(f"  bid_quantity_sum      = {bid_qty:.12f}")
    print(f"  ask_quantity_sum      = {ask_qty:.12f}")
    print(f"  bid_ask_ratio         = {bid_ask_ratio:.6f}")
    print(f"  normalized_imbalance  = {normalized_imbalance:.6f}")
    print(f"  bid_share_percent     = {bid_share * 100:.3f}%")


def main():
    print("Wallex order-book structure inspector")
    print("Direct connection mode: no VPN")

    for symbol in SYMBOLS:
        try:
            inspect_symbol(symbol)
        except requests.RequestException as exc:
            print(
                f"\nNETWORK ERROR | {symbol} | "
                f"{type(exc).__name__}: {exc}"
            )
        except (ValueError, TypeError, KeyError, IndexError) as exc:
            print(
                f"\nDATA ERROR | {symbol} | "
                f"{type(exc).__name__}: {exc}"
            )
        except Exception as exc:
            print(
                f"\nUNEXPECTED ERROR | {symbol} | "
                f"{type(exc).__name__}: {exc}"
            )


if __name__ == "__main__":
    main()
