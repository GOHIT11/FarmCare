"""Test the calendar service."""
import sys
sys.path.insert(0, '.')

from services.calendar_service import get_calendar_features, fetch_holidays

# Test 1: Today's features
features = get_calendar_features()
print("Today features:", features)

# Test 2: Fetch holidays for this year
holidays = fetch_holidays(2026)
print(f"Holidays found: {len(holidays)}")
for h in holidays[:10]:
    print(f"  {h['date']}: {h['name']}")
