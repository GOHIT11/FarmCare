"""
AP Mandi Predict — Calendar & Festival Service
Fetches Indian holiday data from Google Calendar API using a service account.
Generates calendar features: is_weekend, is_festival_week, days_to_next_festival.
"""

import os
import logging
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger(__name__)

# Config from .env
CREDENTIALS_PATH = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
CALENDAR_ID = os.getenv("HOLIDAY_CALENDAR_ID", "en.indian#holiday@group.v.calendar.google.com")
FESTIVAL_WINDOW = int(os.getenv("FESTIVAL_WINDOW_DAYS", "5"))

# Resolve credentials path relative to backend dir
BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
if CREDENTIALS_PATH and not os.path.isabs(CREDENTIALS_PATH):
    CREDENTIALS_PATH = os.path.join(BACKEND_DIR, CREDENTIALS_PATH)

# Output path
DATA_DIR = os.path.join(BACKEND_DIR, 'daily_data')
CALENDAR_FILE = os.path.join(DATA_DIR, 'calendar_features.csv')

# Cache fetched holidays to avoid repeated API calls during a single run
_holiday_cache = {}


def _get_calendar_service():
    """
    Build and return a Google Calendar API service using service account credentials.
    """
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        scopes = ['https://www.googleapis.com/auth/calendar.readonly']

        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_PATH, scopes=scopes
        )

        service = build('calendar', 'v3', credentials=credentials, cache_discovery=False)
        return service

    except FileNotFoundError:
        logger.error(f"Google Calendar credentials not found at: {CREDENTIALS_PATH}")
        raise
    except Exception as e:
        logger.error(f"Failed to build Google Calendar service: {e}")
        raise


def fetch_holidays(year: int) -> list:
    """
    Fetch Indian holidays for a given year from Google Calendar API.
    
    Args:
        year: The year to fetch holidays for.
    
    Returns:
        List of dicts: [{"date": "YYYY-MM-DD", "name": "Festival Name"}, ...]
    """
    cache_key = year
    if cache_key in _holiday_cache:
        return _holiday_cache[cache_key]

    try:
        service = _get_calendar_service()

        time_min = f"{year}-01-01T00:00:00Z"
        time_max = f"{year}-12-31T23:59:59Z"

        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime',
            maxResults=100,
        ).execute()

        events = events_result.get('items', [])
        holidays = []

        for event in events:
            start = event.get('start', {})
            # All-day events use 'date', timed events use 'dateTime'
            date_str = start.get('date') or start.get('dateTime', '')[:10]
            name = event.get('summary', 'Unknown Holiday')

            if date_str:
                holidays.append({
                    "date": date_str,
                    "name": name,
                })

        logger.info(f"Fetched {len(holidays)} holidays for year {year}")
        _holiday_cache[cache_key] = holidays
        return holidays

    except Exception as e:
        logger.error(f"Failed to fetch holidays for {year}: {e}")
        return []


def _get_holidays_as_dates(year: int) -> list:
    """
    Get holidays for a year as a list of datetime.date objects.
    """
    holidays = fetch_holidays(year)
    dates = []
    for h in holidays:
        try:
            dates.append(datetime.strptime(h['date'], "%Y-%m-%d").date())
        except ValueError:
            continue
    return dates


def get_calendar_features(target_date: datetime = None) -> dict:
    """
    Generate calendar features for a single date.
    
    Args:
        target_date: The date to generate features for. Defaults to today.
    
    Returns:
        Dict with: date, is_weekend, is_festival_week, days_to_next_festival
    """
    if target_date is None:
        target_date = datetime.now()

    target = target_date.date() if isinstance(target_date, datetime) else target_date

    # Check weekend (Saturday=5, Sunday=6)
    is_weekend = 1 if target.weekday() in (5, 6) else 0

    # Get holidays for this year and next year (for year-end dates)
    holidays_this_year = _get_holidays_as_dates(target.year)
    holidays_next_year = _get_holidays_as_dates(target.year + 1)
    all_holidays = sorted(set(holidays_this_year + holidays_next_year))

    # Days to next festival
    future_holidays = [h for h in all_holidays if h >= target]
    if future_holidays:
        days_to_next = (future_holidays[0] - target).days
    else:
        days_to_next = 365  # Fallback: no upcoming holidays found

    # Is festival week: 1 if any festival is within FESTIVAL_WINDOW days ahead
    is_festival_week = 1 if days_to_next <= FESTIVAL_WINDOW else 0

    return {
        "date": target.strftime("%Y-%m-%d"),
        "is_weekend": is_weekend,
        "is_festival_week": is_festival_week,
        "days_to_next_festival": days_to_next,
    }


def get_calendar_features_range(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Generate calendar features for a date range.
    
    Args:
        start_date: Range start (inclusive)
        end_date: Range end (inclusive)
    
    Returns:
        DataFrame with columns: date, is_weekend, is_festival_week, days_to_next_festival
    """
    start = start_date.date() if isinstance(start_date, datetime) else start_date
    end = end_date.date() if isinstance(end_date, datetime) else end_date

    rows = []
    current = start
    while current <= end:
        features = get_calendar_features(current)
        rows.append(features)
        current += timedelta(days=1)

    return pd.DataFrame(rows)


def save_calendar_features(df: pd.DataFrame) -> str:
    """
    Append calendar features to CSV, avoiding duplicates.
    Returns path to saved file.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    if df.empty:
        logger.warning("No calendar data to save.")
        return CALENDAR_FILE

    if os.path.exists(CALENDAR_FILE):
        existing = pd.read_csv(CALENDAR_FILE)
        combined = pd.concat([existing, df], ignore_index=True)
        combined.drop_duplicates(subset=['date'], keep='last', inplace=True)
    else:
        combined = df

    combined.sort_values('date', inplace=True)
    combined.to_csv(CALENDAR_FILE, index=False)
    logger.info(f"Saved calendar features to {CALENDAR_FILE} ({len(combined)} rows)")
    return CALENDAR_FILE


def update_calendar(target_date: datetime = None) -> pd.DataFrame:
    """
    Full pipeline: generate calendar features for target date → save.
    Returns the features DataFrame.
    """
    features = get_calendar_features(target_date)
    df = pd.DataFrame([features])
    save_calendar_features(df)
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test: generate features for today
    result = get_calendar_features()
    print(f"Today's features: {result}")

    # Test: fetch holidays
    holidays = fetch_holidays(datetime.now().year)
    for h in holidays[:10]:
        print(f"  {h['date']}: {h['name']}")
