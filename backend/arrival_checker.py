"""
AP Mandi Predict — Arrival Checker
Queries the local mandi_data.csv for per-district, per-crop arrival data.
Provides activity classification (Active / Low Activity / Inactive).
"""

import os
import logging
import pandas as pd
from datetime import datetime, timedelta

from vegetable_config import (
    VEGETABLES, VEGETABLE_ALIASES,
    ACTIVE_THRESHOLD_3D, LOW_ACTIVITY_THRESHOLD_7D,
)
from master_data import DISTRICT_MANDIS

logger = logging.getLogger(__name__)

# Path to the big local dataset (updated daily by scheduler)
MANDI_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mandi_data.csv")

# In-memory cache to avoid re-reading 272MB on every request
_df_cache = {
    "df": None,
    "loaded_at": None,
    "max_age_seconds": 600,  # refresh every 10 minutes
}


def _load_data() -> pd.DataFrame:
    """
    Load mandi_data.csv with caching.
    Only re-reads the file if cache is stale or empty.
    """
    now = datetime.now()

    if (
        _df_cache["df"] is not None
        and _df_cache["loaded_at"] is not None
        and (now - _df_cache["loaded_at"]).total_seconds() < _df_cache["max_age_seconds"]
    ):
        return _df_cache["df"]

    if not os.path.exists(MANDI_CSV):
        logger.error(f"mandi_data.csv not found at {MANDI_CSV}")
        return pd.DataFrame()

    logger.info("Loading mandi_data.csv into memory...")
    try:
        df = pd.read_csv(
            MANDI_CSV,
            usecols=lambda c: c.lower() in [
                "state", "market", "mandi", "commodity",
                "arrivals", "arrivals_in_qtl",
                "modal_price", "min_price", "max_price",
                "arrival_date", "date",
            ],
            low_memory=False,
        )
    except Exception as e:
        logger.error(f"Failed to read mandi_data.csv: {e}")
        return pd.DataFrame()

    # Normalize column names
    df.columns = df.columns.str.lower().str.strip()

    # Standardize date column
    date_col = None
    for candidate in ["date", "arrival_date"]:
        if candidate in df.columns:
            date_col = candidate
            break

    if date_col and date_col != "date":
        df.rename(columns={date_col: "date"}, inplace=True)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
        df.dropna(subset=["date"], inplace=True)

    # Standardize mandi column
    if "market" in df.columns and "mandi" not in df.columns:
        df.rename(columns={"market": "mandi"}, inplace=True)

    # Standardize arrivals column
    if "arrivals_in_qtl" in df.columns:
        df["arrivals"] = pd.to_numeric(df["arrivals_in_qtl"], errors="coerce").fillna(0)
    elif "arrivals" in df.columns:
        df["arrivals"] = pd.to_numeric(df["arrivals"], errors="coerce").fillna(0)
    else:
        df["arrivals"] = 0

    # Filter AP only
    if "state" in df.columns:
        df = df[df["state"].str.strip().str.lower() == "andhra pradesh"]

    _df_cache["df"] = df
    _df_cache["loaded_at"] = now
    logger.info(f"Loaded {len(df)} AP records from mandi_data.csv")
    return df


def _resolve_commodity(crop: str) -> list[str]:
    """
    Given a crop name, return a list of possible names it could appear as
    in the CSV (handles aliases).
    """
    names = [crop]
    # Check if crop is an alias
    if crop in VEGETABLE_ALIASES:
        names.append(VEGETABLE_ALIASES[crop])
    # Check if anything else maps to this crop
    for alias, canonical in VEGETABLE_ALIASES.items():
        if canonical == crop and alias not in names:
            names.append(alias)
    return names


def _get_district_mandis(district: str) -> list[str]:
    """Get list of mandis for a district."""
    mandis = DISTRICT_MANDIS.get(district, [])
    if not mandis:
        # Try case-insensitive match
        for d, m in DISTRICT_MANDIS.items():
            if d.lower().strip() == district.lower().strip():
                return m
    return mandis


