"""
generate_new_crop_data.py
Generates synthetic but realistic historical price data for all AGMARKNET-confirmed
AP crops that are missing or under-represented in mandi_data.csv.

The synthetic data is based on:
- Real MSP values (floor prices)
- Seasonal patterns specific to AP
- Realistic price volatility for each crop type

Run: python generate_new_crop_data.py
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

DATA_FILE = os.path.join(os.path.dirname(__file__), "mandi_data.csv")

# NEW CROPS VERIFIED FROM AGMARKNET (not yet in our dataset or under-represented)
NEW_CROPS_CONFIG = {
    # crop_name: {base_price (₹/Quintal), volatility (%), mandis, harvest_months}
    "Barley(Jau)": {
        "base_price": 1800, "volatility": 0.12,
        "mandis": ["Kurnool APMC", "Guntur APMC"],
        "harvest_months": [3, 4],  # Rabi
        "harvest_dip": 0.85,
    },
    "Copra": {
        "base_price": 12000, "volatility": 0.18,
        "mandis": ["Rajahmundry APMC", "Kakinada APMC", "Amalapuram APMC",
                   "Visakhapatnam APMC", "Eluru APMC", "Ambajipeta APMC",
                   "Ravulapelem APMC"],
        "harvest_months": [4, 5, 6],
        "harvest_dip": 0.88,
    },
    "Green Gram(Moong)(Whole)": {
        "base_price": 8800, "volatility": 0.14,
        "mandis": ["Ongole APMC", "Nellore APMC", "Guntur APMC",
                   "Kurnool APMC", "Vijayawada APMC", "Gudur APMC",
                   "Machilipatnam APMC"],
        "harvest_months": [9, 10],
        "harvest_dip": 0.87,
    },
    "Jute": {
        "base_price": 5200, "volatility": 0.10,
        "mandis": ["Eluru APMC", "Bhimavaram APMC", "Nellore APMC",
                   "Rajahmundry APMC", "Tadepalligudem APMC"],
        "harvest_months": [8, 9, 10],
        "harvest_dip": 0.90,
    },
    "Lentil(Masur)(Whole)": {
        "base_price": 6500, "volatility": 0.13,
        "mandis": ["Guntur APMC", "Kurnool APMC"],
        "harvest_months": [2, 3, 4],
        "harvest_dip": 0.86,
    },
    "Mustard": {
        "base_price": 6200, "volatility": 0.12,
        "mandis": ["Kurnool APMC", "Adoni APMC", "Guntur APMC"],
        "harvest_months": [2, 3, 4],
        "harvest_dip": 0.88,
    },
    "Niger Seed(Ramtil)": {
        "base_price": 9000, "volatility": 0.16,
        "mandis": ["Srikakulam APMC", "Narasannapeta APMC", "Palasa APMC",
                   "Anantapur APMC", "Guntakal APMC"],
        "harvest_months": [10, 11, 12],
        "harvest_dip": 0.85,
    },
    "Ragi(Finger Millet)": {
        "base_price": 4400, "volatility": 0.12,
        "mandis": ["Madanapalli APMC", "Palamaner APMC", "Tirupati APMC",
                   "Hindupur APMC", "Vizianagaram APMC", "Srikakulam APMC",
                   "Punganur APMC", "Kalikiri APMC"],
        "harvest_months": [9, 10, 11],
        "harvest_dip": 0.88,
    },
    "Safflower": {
        "base_price": 6000, "volatility": 0.14,
        "mandis": ["Kurnool APMC", "Anantapur APMC", "Dharmavaram APMC",
                   "Kadapa APMC", "Chittoor APMC", "Cuddapah APMC"],
        "harvest_months": [3, 4, 5],
        "harvest_dip": 0.87,
    },
    "Sesamum(Sesame,Gingelly,Til)": {
        "base_price": 9500, "volatility": 0.15,
        "mandis": ["Kurnool APMC", "Anantapur APMC", "Guntur APMC",
                   "Kadapa APMC", "Vijayawada APMC", "Chilakaluripet APMC",
                   "Rapur APMC", "Dharmavaram APMC"],
        "harvest_months": [9, 10],
        "harvest_dip": 0.86,
    },
    "Soyabean": {
        "base_price": 5000, "volatility": 0.12,
        "mandis": ["Guntur APMC", "Kurnool APMC"],
        "harvest_months": [10, 11],
        "harvest_dip": 0.88,
    },
    "Rapeseed(Toria)": {
        "base_price": 6100, "volatility": 0.12,
        "mandis": ["Kurnool APMC", "Guntur APMC"],
        "harvest_months": [2, 3, 4],
        "harvest_dip": 0.87,
    },
    "Wheat": {
        "base_price": 2400, "volatility": 0.08,
        "mandis": ["Kurnool APMC", "Guntur APMC", "Vijayawada APMC"],
        "harvest_months": [3, 4, 5],
        "harvest_dip": 0.90,
    },
    "Sugarcane": {
        "base_price": 3200, "volatility": 0.06,
        "mandis": ["Jaggaiahpeta APMC", "Eluru APMC", "Vizianagaram APMC",
                   "Srikakulam APMC", "Tirupati APMC", "Chittoor APMC",
                   "Bobbili APMC"],
        "harvest_months": [11, 12, 1, 2],
        "harvest_dip": 0.92,
    },
}

def generate_price_series(base_price, volatility, dates, harvest_months, harvest_dip):
    """Generate a realistic price time-series with seasonality and trend."""
    np.random.seed(42)
    prices = []
    prev = base_price
    trend = np.random.uniform(-0.01, 0.02) / 365  # Slight annual trend

    for d in dates:
        # Convert numpy datetime64 to pandas Timestamp to use .month
        ts = pd.Timestamp(d)
        # Seasonal multiplier
        is_harvest = ts.month in harvest_months
        multiplier = harvest_dip if is_harvest else 1.0

        # Lean season (3–4 months before harvest) → price rises
        harvest_soon = any(
            (ts + pd.DateOffset(days=90)).month == hm for hm in harvest_months
        )
        if harvest_soon and not is_harvest:
            multiplier = 1.05

        # Random daily change
        change = np.random.normal(0, volatility / 100)
        new_price = prev * (1 + change + trend) * multiplier
        new_price = max(new_price, base_price * 0.6)  # floor at 60% of base
        new_price = min(new_price, base_price * 2.0)  # ceil at 200% of base
        prices.append(round(new_price, 1))
        prev = new_price

    return prices


def generate_for_crop(crop_name, config, start_date, end_date):
    """Generate synthetic data for one crop across its mandis."""
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    # Only include trading days (not all mandis trade daily)
    # Sample ~50% of days (weekdays + market days)
    sampled_dates = sorted(
        np.random.choice(dates, size=int(len(dates) * 0.6), replace=False)
    )

    rows = []
    for mandi in config["mandis"]:
        # Each mandi has slightly different base prices
        mandi_factor = np.random.uniform(0.92, 1.08)
        base = config["base_price"] * mandi_factor
        prices = generate_price_series(
            base, config["volatility"], sampled_dates,
            config["harvest_months"], config["harvest_dip"]
        )

        for date, price in zip(sampled_dates, prices):
            spread = price * np.random.uniform(0.02, 0.08)
            rows.append({
                "state": "Andhra Pradesh",
                "mandi": mandi,
                "commodity": crop_name,
                "date": pd.Timestamp(date),
                "min_price": round(price - spread, 1),
                "max_price": round(price + spread, 1),
                "modal_price": round(price, 1),
                "arrivals": int(np.random.uniform(10, 500)),
            })

    return pd.DataFrame(rows)


def main():
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2026, 2, 28)

    print(f"=== Generating synthetic data for {len(NEW_CROPS_CONFIG)} new AP crops ===")
    print(f"Period: {start_date.date()} → {end_date.date()}")

    # Load existing
    if os.path.exists(DATA_FILE):
        df_existing = pd.read_csv(DATA_FILE)
        df_existing["date"] = pd.to_datetime(df_existing["date"], errors="coerce")
        ap_existing = df_existing[df_existing["state"] == "Andhra Pradesh"]
        existing_crops = set(ap_existing["commodity"].unique())
        print(f"Existing AP crops: {len(existing_crops)}")
    else:
        df_existing = pd.DataFrame()
        existing_crops = set()

    all_new = []
    for crop_name, config in NEW_CROPS_CONFIG.items():
        if crop_name in existing_crops:
            count = len(ap_existing[ap_existing["commodity"] == crop_name])
            if count > 100:
                print(f"  ✓ {crop_name}: already has {count} rows — skipping")
                continue

        df_crop = generate_for_crop(crop_name, config, start_date, end_date)
        all_new.append(df_crop)
        print(f"  ✓ {crop_name}: generated {len(df_crop)} rows across {len(config['mandis'])} mandis")

    if all_new:
        df_new = pd.concat(all_new, ignore_index=True)
        print(f"\nTotal new rows: {len(df_new)}")

        if not df_existing.empty:
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new

        df_combined.drop_duplicates(subset=["state", "mandi", "commodity", "date"], keep="last", inplace=True)
        df_combined.to_csv(DATA_FILE, index=False)
        print(f"Saved! Total DB rows: {len(df_combined)}")

        # Print crop summary
        ap_df = df_combined[df_combined["state"] == "Andhra Pradesh"]
        print(f"\n=== FINAL AP CROP COUNT: {ap_df['commodity'].nunique()} unique crops ===")
        for c in sorted(ap_df["commodity"].unique()):
            cnt = len(ap_df[ap_df["commodity"] == c])
            print(f"  {c}: {cnt} records")
    else:
        print("No new data generated (all crops already covered).")


if __name__ == "__main__":
    main()
