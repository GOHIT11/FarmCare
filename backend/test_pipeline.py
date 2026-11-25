"""End-to-end test of the daily data pipeline."""
import sys
import logging

sys.path.insert(0, '.')
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

from services.feature_engineering import update_daily_data

print("=== Running full daily update pipeline ===")
results = update_daily_data()

print("\n--- Results ---")
for service, info in results.items():
    print(f"  {service}: {info}")

# Verify CSV outputs exist
import os
import pandas as pd

data_dir = os.path.join(os.path.dirname(__file__), 'daily_data')
for fname in ['arrivals.csv', 'weather.csv', 'calendar_features.csv', 'prices.csv', 'merged_features.csv']:
    fpath = os.path.join(data_dir, fname)
    if os.path.exists(fpath):
        df = pd.read_csv(fpath)
        print(f"\n  {fname}: {df.shape[0]} rows, {df.shape[1]} cols")
        print(f"    Columns: {list(df.columns)}")
        print(f"    Sample:\n{df.head(2).to_string()}")
    else:
        print(f"\n  {fname}: NOT FOUND")