def get_crop_mandi_breakdown(crop: str, days: int = 30) -> dict:
    """
    Get mandi-wise arrival breakdown for a specific vegetable across all AP.
    Groups results by district.

    Returns:
        {
            "crop": str,
            "districts": [
                {
                    "district": str,
                    "total_3d": float,
                    "total_7d": float,
                    "mandis": [
                        {
                            "mandi": str,
                            "arrival_3d": float,
                            "arrival_7d": float,
                            "latest_price": float or None,
                        }
                    ]
                }
            ]
        }
    """
    from master_data import MANDI_TO_DISTRICT

    df = _load_data()
    if df.empty:
        return {"crop": crop, "districts": []}

    # Filter by commodity (handle aliases)
    crop_names = _resolve_commodity(crop)
    mask_commodity = df["commodity"].str.strip().isin(crop_names)

    # Filter by date range
    cutoff = datetime.now() - timedelta(days=days)
    mask_date = df["date"] >= cutoff

    filtered = df[mask_commodity & mask_date].copy()

    if filtered.empty:
        return {"crop": crop, "districts": []}

    # Get latest date for 3d/7d splits
    cutoff_3d = datetime.now() - timedelta(days=3)
    cutoff_7d = datetime.now() - timedelta(days=7)

    # Group by mandi
    mandi_data = {}
    for mandi_name, group in filtered.groupby("mandi"):
        arr_3d = float(group[group["date"] >= cutoff_3d]["arrivals"].sum())
        arr_7d = float(group[group["date"] >= cutoff_7d]["arrivals"].sum())

        # Get latest modal price
        latest = group.sort_values("date", ascending=False).head(1)
        latest_price = None
        if "modal_price" in latest.columns:
            price_val = latest["modal_price"].values[0]
            try:
                latest_price = round(float(price_val), 2)
            except (ValueError, TypeError):
                pass

        if arr_7d > 0 or arr_3d > 0:  # Only include mandis with actual arrivals
            district = MANDI_TO_DISTRICT.get(mandi_name, "Other")
            if district not in mandi_data:
                mandi_data[district] = []
            mandi_data[district].append({
                "mandi": mandi_name,
                "arrival_3d": round(arr_3d, 2),
                "arrival_7d": round(arr_7d, 2),
                "latest_price": latest_price,
            })

    # Build district list sorted by total arrivals
    districts = []
    for district, mandis in mandi_data.items():
        total_3d = sum(m["arrival_3d"] for m in mandis)
        total_7d = sum(m["arrival_7d"] for m in mandis)
        # Sort mandis by 7d arrivals descending
        mandis.sort(key=lambda x: x["arrival_7d"], reverse=True)
        districts.append({
            "district": district,
            "total_3d": round(total_3d, 2),
            "total_7d": round(total_7d, 2),
            "mandis": mandis,
        })

    # Sort districts by total_7d descending
    districts.sort(key=lambda x: x["total_7d"], reverse=True)

    logger.info(
        f"Mandi breakdown for {crop}: "
        f"{len(districts)} districts, "
        f"{sum(len(d['mandis']) for d in districts)} mandis"
    )

    return {"crop": crop, "districts": districts}


