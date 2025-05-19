import requests
import os
from datetime import datetime


price_cache = {}
AERODOME_API_KEY = os.getenv("AERODOME_API_KEY")
AERODROME_SUBGRAPH_URL = f"https://gateway.thegraph.com/api/{AERODOME_API_KEY}/subgraphs/id/GENunSHWLBXm59mBSgPzQ8metBEp9YDfdqwFr91Av1UM"
ETH_ADDRESS = "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"

def get_token_price_at(timestamp_unix, token_address):
    token_address = token_address.lower()

    # Normalize ETH to WETH on Base
    if token_address == ETH_ADDRESS:
        token_address = "0x4200000000000000000000000000000000000006"

    # Align to start of day (UTC)
    day_start = (timestamp_unix // 86400) * 86400
    cache_key = (token_address, day_start)

    if cache_key in price_cache:
        return price_cache[cache_key]

    # GraphQL query to fetch price from subgraph
    query = """
    query($token: String!, $dayStart: Int!) {
      tokenDayDatas(
        where: { token: $token, date: $dayStart }
      ) {
        priceUSD
      }
    }
    """

    variables = {
        "token": token_address,
        "dayStart": day_start
    }

    try:
        response = requests.post(
            AERODROME_SUBGRAPH_URL,
            json={"query": query, "variables": variables},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()

        price_str = (
            result.get("data", {})
            .get("tokenDayDatas", [{}])[0]
            .get("priceUSD")
        )

        price = float(price_str) if price_str else 0.0

    except Exception as e:
        print(f"[ERROR] Price fetch failed for {token_address} on {day_start}: {e}")
        price = 0.0

    price_cache[cache_key] = price
    return price

price = get_token_price_at(datetime.now().timestamp(), "0x524efe594a74204d91b27c1177f09166da96d32bbf673a874538c05a77b001f3" )
print(price)