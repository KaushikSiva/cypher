import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# Load constants from environment
COINGECKO_BASE_URL = os.getenv("COINGECKO_BASE_URL")
ETH_ADDRESS = os.getenv("ETH_ADDRESS")
WETH_ADDRESS = os.getenv("WETH_ADDRESS")
ETH_NORMALIZED_ADDRESS = os.getenv("ETH_NORMALIZED_ADDRESS")

SECONDS_IN_A_DAY = 86400
price_cache = {}


def get_current_token_usd_price(contract_address: str) -> float:
    url = f"{COINGECKO_BASE_URL}/simple/token_price/base"
    params = {
        "contract_addresses": contract_address,
        "vs_currencies": "usd"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        price = data.get(contract_address.lower(), {}).get("usd", 0)
        return float(price) if price else 0.0
    except Exception:
        return 0.0


def get_token_market_chart(token_address, days):
    url = f"{COINGECKO_BASE_URL}/coins/ethereum/contract/{token_address}/market_chart/"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily"
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def get_token_price_at(timestamp_unix, token_address):
    token_address = token_address.lower()
    day_start = int(timestamp_unix // SECONDS_IN_A_DAY * SECONDS_IN_A_DAY)
    now_day_start = int(datetime.now(timezone.utc).timestamp() // SECONDS_IN_A_DAY * SECONDS_IN_A_DAY)

    if token_address in {ETH_ADDRESS, WETH_ADDRESS}:
        token_address = ETH_NORMALIZED_ADDRESS
    else:
        return get_current_token_usd_price(token_address)

    cache_key = (token_address, day_start)

    if cache_key in price_cache:
        print(f"[CACHE HIT] {cache_key}")
        return price_cache[cache_key]

    for delta in [0, -SECONDS_IN_A_DAY, SECONDS_IN_A_DAY]:
        candidate_key = (token_address, day_start + delta)
        if candidate_key in price_cache:
            print(f"Using price from day offset {delta // SECONDS_IN_A_DAY} for requested day")
            return price_cache[candidate_key]

    try:
        days = 90 if day_start < now_day_start else 1
        data = get_token_market_chart(token_address, days)

        if "prices" in data:
            for ts_ms, price in data["prices"]:
                day_ts = int((ts_ms // 1000) // SECONDS_IN_A_DAY * SECONDS_IN_A_DAY)
                price_cache[(token_address, day_ts)] = price

        for delta in [0, -SECONDS_IN_A_DAY, SECONDS_IN_A_DAY]:
            candidate_key = (token_address, day_start + delta)
            if candidate_key in price_cache:
                if delta != 0:
                    print(f"Using price from day offset {delta // SECONDS_IN_A_DAY} for requested day")
                return price_cache[candidate_key]

        return 0.0

    except Exception as e:
        print(f"[ERROR] Coingecko price fetch failed: {e}")
        price_cache[cache_key] = 0.0
        return 0.0


def get_price_days_ago(days_ago, token_address):
    now_ts = datetime.now(timezone.utc).timestamp()
    target_ts = now_ts - (days_ago * SECONDS_IN_A_DAY)
    return get_token_price_at(target_ts, token_address)
