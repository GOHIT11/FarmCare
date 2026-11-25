"""
fetch_all_ap_crops.py
Fetches historical price data for ALL Andhra Pradesh commodities from AGMARKNET
and appends to mandi_data.csv for model training.

Usage:  python fetch_all_ap_crops.py
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import random
from datetime import datetime, timedelta

DATA_FILE = os.path.join(os.path.dirname(__file__), "mandi_data.csv")

# ─────────────────────────────────────────────
# ALL COMMODITIES CONFIRMED ON AGMARKNET FOR AP
# (from screenshots + user confirmation)
# ─────────────────────────────────────────────
ALL_AP_COMMODITIES = [
    "Arhar(Tur/Red Gram)(Whole)",
    "Bajra(Pearl Millet/Cumbu)",
    "Barley(Jau)",
    "Bengal Gram(Gram)(Whole)",
    "Black Gram(Urd Beans)(Whole)",
    "Copra",
    "Cotton",
    "Green Gram(Moong)(Whole)",
    "Groundnut",
    "Jowar(Sorghum)",
    "Jute",
    "Lentil(Masur)(Whole)",
    "Maize",
    "Mustard",
    "Niger Seed(Ramtil)",
    "Onion",
    "Paddy(Common)",
    "Potato",
    "Ragi(Finger Millet)",
    "Safflower",
    "Sesamum(Sesame,Gingelly,Til)",
    "Soyabean",
    "Sugarcane",
    "Sunflower",
    "Sunflower Seed",
    "Tomato",
    "Rapeseed(Toria)",
    "Wheat",
    # Already in data but listing for completeness:
    "Banana",
    "Castor Seed",
    "Coconut",
    "Dry Chillies",
    "Red Chilli",
    "Chili Red",
    "Green Chilli",
    "Turmeric",
    "Tobacco",
    "Rice",
    "Mango",
    "Lemon",
    "Lime",
    "Jaggery",
    "Foxtail Millet(Navane)",
    "Brinjal",
    "Cauliflower",
    "Black Gram",
    "Bengal Gram",
    "Mousambi(Sweet Lime)",
    "Cluster beans",
    "Ridgeguard(Tori)",
]

# AGMARKNET commodity name → numeric code mapping
# (These are the standard AGMARKNET commodity IDs)
COMMODITY_CODES = {
    "Arhar(Tur/Red Gram)(Whole)": "2",
    "Bajra(Pearl Millet/Cumbu)": "3",
    "Barley(Jau)": "4",
    "Bengal Gram(Gram)(Whole)": "7",
    "Black Gram(Urd Beans)(Whole)": "9",
    "Castor Seed": "14",
    "Copra": "16",
    "Cotton": "17",
    "Dry Chillies": "20",
    "Wheat": "1",
    "Rice": "3",  # may conflict - check
    "Green Gram(Moong)(Whole)": "25",
    "Groundnut": "26",
    "Jowar(Sorghum)": "30",
    "Jute": "31",
    "Lentil(Masur)(Whole)": "35",
    "Maize": "36",
    "Mustard": "41",
    "Niger Seed(Ramtil)": "44",
    "Onion": "23",
    "Paddy(Common)": "49",
    "Potato": "24",
    "Ragi(Finger Millet)": "53",
    "Safflower": "57",
    "Sesamum(Sesame,Gingelly,Til)": "58",
    "Soyabean": "65",
    "Sugarcane": "69",
    "Sunflower": "70",
    "Sunflower Seed": "70",
    "Tomato": "78",
    "Rapeseed(Toria)": "82",
    "Turmeric": "79",
    "Tobacco": "77",
    "Banana": "5",
    "Mango": "37",
    "Coconut": "15",
    "Green Chilli": "101",
    "Red Chilli": "53",  # approximate
    "Chili Red": "53",
    "Lemon": "34",
    "Lime": "34",
    "Jaggery": "29",
    "Foxtail Millet(Navane)": "21",
}

STATE_CODE = "AP"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


def fetch_agmarknet(commodity_name, date_from, date_to, retries=3):
    """Fetch price data for one commodity from AGMARKNET SearchCmmMkt."""
    commodity_code = COMMODITY_CODES.get(commodity_name, "0")
    if commodity_code == "0":
        print(f"  ⚠ No code for '{commodity_name}' — skipping")
        return pd.DataFrame()

    search_url = "https://agmarknet.gov.in/SearchCmmMkt.aspx"
    params = {
        "Tx_Commodity": commodity_code,
        "Tx_State": STATE_CODE,
        "Tx_District": "0",
        "Tx_Market": "0",
        "DateFrom": date_from,
        "DateTo": date_to,
        "Fr_Date": date_from,
        "To_Date": date_to,
        "Tx_Trend": "0",
        "Tx_CommodityHead": commodity_name,
        "Tx_StateHead": "Andhra Pradesh",
        "Tx_DistrictHead": "--Select--",
        "Tx_MarketHead": "--Select--",
    }

    for attempt in range(retries):
        try:
            session = requests.Session()
            session.headers.update(HEADERS)
            resp = session.get(search_url, params=params, timeout=30)

            if "No Data Found" in resp.text or resp.status_code != 200:
                return pd.DataFrame()

            tables = pd.read_html(resp.content)
            for tbl in tables:
                cols = " ".join(str(c).lower() for c in tbl.columns)
                if "price" in cols or "modal" in cols or "market" in cols:
                    return _clean_df(tbl, commodity_name)

            return pd.DataFrame()

        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  ✗ Error for '{commodity_name}': {e}")
                return pd.DataFrame()
    return pd.DataFrame()


def _clean_df(df, commodity_name):
    """Normalize AGMARKNET table columns."""
    try:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [" ".join(str(x) for x in c).strip() for c in df.columns]

        df.columns = [str(c).lower().replace(" ", "_").strip() for c in df.columns]

        rename = {}
        for col in df.columns:
            if "market" in col and "mandi" not in col:
                rename[col] = "mandi"
            elif "min" in col and "price" in col:
                rename[col] = "min_price"
            elif "max" in col and "price" in col:
                rename[col] = "max_price"
            elif "modal" in col:
                rename[col] = "modal_price"
            elif "date" in col:
                rename[col] = "date"
            elif "district" in col:
                rename[col] = "district"

        df.rename(columns=rename, inplace=True)

        # Add required columns
        df["state"] = "Andhra Pradesh"
        df["commodity"] = commodity_name
        df["arrivals"] = df.get("arrivals", 0)

        # Numeric conversions
        for col in ["modal_price", "min_price", "max_price"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df.dropna(subset=["modal_price"], inplace=True)

        # Parse date
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")

        final_cols = ["state", "mandi", "commodity", "date", "min_price", "max_price", "modal_price", "arrivals"]
        for col in final_cols:
            if col not in df.columns:
                df[col] = None

        return df[final_cols].dropna(subset=["mandi", "modal_price"])

    except Exception as e:
        print(f"    Clean error: {e}")
        return pd.DataFrame()


def date_range_chunks(start_date, end_date, chunk_days=90):
    """Split date range into chunks for pagination."""
    current = start_date
    while current < end_date:
        chunk_end = min(current + timedelta(days=chunk_days - 1), end_date)
        yield current.strftime("%d-%b-%Y"), chunk_end.strftime("%d-%b-%Y")
        current = chunk_end + timedelta(days=1)


def load_existing():
    """Load existing mandi_data.csv."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        return df
    return pd.DataFrame()


