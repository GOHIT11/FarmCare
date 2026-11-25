"""
AP Mandi Predict — Feature Engineering Service
Merges price, arrival, weather, and calendar data into a single
ML-ready feature dataset for XGBoost training.
"""

import os
import logging
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger(__name__)

# Paths
BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BACKEND_DIR, 'daily_data')
MANDI_DATA_FILE = os.path.join(BACKEND_DIR, 'mandi_data.csv')

# Output files
PRICES_FILE = os.path.join(DATA_DIR, 'prices.csv')
ARRIVALS_FILE = os.path.join(DATA_DIR, 'arrivals.csv')
WEATHER_FILE = os.path.join(DATA_DIR, 'weather.csv')
CALENDAR_FILE = os.path.join(DATA_DIR, 'calendar_features.csv')
MERGED_FILE = os.path.join(DATA_DIR, 'merged_features.csv')


def generate_prices_csv() -> pd.DataFrame:
    """
    Read the main mandi_data.csv and generate a daily price summary
    per commodity per mandi. Saves to daily_data/prices.csv.
    
    Returns:
        DataFrame with columns: date, commodity, mandi, modal_price, min_price, max_price
    """
    if not os.path.exists(MANDI_DATA_FILE):
        logger.error(f"Price data file not found: {MANDI_DATA_FILE}")
        return pd.DataFrame()

    logger.info(f"Reading price data from {MANDI_DATA_FILE}...")
    df = pd.read_csv(MANDI_DATA_FILE)

    # Filter to AP only
    if 'state' in df.columns:
        df = df[df['state'] == 'Andhra Pradesh']

    # Standardize date
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df.dropna(subset=['date'], inplace=True)
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')

    # Numeric cleanup
    for col in ['modal_price', 'min_price', 'max_price']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df.dropna(subset=['modal_price'], inplace=True)

    # Keep essential columns
    keep_cols = ['date', 'commodity', 'mandi', 'modal_price', 'min_price', 'max_price']
    available = [c for c in keep_cols if c in df.columns]
    df = df[available].copy()

    # Deduplicate
    df.drop_duplicates(subset=['date', 'commodity', 'mandi'], keep='last', inplace=True)
    df.sort_values(['commodity', 'mandi', 'date'], inplace=True)

    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(PRICES_FILE, index=False)
    logger.info(f"Generated prices.csv with {len(df)} rows")
    return df


