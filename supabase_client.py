from supabase import create_client, Client
import os
import datetime
from dotenv import load_dotenv

load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
 # Use service_role key for write access
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_usd_volume_date():
    response = supabase.table("usd_volume").select("*").execute()
    data = response.data

    # Convert date unix timestamp to YYYY-MM-DD string
    formatted_data = []
    for row in data:
        dt_str = datetime.datetime.utcfromtimestamp(row["date"]).strftime("%Y-%m-%d")
        formatted_data.append({
            "date": dt_str,
            "daily": float(row.get("daily") or 0),
            "weekly": float(row.get("weekly") or 0),
            "monthly": float(row.get("monthly") or 0),
        })

    # Sort by date ascending
    formatted_data.sort(key=lambda x: x["date"])
    return formatted_data

def save_volume_to_db(daily, weekly, monthly):
    # Combine all dates
    all_dates = set(daily) | set(weekly) | set(monthly)

    # Delete all previous rows (optional, if you want to clear old data)
    #supabase.table("usd_volume").delete().neq("date", 0).execute()

    # Insert each row
    rows = []
    for date in sorted(all_dates):
        rows.append({
            "date": date,
            "daily": daily.get(date, 0),
            "weekly": weekly.get(date, 0),
            "monthly": monthly.get(date, 0)
        })

    # Supabase allows bulk insert
    if rows:
        response = supabase.table("usd_volume").insert(rows).execute()
        if not response.data:
            print("Error inserting to Supabase:", response)
        else:
            print(f"Inserted {len(rows)} rows into Supabase.")