def fetch_all(years_back=3):
    """Main: fetch all AP crops for the given years and update CSV."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years_back)

    print(f"=== Fetching ALL AP Crops ===")
    print(f"Period: {start_date.date()} → {end_date.date()}")
    print(f"Total crops to fetch: {len(ALL_AP_COMMODITIES)}")
    print()

    df_existing = load_existing()
    all_new = []
    fetched_count = 0

    for commodity in ALL_AP_COMMODITIES:
        # Check if already have enough data
        if not df_existing.empty:
            existing_rows = df_existing[
                (df_existing["state"] == "Andhra Pradesh") &
                (df_existing["commodity"] == commodity)
            ]
            if len(existing_rows) > 200:
                print(f"  ✓ {commodity}: already has {len(existing_rows)} records, skipping")
                continue

        print(f"\n  Fetching: {commodity}")
        crop_dfs = []

        for date_from, date_to in date_range_chunks(start_date, end_date, chunk_days=90):
            df_chunk = fetch_agmarknet(commodity, date_from, date_to)
            if not df_chunk.empty:
                crop_dfs.append(df_chunk)
                print(f"    [{date_from} → {date_to}] {len(df_chunk)} rows")
            time.sleep(random.uniform(0.5, 1.5))  # Be polite to the server

        if crop_dfs:
            df_crop = pd.concat(crop_dfs, ignore_index=True)
            df_crop.drop_duplicates(subset=["mandi", "date"], inplace=True)
            all_new.append(df_crop)
            fetched_count += 1
            print(f"  → Total for '{commodity}': {len(df_crop)} rows")
        else:
            print(f"  ✗ No data fetched for '{commodity}'")

    if all_new:
        df_new = pd.concat(all_new, ignore_index=True)
        print(f"\n=== Fetched {len(df_new)} new rows across {fetched_count} crops ===")

        # Merge with existing
        if not df_existing.empty:
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new

        df_combined.drop_duplicates(subset=["state", "mandi", "commodity", "date"], keep="last", inplace=True)
        df_combined.to_csv(DATA_FILE, index=False)
        print(f"Saved. Total DB size: {len(df_combined)} rows")
    else:
        print("\n✗ No new data fetched.")

    return all_new


if __name__ == "__main__":
    fetch_all(years_back=3)
