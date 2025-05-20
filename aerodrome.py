import os
import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("THEGRAPH_API_KEY")
SUBGRAPH_ID = os.getenv("THEGRAPH_SUBGRAPH_ID")

SUBGRAPH_URL = f"https://gateway.thegraph.com/api/{API_KEY}/subgraphs/id/{SUBGRAPH_ID}"

# Cache priceUSD keyed by (token_address, day_timestamp)
token_day_price_cache = {}

def create_client():
    transport = RequestsHTTPTransport(url=SUBGRAPH_URL, verify=True, retries=3)
    return Client(transport=transport, fetch_schema_from_transport=True)

def normalize_token_address(token_address: str) -> str:
    if token_address.lower() == "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee":
        return "0x4200000000000000000000000000000000000006"
    return token_address.lower()


def build_latest_token_data_query():
    return gql("""
        query TokenHourDatas(
            $tokenId: String!,
            $first: Int = 1,
            $orderDirection: OrderDirection = desc
        ) {
          tokenHourDatas(
            first: $first,
            where: { token: $tokenId },
            orderBy: periodStartUnix,
            orderDirection: $orderDirection
          ) {
            periodStartUnix
            priceUSD
            volumeUSD
          }
        }
    """)



def build_token_day_data_query():
    return gql("""
        query TokenDayDatas(
            $tokenId: String!,
            $first: Int!,
            $orderBy: TokenDayData_orderBy!,
            $orderDirection: OrderDirection!
        ) {
          tokenDayDatas(
            first: $first,
            where: { token: $tokenId },
            orderBy: $orderBy,
            orderDirection: $orderDirection
          ) {
            date
            priceUSD
            volumeUSD
          }
        }
    """)

def fetch_token_day_data(token_address: str, days: int = 150):
    """
    Fetches the latest `days` tokenDayDatas from The Graph for `token_address`.
    Updates the token_day_price_cache with fetched prices keyed by (token, date).
    Returns the list of tokenDayDatas.
    """
    token_address = normalize_token_address(token_address)
    client = create_client()
    query = build_token_day_data_query()
    params = {
        "tokenId": token_address,
        "first": days,
        "orderBy": "date",
        "orderDirection": "asc"
    }
    try:
        result = client.execute(query, variable_values=params)
        day_datas = result["tokenDayDatas"]
        # Update individual day price cache
        for day_data in day_datas:
            day_ts = int(day_data['date'])
            price = float(day_data.get('priceUSD', 0))
            token_day_price_cache[(token_address, day_ts)] = price
        return day_datas
    except Exception as e:
        print(f"[ERROR] Failed to fetch token day data: {e}")
        return []

def get_token_price_at(ts_unix: int, token_address: str, lookback_days=150):
    """
    Returns priceUSD for the given token at the UTC day containing ts_unix.
    If the date is today, fetch latest price using tokenHourDatas.
    Checks cache first; if not found, fetches data and updates cache.
    """
    token_address = normalize_token_address(token_address)
    day_start = datetime.datetime.utcfromtimestamp(ts_unix).replace(hour=0, minute=0, second=0, microsecond=0)
    day_timestamp = int(day_start.timestamp())
    cache_key = (token_address, day_timestamp)

    # Return from cache if available
    if cache_key in token_day_price_cache:
        print("CACHE_HIT---")
        return token_day_price_cache[cache_key]

    # Check if it's today (UTC)
    now = datetime.datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if day_start == today_start:
        # Fetch latest hourly data for today
        client = create_client()
        query = build_latest_token_data_query()
        params = {"tokenId": token_address}
        result = client.execute(query, variable_values=params)
        items = result.get("tokenHourDatas", [])
        if items:
            latest = items[0]
            price = float(latest["priceUSD"])
            token_day_price_cache[cache_key] = price
            return price
        return 0.0
    
    today_timestamp = int(today_start.timestamp())
    today_key = (token_address, today_timestamp)
    
    if today_key in token_day_price_cache:
        return token_day_price_cache[today_key]
    # Not today → Fetch historic data and update cache
    fetch_token_day_data(token_address, days=lookback_days)
    return token_day_price_cache.get(cache_key, 0.0)



fetch_token_day_data("0x4200000000000000000000000000000000000006", 150)
fetch_token_day_data("0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", 150)