def merge_features() -> pd.DataFrame:
    """
    Merge all data sources into a single feature dataset.
    
    Pipeline:
        1. Load prices.csv (per commodity per mandi per day)
        2. Left-join arrivals.csv (state-level daily totals)
        3. Left-join weather.csv (daily weather)
        4. Left-join calendar_features.csv (festival/weekend flags)
        5. Create lag and rolling features per commodity+mandi group
        6. Save as merged_features.csv
    
    Returns:
        DataFrame with all features merged.
    """
    # 1. Load prices
    if not os.path.exists(PRICES_FILE):
        logger.warning("prices.csv not found. Generating from mandi_data.csv...")
        generate_prices_csv()

    if not os.path.exists(PRICES_FILE):
        logger.error("Cannot generate prices.csv. Aborting merge.")
        return pd.DataFrame()

    logger.info("Loading prices data...")
    prices = pd.read_csv(PRICES_FILE)
    prices['date'] = pd.to_datetime(prices['date']).dt.strftime('%Y-%m-%d')

    # 2. Left-join arrivals
    if os.path.exists(ARRIVALS_FILE):
        logger.info("Joining arrivals data...")
        arrivals = pd.read_csv(ARRIVALS_FILE)
        arrivals['date'] = pd.to_datetime(arrivals['date']).dt.strftime('%Y-%m-%d')
        prices = prices.merge(arrivals, on='date', how='left')
    else:
        logger.warning("arrivals.csv not found. Skipping arrivals join.")
        prices['total_arrival_state'] = 0.0
        prices['avg_modal_price_state'] = 0.0

    # 3. Left-join weather
    if os.path.exists(WEATHER_FILE):
        logger.info("Joining weather data...")
        weather = pd.read_csv(WEATHER_FILE)
        weather['date'] = pd.to_datetime(weather['date']).dt.strftime('%Y-%m-%d')
        prices = prices.merge(weather, on='date', how='left')
    else:
        logger.warning("weather.csv not found. Skipping weather join.")
        prices['rainfall_flag'] = 0
        prices['temp_avg'] = 0.0

    # 4. Left-join calendar features
    if os.path.exists(CALENDAR_FILE):
        logger.info("Joining calendar features...")
        calendar = pd.read_csv(CALENDAR_FILE)
        calendar['date'] = pd.to_datetime(calendar['date']).dt.strftime('%Y-%m-%d')
        prices = prices.merge(calendar, on='date', how='left')
    else:
        logger.warning("calendar_features.csv not found. Skipping calendar join.")
        prices['is_weekend'] = 0
        prices['is_festival_week'] = 0
        prices['days_to_next_festival'] = 365

    # 5. Create lag and rolling features (per commodity + mandi group)
    logger.info("Creating lag & rolling features...")
    prices.sort_values(['commodity', 'mandi', 'date'], inplace=True)

    grouped = prices.groupby(['commodity', 'mandi'])

    # Yesterday's price
    prices['yesterday_price'] = grouped['modal_price'].shift(1)

    # Rolling averages
    prices['3_day_avg'] = grouped['modal_price'].transform(
        lambda x: x.rolling(window=3, min_periods=1).mean()
    )
    prices['7_day_avg'] = grouped['modal_price'].transform(
        lambda x: x.rolling(window=7, min_periods=1).mean()
    )

    # 7-day arrival average
    prices['7_day_arrival_avg'] = grouped['total_arrival_state'].transform(
        lambda x: x.rolling(window=7, min_periods=1).mean()
    )

    # Price momentum (today - yesterday)
    prices['price_momentum'] = prices['modal_price'] - prices['yesterday_price']

    # Festival flag (alias for is_festival_week)
    if 'is_festival_week' in prices.columns:
        prices['festival_flag'] = prices['is_festival_week'].fillna(0).astype(int)
    else:
        prices['festival_flag'] = 0

    # Fill NaNs in key feature columns with sensible defaults
    fill_defaults = {
        'total_arrival_state': 0.0,
        'avg_modal_price_state': 0.0,
        'rainfall_flag': 0,
        'temp_avg': 0.0,
        'temperature_2m_max': 0.0,
        'temperature_2m_min': 0.0,
        'precipitation_sum': 0.0,
        'windspeed_10m_max': 0.0,
        'is_weekend': 0,
        'is_festival_week': 0,
        'days_to_next_festival': 365,
        'festival_flag': 0,
    }
    for col, default in fill_defaults.items():
        if col in prices.columns:
            prices[col] = prices[col].fillna(default)

    # Round all float columns
    float_cols = prices.select_dtypes(include=['float64']).columns
    prices[float_cols] = prices[float_cols].round(2)

    # 6. Save
    os.makedirs(DATA_DIR, exist_ok=True)
    prices.to_csv(MERGED_FILE, index=False)
    logger.info(f"Saved merged features to {MERGED_FILE} ({len(prices)} rows, {len(prices.columns)} columns)")
    logger.info(f"Columns: {list(prices.columns)}")

    return prices


def backfill_historical_data():
    """
    Backfill weather and calendar data for all historical dates in prices.csv.
    Call this once to populate weather.csv and calendar_features.csv
    for the full price history. Subsequent runs via update_daily_data()
    will only append new dates.
    
    This function is idempotent — it skips dates already in the CSV files.
    """
    if not os.path.exists(PRICES_FILE):
        generate_prices_csv()

    if not os.path.exists(PRICES_FILE):
        logger.error("No prices.csv to backfill from.")
        return

    prices = pd.read_csv(PRICES_FILE)
    all_dates = pd.to_datetime(prices['date']).dt.date.unique()
    all_dates = sorted(all_dates)

    if len(all_dates) == 0:
        logger.warning("No dates found in prices.csv")
        return

    min_date = all_dates[0]
    max_date = all_dates[-1]
    logger.info(f"Backfill range: {min_date} to {max_date} ({len(all_dates)} unique dates)")

    # --- Backfill Weather ---
    logger.info("Backfilling weather data...")
    existing_weather_dates = set()
    if os.path.exists(WEATHER_FILE):
        existing_w = pd.read_csv(WEATHER_FILE)
        existing_weather_dates = set(existing_w['date'].tolist())

    try:
        from services.weather_service import fetch_weather_range, save_weather

        # Open-Meteo archive API supports date ranges, process in 30-day chunks
        chunk_size = timedelta(days=30)
        current = datetime.combine(min_date, datetime.min.time())
        end = datetime.combine(max_date, datetime.min.time())

        all_weather_frames = []
        while current <= end:
            chunk_end = min(current + chunk_size, end)
            # Check if we already have all dates in this chunk
            chunk_dates = set()
            d = current.date()
            while d <= chunk_end.date():
                chunk_dates.add(d.strftime("%Y-%m-%d"))
                d += timedelta(days=1)

            missing = chunk_dates - existing_weather_dates
            if not missing:
                current = chunk_end + timedelta(days=1)
                continue

            try:
                weather_df = fetch_weather_range(current, chunk_end)
                if not weather_df.empty:
                    all_weather_frames.append(weather_df)
                    logger.info(f"  Weather {current.date()} to {chunk_end.date()}: {len(weather_df)} rows")
            except Exception as e:
                logger.warning(f"  Weather chunk {current.date()} failed: {e}")

            current = chunk_end + timedelta(days=1)
            # Be polite to the API
            import time
            time.sleep(0.5)

        if all_weather_frames:
            combined_weather = pd.concat(all_weather_frames, ignore_index=True)
            save_weather(combined_weather)
            logger.info(f"Weather backfill complete: {len(combined_weather)} new rows")
        else:
            logger.info("Weather backfill: no new data needed")

    except Exception as e:
        logger.error(f"Weather backfill failed: {e}")

    # --- Backfill Calendar ---
    logger.info("Backfilling calendar data...")
    try:
        from services.calendar_service import get_calendar_features_range, save_calendar_features

        existing_calendar_dates = set()
        if os.path.exists(CALENDAR_FILE):
            existing_c = pd.read_csv(CALENDAR_FILE)
            existing_calendar_dates = set(existing_c['date'].tolist())

        # Generate features for all dates at once
        start_dt = datetime.combine(min_date, datetime.min.time())
        end_dt = datetime.combine(max_date, datetime.min.time())

        calendar_df = get_calendar_features_range(start_dt, end_dt)

        if not calendar_df.empty:
            # Filter to only new dates
            new_rows = calendar_df[~calendar_df['date'].isin(existing_calendar_dates)]
            if not new_rows.empty:
                save_calendar_features(new_rows)
                logger.info(f"Calendar backfill complete: {len(new_rows)} new rows")
            else:
                logger.info("Calendar backfill: no new data needed")

    except Exception as e:
        logger.error(f"Calendar backfill failed: {e}")

    logger.info("Historical backfill complete.")


