"""
AP Mandi Predict — Weather Service
Fetches daily weather data from Open-Meteo API.
Coordinates and timezone loaded from .env configuration.
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
LATITUDE = os.getenv("AP_LATITUDE")
LONGITUDE = os.getenv("AP_LONGITUDE")
TIMEZONE = os.getenv("AP_TIMEZONE", "Asia/Kolkata")

# Output path
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'daily_data')
WEATHER_FILE = os.path.join(DATA_DIR, 'weather.csv')

# Open-Meteo endpoints
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


_is_offline = False


def fetch_weather(target_date: datetime = None) -> pd.DataFrame:
    """
    Fetch daily weather data from Open-Meteo.
    Uses forecast endpoint for today/future, archive endpoint for past dates.
    
    Args:
        target_date: Date to fetch weather for. Defaults to today.
    
    Returns:
        DataFrame with columns: date, temperature_2m_max, temperature_2m_min,
                                 temp_avg, precipitation_sum, rainfall_flag,
                                 windspeed_10m_max
    """
    global _is_offline
    if _is_offline:
        return pd.DataFrame()
    if target_date is None:
        target_date = datetime.now()

    today = datetime.now().date()
    target = target_date.date() if isinstance(target_date, datetime) else target_date

    # Decide which endpoint to use
    if target >= today:
        # Forecast endpoint (today or future)
        url = FORECAST_URL
        params = {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
            "timezone": TIMEZONE,
        }
    else:
        # Archive endpoint (historical)
        url = ARCHIVE_URL
        date_str = target.strftime("%Y-%m-%d")
        params = {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "start_date": date_str,
            "end_date": date_str,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
            "timezone": TIMEZONE,
        }

    try:
        logger.info(f"Fetching weather from {url} for {target.strftime('%Y-%m-%d')}...")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        daily = data.get("daily", {})
        if not daily or not daily.get("time"):
            logger.warning("No weather data in API response")
            return pd.DataFrame()

        df = pd.DataFrame(daily)
        df.rename(columns={"time": "date"}, inplace=True)

        # Filter to target date only (forecast returns multiple days)
        target_str = target.strftime("%Y-%m-%d")
        df = df[df['date'] == target_str].copy()

        if df.empty:
            logger.warning(f"Target date {target_str} not found in weather response")
            return pd.DataFrame()

        # Feature engineering
        df["temp_avg"] = (
            df["temperature_2m_max"].fillna(0) + df["temperature_2m_min"].fillna(0)
        ) / 2
        df["temp_avg"] = df["temp_avg"].round(2)

        df["rainfall_flag"] = df["precipitation_sum"].apply(
            lambda x: 1 if pd.notna(x) and x > 0 else 0
        )

        logger.info(f"Weather data fetched for {target_str}")
        return df[['date', 'temperature_2m_max', 'temperature_2m_min', 'temp_avg',
                    'precipitation_sum', 'rainfall_flag', 'windspeed_10m_max']]

    except requests.RequestException as e:
        logger.error(f"Open-Meteo API request failed: {e}")
        if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
            logger.warning("Connection/Timeout error detected. Setting weather_service to offline mode.")
            _is_offline = True
        return pd.DataFrame()


def fetch_weather_range(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Fetch weather data for a date range.
    Uses archive endpoint for historical ranges, forecast for future.
    
    Args:
        start_date: Range start (inclusive)
        end_date: Range end (inclusive)
    
    Returns:
        DataFrame with weather data for all dates in range.
    """
    global _is_offline
    if _is_offline:
        return pd.DataFrame()

    today = datetime.now().date()
    start = start_date.date() if isinstance(start_date, datetime) else start_date
    end = end_date.date() if isinstance(end_date, datetime) else end_date

    frames = []

    # Historical portion (archive API supports date ranges)
    if start < today:
        archive_end = min(end, today - timedelta(days=1))
        url = ARCHIVE_URL
        params = {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": archive_end.strftime("%Y-%m-%d"),
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
            "timezone": TIMEZONE,
        }
        try:
            logger.info(f"Fetching archive weather {start} to {archive_end}...")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            daily = data.get("daily", {})
            if daily and daily.get("time"):
                df = pd.DataFrame(daily)
                df.rename(columns={"time": "date"}, inplace=True)
                frames.append(df)
        except requests.RequestException as e:
            logger.error(f"Archive weather fetch failed: {e}")

    # Forecast portion (today and future)
    if end >= today:
        url = FORECAST_URL
        params = {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
            "timezone": TIMEZONE,
        }
        try:
            logger.info(f"Fetching forecast weather...")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            daily = data.get("daily", {})
            if daily and daily.get("time"):
                df = pd.DataFrame(daily)
                df.rename(columns={"time": "date"}, inplace=True)
                # Filter to requested range
                df = df[(df['date'] >= today.strftime("%Y-%m-%d")) &
                        (df['date'] <= end.strftime("%Y-%m-%d"))]
                frames.append(df)
        except requests.RequestException as e:
            logger.error(f"Forecast weather fetch failed: {e}")

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    combined.drop_duplicates(subset=['date'], keep='last', inplace=True)

    # Feature engineering
    combined["temp_avg"] = (
        combined["temperature_2m_max"].fillna(0) + combined["temperature_2m_min"].fillna(0)
    ) / 2
    combined["temp_avg"] = combined["temp_avg"].round(2)
    combined["rainfall_flag"] = combined["precipitation_sum"].apply(
        lambda x: 1 if pd.notna(x) and x > 0 else 0
    )

    combined.sort_values('date', inplace=True)
    return combined[['date', 'temperature_2m_max', 'temperature_2m_min', 'temp_avg',
                      'precipitation_sum', 'rainfall_flag', 'windspeed_10m_max']]


def save_weather(df: pd.DataFrame) -> str:
    """
    Append weather data to CSV, avoiding duplicates.
    Returns path to saved file.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    if df.empty:
        logger.warning("No weather data to save.")
        return WEATHER_FILE

    if os.path.exists(WEATHER_FILE):
        existing = pd.read_csv(WEATHER_FILE)
        combined = pd.concat([existing, df], ignore_index=True)
        combined.drop_duplicates(subset=['date'], keep='last', inplace=True)
    else:
        combined = df

    combined.sort_values('date', inplace=True)
    combined.to_csv(WEATHER_FILE, index=False)
    logger.info(f"Saved weather data to {WEATHER_FILE} ({len(combined)} rows)")
    return WEATHER_FILE


def update_weather(target_date: datetime = None) -> pd.DataFrame:
    """
    Full pipeline: fetch today's weather → save.
    Returns the fetched DataFrame.
    """
    df = fetch_weather(target_date)
    save_weather(df)
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = fetch_weather()
    print(result)