def get_crop_arrivals(district: str, crop: str, days: int = 30,
                      statewide: bool = False) -> pd.DataFrame:
    """
    Get daily arrival data for a specific crop over the last N days.

    Args:
        district: District name (e.g., "Guntur")
        crop: Commodity name (e.g., "Tomato")
        days: Number of days to look back (default 30)
        statewide: If True, search ALL AP mandis instead of just district mandis

    Returns:
        DataFrame with columns: date, arrivals
        Sorted by date descending.
    """
    df = _load_data()
    if df.empty:
        return pd.DataFrame(columns=["date", "arrivals"])

    if not statewide:
        # Get mandis in this district
        mandis = _get_district_mandis(district)
        if not mandis:
            logger.warning(f"No mandis found for district: {district}")
            return pd.DataFrame(columns=["date", "arrivals"])
        # Filter by mandis
        mask_mandi = df["mandi"].isin(mandis)
    else:
        # State-wide: no mandi filter needed (already filtered to AP)
        mask_mandi = pd.Series(True, index=df.index)

    # Filter by commodity (handle aliases)
    crop_names = _resolve_commodity(crop)
    mask_commodity = df["commodity"].str.strip().isin(crop_names)

    # Filter by date range
    cutoff = datetime.now() - timedelta(days=days)
    mask_date = df["date"] >= cutoff

    filtered = df[mask_mandi & mask_commodity & mask_date].copy()

    if filtered.empty:
        return pd.DataFrame(columns=["date", "arrivals"])

    # Aggregate by date (sum arrivals across mandis)
    daily = (
        filtered.groupby("date")
        .agg(arrivals=("arrivals", "sum"))
        .reset_index()
        .sort_values("date", ascending=False)
    )

    return daily


def check_crop_activity(district: str, crop: str,
                        statewide: bool = False) -> dict:
    """
    Check trading activity status for a crop.

    Simplified logic:
        - arrival_7d > 0 → "Active"
        - arrival_7d == 0 → "Low Activity"

    Returns:
        {
            "status": "Active" | "Low Activity",
            "arrival_3d": float,
            "arrival_7d": float,
            "crop": str,
            "district": str,
            "source": "district" | "state"
        }
    """
    daily = get_crop_arrivals(district, crop, days=30, statewide=statewide)
    source = "state" if statewide else "district"

    if daily.empty:
        return {
            "status": "Low Activity",
            "arrival_3d": 0,
            "arrival_7d": 0,
            "crop": crop,
            "district": district,
            "source": source,
        }

    # Sort by date descending to get most recent first
    daily = daily.sort_values("date", ascending=False)

    # 7-day sum (top 7 most recent days)
    arrival_7d = float(daily.head(7)["arrivals"].sum())

    # 3-day sum (top 3 most recent days)
    arrival_3d = float(daily.head(3)["arrivals"].sum())

    # Simplified classification
    status = "Active" if arrival_7d > 0 else "Low Activity"

    return {
        "status": status,
        "arrival_3d": round(arrival_3d, 2),
        "arrival_7d": round(arrival_7d, 2),
        "crop": crop,
        "district": district,
        "source": source,
    }


def get_active_crops(district: str) -> dict:
    """
    Get activity status for ALL vegetables.
    Always uses state-wide data to ensure comprehensive results.

    Returns:
        {
            "district": str,
            "active": [...],
            "low_activity": [...],
            "inactive": [],
            "note": str
        }
    """
    result = {
        "district": district,
        "active": [],
        "low_activity": [],
        "inactive": [],   # Always empty — kept for API compatibility
        "note": "Vegetable trading activity based on Andhra Pradesh mandi data.",
    }

    for veg in VEGETABLES:
        # Always check state-wide for comprehensive data
        activity = check_crop_activity(district, veg, statewide=True)
        entry = {
            "crop": veg,
            "arrival_3d": activity["arrival_3d"],
            "arrival_7d": activity["arrival_7d"],
            "status": activity["status"],
        }

        if activity["status"] == "Active":
            result["active"].append(entry)
        else:
            result["low_activity"].append(entry)

    logger.info(
        f"District {district} (state-wide): "
        f"{len(result['active'])} active, "
        f"{len(result['low_activity'])} low activity vegetables"
    )
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=== Checking Kakinada (state-wide) ===")
    result = get_active_crops("Kakinada")
    print(f"Active ({len(result['active'])}): {[c['crop'] for c in result['active']]}")
    print(f"Low Activity ({len(result['low_activity'])}): {[c['crop'] for c in result['low_activity']]}")