def update_daily_data(target_date: datetime = None):
    """
    Main orchestrator: fetches all daily data sources and merges them.
    Call this function daily (via cron, scheduler, or /update_daily endpoint).
    
    On first run, also triggers historical backfill for weather and calendar.
    
    Args:
        target_date: Date to update. Defaults to today.
    
    Returns:
        dict with status and counts.
    """
    if target_date is None:
        target_date = datetime.now()

    logger.info(f"=== Starting daily data update for {target_date.strftime('%Y-%m-%d')} ===")

    results = {
        "date": target_date.strftime("%Y-%m-%d"),
        "arrivals": {"status": "skipped", "rows": 0},
        "weather": {"status": "skipped", "rows": 0},
        "calendar": {"status": "skipped", "rows": 0},
        "backfill": {"status": "skipped"},
        "merged": {"status": "skipped", "rows": 0},
    }

    # 1. Generate prices.csv (only if it doesn't exist or is empty)
    if not os.path.exists(PRICES_FILE) or os.path.getsize(PRICES_FILE) < 100:
        try:
            generate_prices_csv()
        except Exception as e:
            logger.error(f"Price CSV generation failed: {e}")

    # 2. Check if backfill is needed (first run detection)
    needs_backfill = False
    if os.path.exists(WEATHER_FILE):
        w_df = pd.read_csv(WEATHER_FILE)
        if len(w_df) < 30:
            needs_backfill = True
    else:
        needs_backfill = True

    # 3. Arrivals
    try:
        from services.arrivals_service import update_arrivals
        arrivals_df = update_arrivals(target_date)
        results["arrivals"] = {"status": "success", "rows": len(arrivals_df)}
    except Exception as e:
        logger.error(f"Arrivals update failed: {e}")
        results["arrivals"] = {"status": "error", "error": str(e)}

    # 4. Weather (today)
    try:
        from services.weather_service import update_weather
        weather_df = update_weather(target_date)
        results["weather"] = {"status": "success", "rows": len(weather_df)}
    except Exception as e:
        logger.error(f"Weather update failed: {e}")
        results["weather"] = {"status": "error", "error": str(e)}

    # 5. Calendar (today)
    try:
        from services.calendar_service import update_calendar
        calendar_df = update_calendar(target_date)
        results["calendar"] = {"status": "success", "rows": len(calendar_df)}
    except Exception as e:
        logger.error(f"Calendar update failed: {e}")
        results["calendar"] = {"status": "error", "error": str(e)}

    # 6. Historical backfill (first run only)
    if needs_backfill:
        try:
            logger.info("First run detected — running historical backfill...")
            backfill_historical_data()
            results["backfill"] = {"status": "success"}
        except Exception as e:
            logger.error(f"Backfill failed: {e}")
            results["backfill"] = {"status": "error", "error": str(e)}

    # 7. Merge all features
    try:
        merged_df = merge_features()
        results["merged"] = {"status": "success", "rows": len(merged_df)}
    except Exception as e:
        logger.error(f"Feature merge failed: {e}")
        results["merged"] = {"status": "error", "error": str(e)}

    logger.info(f"=== Daily update complete: {results} ===")
    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    results = update_daily_data()
    print("\n--- Update Results ---")
    for service, info in results.items():
        print(f"  {service}: {info}")
