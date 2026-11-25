"""
AP Mandi Predict — Arrivals Service
Fetches daily arrival and price data from data.gov.in OGD API.
Aggregates to state-level totals for Andhra Pradesh.
"""

import os
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger(__name__)

# Config from .env
API_KEY = os.getenv("OGD_API_KEY")
RESOURCE_ID = os.getenv("OGD_RESOURCE_ID")
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

# Output path
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'daily_data')
ARRIVALS_FILE = os.path.join(DATA_DIR, 'arrivals.csv')


_is_offline = False


def _fetch_page(date_str: str, offset: int = 0, limit: int = 1000) -> list:
    """
    Fetch a single page of records from OGD API.
    date_str: format "dd/mm/yyyy"
    Returns list of record dicts.
    """
    global _is_offline
    if _is_offline:
        return []

    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": limit,
        "offset": offset,
        "filters[state]": "Andhra Pradesh",
    }
    if date_str:
        params["filters[arrival_date]"] = date_str

    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("records", [])
    except requests.RequestException as e:
        logger.error(f"OGD API request failed: {e}")
        if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
            logger.warning("Connection/Timeout error detected. Setting arrivals_service to offline mode.")
            _is_offline = True
        return []


def fetch_arrivals(target_date: datetime = None) -> pd.DataFrame:
    """
    Fetch all AP arrival records for a given date from OGD API.
    Paginates automatically. Returns raw DataFrame.
    
    Args:
        target_date: The date to fetch arrivals for. Defaults to today.
    
    Returns:
        DataFrame with columns: date, market, commodity, arrivals_in_qtl,
                                 min_price, max_price, modal_price
    """
    if target_date is None:
        target_date = datetime.now()

    date_str = target_date.strftime("%d/%m/%Y")
    logger.info(f"Fetching AP arrivals for {date_str}...")

    all_records = []
    offset = 0
    limit = 1000

    while True:
        records = _fetch_page(date_str, offset, limit)
        if not records:
            break
        all_records.extend(records)
        offset += limit
        if len(records) < limit:
            break

    if not all_records:
        logger.warning(f"No arrival data found for {date_str}")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)
    logger.info(f"Fetched {len(df)} AP records for {date_str}")

    # Standardize columns
    col_map = {
        "market": "mandi",
        "arrival_date": "date",
    }
    df.rename(columns=col_map, inplace=True)

    # Parse numeric fields
    for col in ['min_price', 'max_price', 'modal_price']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Parse arrivals — use 'arrivals_in_qtl' if available
    arrival_col = None
    for candidate in ['arrivals_in_qtl', 'arrivals', 'arrival']:
        if candidate in df.columns:
            arrival_col = candidate
            break

    if arrival_col:
        df['arrivals_in_qtl'] = pd.to_numeric(df[arrival_col], errors='coerce').fillna(0)
    else:
        df['arrivals_in_qtl'] = 0
        logger.warning("No arrivals column found in API response; defaulting to 0")

    # Normalize date
    df['date'] = target_date.strftime("%Y-%m-%d")

    return df


def aggregate_state_arrivals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate mandi-level data to state-level daily totals.
    
    Returns:
        DataFrame with columns: date, total_arrival_state, avg_modal_price_state
    """
    if df.empty:
        return pd.DataFrame(columns=['date', 'total_arrival_state', 'avg_modal_price_state'])

    agg = df.groupby('date').agg(
        total_arrival_state=('arrivals_in_qtl', 'sum'),
        avg_modal_price_state=('modal_price', 'mean')
    ).reset_index()

    agg['total_arrival_state'] = agg['total_arrival_state'].round(2)
    agg['avg_modal_price_state'] = agg['avg_modal_price_state'].round(2)

    return agg


def save_arrivals(agg_df: pd.DataFrame) -> str:
    """
    Append aggregated arrivals to CSV, avoiding duplicates.
    Returns the path to the saved file.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    if agg_df.empty:
        logger.warning("No arrival data to save.")
        return ARRIVALS_FILE

    if os.path.exists(ARRIVALS_FILE):
        existing = pd.read_csv(ARRIVALS_FILE)
        combined = pd.concat([existing, agg_df], ignore_index=True)
        combined.drop_duplicates(subset=['date'], keep='last', inplace=True)
    else:
        combined = agg_df

    combined.sort_values('date', inplace=True)
    combined.to_csv(ARRIVALS_FILE, index=False)
    logger.info(f"Saved arrivals data to {ARRIVALS_FILE} ({len(combined)} rows)")
    return ARRIVALS_FILE


def update_arrivals(target_date: datetime = None) -> pd.DataFrame:
    """
    Full pipeline: fetch → aggregate → save.
    Returns the aggregated DataFrame.
    """
    raw = fetch_arrivals(target_date)
    agg = aggregate_state_arrivals(raw)
    save_arrivals(agg)
    return agg


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = update_arrivals()
    print(result)
