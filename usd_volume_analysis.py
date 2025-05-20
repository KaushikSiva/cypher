from collections import defaultdict
from datetime import datetime, timedelta, date, timezone
import aerodrome as aerodrome
import alchemy
import os
import supabase_client  # pip install python-dateutil

MASTER_WALLET = os.getenv("MASTER_WALLET").lower()
ETH_ADDRESS = os.getenv("ETH_ADDRESS")

SECONDS_IN_DAY = 86400

STABLECOINS = {
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": 1.0,  # USDC (Base)
    "0xaaa62d791835a98c35f8df62b708f68ccd398f11": 1.0,  # USDT (Base)
    "0x50c5725949a6f0c72e6c4a641f24049a917db0cb": 1.0,  # DAI (Base)
    "0x417ac0e078398c154edfadd9ef675d30be60af93": 1.0,  # crvUSD (Base)
}

def get_week_start(dt):
    """Return the timestamp for Monday midnight UTC of the week for dt."""
    monday = dt - timedelta(days=dt.weekday())
    monday_midnight = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(monday_midnight.timestamp())

def parse_transfer_timestamp(tx):
    from dateutil import parser

    ts = tx.get("metadata", {}).get("blockTimestamp")
    if ts:
        try:
            dt = parser.isoparse(ts)
            ts_unix = int(dt.timestamp())
            return dt, ts_unix
        except Exception as e:
            print(f"Failed to parse ISO timestamp '{ts}': {e}")
            return None, None
    else:
        block_num_hex = tx.get("blockNum")
        if block_num_hex:
            ts_unix = alchemy.get_block_timestamp_from_alchemy(block_num_hex)
            if ts_unix is not None:
                dt = datetime.fromtimestamp(ts_unix)
                return dt, ts_unix
            else:
                print("No block timestamp from alchemy for blockNum:", block_num_hex)
        else:
            print("No timestamp or blockNum in transfer")
        return None, None

def get_token_price(token_address, ts_unix):
    token_address = token_address.lower()
    if token_address in STABLECOINS:
        return STABLECOINS[token_address]
    else:
        return aerodrome.get_token_price_at(ts_unix, token_address, 150)

def process_transfer(tx, index, daily_volume, weekly_volume, monthly_volume, start_ts, end_ts):
    dt, ts_unix = parse_transfer_timestamp(tx)
    if dt is None or ts_unix is None:
        print(f"Transfer {index}: Missing or invalid timestamp, skipping.")
        return True  # continue processing

    if not start_ts <= ts_unix < end_ts:
        print(f"Transfer {index}: Date {dt.date()} outside target range, stopping.")
        return False  # signal to stop further processing

    token_address = tx.get("rawContract", {}).get("address")
    if tx.get("asset") == "ETH":
        token_address = ETH_ADDRESS
    if not token_address:
        print(f"Transfer {index}: Missing token address, skipping.")
        return True  # continue processing

    token_address = token_address.lower()
    value_raw = tx.get("value")
    if not value_raw:
        print(f"Transfer {index}: Missing value, skipping.")
        return True  # continue processing

    try:
        value = float(value_raw)
    except Exception as e:
        print(f"Transfer {index}: Invalid value '{value_raw}', skipping. Error: {e}")
        return True  # continue processing

    if value == 0:
        print(f"Transfer {index}: Value zero, skipping.")
        return True  # continue processing

    decimals = alchemy.get_token_decimals(token_address)  # preserved call, though unused here

    price = get_token_price(token_address, ts_unix)
    print(f"Transfer {index}: Token {token_address} on {dt.date()} price = {price}")

    if price == 0:
        print(f"Transfer {index}: Price zero, skipping.")
        return True  # continue processing

    usd_value = value * price

    # Calculate start timestamps for daily, weekly, monthly buckets
    day_start = ts_unix - (ts_unix % SECONDS_IN_DAY)
    week_start = get_week_start(dt)
    month_start = int(datetime(dt.year, dt.month, 1, tzinfo=dt.tzinfo).timestamp())

    daily_volume[day_start] += usd_value
    weekly_volume[week_start] += usd_value
    monthly_volume[month_start] += usd_value

    print(f"Transfer {index}: Added USD {usd_value} to daily volume on {dt.date()}.")
    return True  # processed successfully

def aggregate_usd_volume_backfill(transfers, start_ts, end_ts):
    daily_volume = defaultdict(float)
    weekly_volume = defaultdict(float)
    monthly_volume = defaultdict(float)

    print(f"Backfilling volume for transfers between {datetime.fromtimestamp(start_ts, tz=timezone.utc).date()} and {datetime.fromtimestamp(end_ts, tz=timezone.utc).date()}")

    def date_check(ts_unix):
        return start_ts <= ts_unix < end_ts

    for i, tx in enumerate(transfers, 1):
        should_continue = process_transfer(tx, i, daily_volume, weekly_volume, monthly_volume, start_ts, end_ts)
        if not should_continue:
            print(f"Stopping at transfer {i} due to date out of range.")
            break

    print("\nSample Daily USD Volume:")
    for day_start, vol in sorted(daily_volume.items())[:10]:
        print(datetime.fromtimestamp(day_start, tz=timezone.utc).strftime("%Y-%m-%d"), f"${vol:.2f}")

    return daily_volume, weekly_volume, monthly_volume

def aggregate_usd_volume_single_day(transfers, target_date):
    """
    target_date: datetime.date instance representing the single day to aggregate
    """
    daily_volume = defaultdict(float)
    weekly_volume = defaultdict(float)
    monthly_volume = defaultdict(float)

    print(f"Aggregating volume for single day: {target_date}")

    # Calculate start and end timestamps for the day
    start_dt = datetime(target_date.year, target_date.month, target_date.day)
    start_ts = int(start_dt.timestamp())
    end_ts = start_ts + SECONDS_IN_DAY

    for i, tx in enumerate(transfers, 1):
        should_continue = process_transfer(tx, i, daily_volume, weekly_volume, monthly_volume, start_ts, end_ts)
        if not should_continue:
            print(f"Stopping at transfer {i} due to date out of range.")
            break

    print("\nDaily USD Volume for", target_date)
    for day_start, vol in sorted(daily_volume.items()):
        print(datetime.fromtimestamp(day_start, timezone.utc).strftime("%Y-%m-%d"), f"${vol:.2f}")

    return daily_volume, weekly_volume, monthly_volume


def run_backfill():
    transfers = alchemy.fetch_all_incoming_transfers(MASTER_WALLET)

    start_2025 = int(datetime(2025, 1, 1).timestamp())
    end_2025 = int(datetime(2026, 1, 1).timestamp())
    daily_volume, weekly_volume, monthly_volume = aggregate_usd_volume_backfill(transfers, start_2025, end_2025)

    print("Reached here after backfill")

    supabase_client.save_volume_to_db(daily_volume, weekly_volume, monthly_volume)

def run_single_day(target_day=None):
    transfers = alchemy.fetch_all_incoming_transfers(MASTER_WALLET)

    if target_day is None:
        target_day = date.today()  # Default to today if no date given

    daily_volume, weekly_volume, monthly_volume = aggregate_usd_volume_single_day(transfers, target_day)

    supabase_client.save_volume_to_db(daily_volume, weekly_volume, monthly_volume)


if __name__ == "__main__":
    run_single_day()
