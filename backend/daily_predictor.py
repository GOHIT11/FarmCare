"""
AP Mandi Predict — Daily Predictor
Loads trained XGBoost daily models and generates multi-step
day-to-day price predictions with confidence intervals.
"""

import os
import logging
import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

logger = logging.getLogger(__name__)

# Paths
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BACKEND_DIR, 'daily_data')
DAILY_MODELS_DIR = os.path.join(BACKEND_DIR, 'models', 'daily')
MERGED_FILE = os.path.join(DATA_DIR, 'merged_features.csv')

# Import feature definitions and engineering from daily_model
from daily_model import (
    DAILY_FEATURE_NAMES, engineer_features
)
from ap_config import (
    get_msp, get_seasonality_features, get_export_features,
    CYCLONE_MONTHS, AP_STATE_CENTER, get_district_coords
)
from weather_service import get_forecast

# Cache for loaded models
_daily_model_cache = {}


def _safe_commodity_name(commodity: str) -> str:
    """Sanitize commodity name for filesystem."""
    return (commodity.replace("/", "_").replace("\\", "_")
            .replace(":", "_").replace("(", "_").replace(")", "_")
            .replace(" ", "_"))


def load_daily_model(commodity: str):
    """
    Load a trained daily XGBoost model for a commodity.
    Returns the model dict or None if not found.
    """
    if commodity in _daily_model_cache:
        return _daily_model_cache[commodity]

    safe_name = _safe_commodity_name(commodity)
    model_path = os.path.join(DAILY_MODELS_DIR, f"daily_{safe_name}.joblib")

    if not os.path.exists(model_path):
        logger.debug(f"No daily model found for {commodity} at {model_path}")
        return None

    try:
        model_data = joblib.load(model_path)
        _daily_model_cache[commodity] = model_data
        logger.info(f"Loaded daily model for {commodity} "
                     f"(MAPE: {model_data['metrics']['mape']:.1f}%)")
        return model_data
    except Exception as e:
        logger.error(f"Failed to load daily model for {commodity}: {e}")
        return None


def _get_latest_history(commodity: str, mandi: str = None) -> pd.DataFrame:
    """
    Get the most recent price history for a commodity from merged_features.csv.

    Args:
        commodity: Crop name.
        mandi: Optional specific mandi filter.

    Returns:
        DataFrame with latest data, sorted by date.
    """
    if not os.path.exists(MERGED_FILE):
        logger.warning("merged_features.csv not found")
        return pd.DataFrame()

    df = pd.read_csv(MERGED_FILE)
    df['date'] = pd.to_datetime(df['date'])

    # Filter to commodity
    mask = df['commodity'] == commodity
    if mandi:
        mask = mask & (df['mandi'] == mandi)
    filtered = df[mask].copy()

    if filtered.empty:
        return pd.DataFrame()

    # For prediction, we need a single time-series
    # If no mandi specified, average across mandis per date
    if mandi is None and 'mandi' in filtered.columns:
        filtered = filtered.groupby('date').agg({
            'modal_price': 'mean',
            'min_price': 'mean',
            'max_price': 'mean',
            'total_arrival_state': 'first',
            'avg_modal_price_state': 'first',
            'temperature_2m_max': 'first',
            'temperature_2m_min': 'first',
            'temp_avg': 'first',
            'precipitation_sum': 'first',
            'rainfall_flag': 'first',
            'windspeed_10m_max': 'first',
            'is_weekend': 'first',
            'is_festival_week': 'first',
            'days_to_next_festival': 'first',
        }).reset_index()

    filtered.sort_values('date', inplace=True)
    return filtered


def _build_feature_row(history: pd.DataFrame, target_date,
                       weather_data: dict, commodity: str) -> np.ndarray:
    """
    Build a single feature row for prediction at target_date.
    Uses history up to target_date - 1.

    Args:
        history: Historical data including predicted prices.
        target_date: Date to predict.
        weather_data: Dict with temp_avg, temperature_2m_max, etc.
        commodity: Commodity name.

    Returns:
        Numpy array with features in DAILY_FEATURE_NAMES order.
    """
    prices = history['modal_price'].values
    n = len(prices)

    # ---- Group 1: Price Lags ----
    price_lag_1 = prices[-1] if n >= 1 else 0
    price_lag_2 = prices[-2] if n >= 2 else price_lag_1
    price_lag_3 = prices[-3] if n >= 3 else price_lag_1
    price_lag_7 = prices[-7] if n >= 7 else price_lag_1
    price_lag_14 = prices[-14] if n >= 14 else price_lag_1

    # ---- Group 2: Rolling Statistics ----
    recent_prices = prices[-max(n, 1):]
    price_ma_3 = np.mean(prices[-3:]) if n >= 3 else np.mean(prices)
    price_ma_7 = np.mean(prices[-7:]) if n >= 7 else np.mean(prices)
    price_ma_14 = np.mean(prices[-14:]) if n >= 14 else np.mean(prices)
    price_ma_30 = np.mean(prices[-30:]) if n >= 30 else np.mean(prices)

    price_std_7 = np.std(prices[-7:]) if n >= 7 else (np.std(prices) if n >= 2 else 0)
    price_std_14 = np.std(prices[-14:]) if n >= 14 else (np.std(prices) if n >= 2 else 0)

    # ---- Group 3: Momentum ----
    momentum_1 = prices[-1] - prices[-2] if n >= 2 else 0
    momentum_3 = prices[-1] - prices[-4] if n >= 4 else 0
    momentum_7 = prices[-1] - prices[-8] if n >= 8 else 0
    price_pct_change_1 = (momentum_1 / prices[-2] * 100) if n >= 2 and prices[-2] != 0 else 0

    # ---- Group 4: Arrivals ----
    if 'total_arrival_state' in history.columns:
        arrivals = history['total_arrival_state'].values
        total_arrival = arrivals[-1] if len(arrivals) > 0 else 0
        arrival_lag_1 = arrivals[-1] if len(arrivals) >= 1 else 0
        arrival_ma_7 = np.mean(arrivals[-7:]) if len(arrivals) >= 7 else np.mean(arrivals)
    else:
        total_arrival = 0
        arrival_lag_1 = 0
        arrival_ma_7 = 0

    # ---- Group 5: Weather ----
    temp_avg = weather_data.get('temp_avg', 0)
    temp_max = weather_data.get('temperature_2m_max', weather_data.get('temp_max', 0))
    temp_min = weather_data.get('temperature_2m_min', weather_data.get('temp_min', 0))
    precip = weather_data.get('precipitation_sum', weather_data.get('rain_mm', 0))
    rainfall_flag = 1 if precip > 0 else 0
    windspeed = weather_data.get('windspeed_10m_max', 0)

    # Rainfall lag: use yesterday's value from history
    if 'rainfall_flag' in history.columns:
        rf = history['rainfall_flag'].values
        rainfall_lag_1 = rf[-1] if len(rf) > 0 else 0
    else:
        rainfall_lag_1 = 0

    # Cyclone
    td = target_date if isinstance(target_date, datetime) else datetime.combine(target_date, datetime.min.time())
    month = td.month
    cyclone = 1 if (month in CYCLONE_MONTHS and precip > 20) else 0

    # ---- Group 6: Calendar ----
    day_of_week = td.weekday()
    week_of_year = td.isocalendar()[1]
    quarter = (month - 1) // 3 + 1
    is_weekend = 1 if day_of_week >= 5 else 0

    # Festival data from history's latest or defaults
    if 'is_festival_week' in history.columns and len(history) > 0:
        is_festival_week = int(history['is_festival_week'].iloc[-1])
        days_to_festival = int(history['days_to_next_festival'].iloc[-1])
        # Adjust for prediction day offset
        days_to_festival = max(0, days_to_festival - 1)
        is_festival_week = 1 if days_to_festival <= 5 else is_festival_week
    else:
        is_festival_week = 0
        days_to_festival = 365

    # ---- Group 7: Crop Seasonality ----
    season = get_seasonality_features(commodity, month)

    # ---- Group 8: MSP ----
    msp_value = get_msp(commodity)
    price_vs_msp = (price_lag_1 / msp_value) if msp_value > 0 else 0

    # ---- Group 9: Export ----
    export = get_export_features(commodity, month)

    # Build feature vector in DAILY_FEATURE_NAMES order
    features = [
        # Group 1
        price_lag_1, price_lag_2, price_lag_3, price_lag_7, price_lag_14,
        # Group 2
        price_ma_3, price_ma_7, price_ma_14, price_ma_30,
        price_std_7, price_std_14,
        # Group 3
        momentum_1, momentum_3, momentum_7, price_pct_change_1,
        # Group 4
        total_arrival, arrival_lag_1, arrival_ma_7,
        # Group 5
        temp_avg, temp_max, temp_min, precip, rainfall_flag, rainfall_lag_1,
        windspeed, cyclone,
        # Group 6
        day_of_week, week_of_year, month, quarter,
        is_weekend, is_festival_week, days_to_festival,
        # Group 7
        season['is_kharif_harvest'], season['is_rabi_harvest'],
        season['is_lean_season'],
        # Group 8
        msp_value, price_vs_msp,
        # Group 9
        export['is_export_crop'], export['is_export_season'],
    ]

    return np.array(features, dtype=np.float64)


def predict_daily(commodity: str, mandi: str = None,
                  days: int = 7, district: str = None) -> list:
    """
    Generate day-to-day price predictions using the trained XGBoost daily model.

    Args:
        commodity: Crop/commodity name.
        mandi: Optional mandi name for filtering.
        days: Number of days to predict (default 7).
        district: District for weather forecasts.

    Returns:
        List of dicts: [{"date": "YYYY-MM-DD", "predicted_price": float,
                         "confidence_low": float, "confidence_high": float,
                         "source": "daily_model"}, ...]
    """
    model_data = load_daily_model(commodity)
    if model_data is None:
        logger.info(f"No daily model for {commodity}. Returning empty.")
        return []

    xgb_model = model_data['model']
    model_metrics = model_data['metrics']

    # Get history
    history = _get_latest_history(commodity, mandi)
    if history.empty or len(history) < 3:
        logger.warning(f"Insufficient history for {commodity}. Need at least 3 rows.")
        return []

    # Fetch weather forecast
    try:
        if district:
            coords = get_district_coords(district)
        else:
            coords = AP_STATE_CENTER
        weather_forecasts = get_forecast(coords['lat'], coords['lon'], days=days + 5)
    except Exception as e:
        logger.warning(f"Weather forecast failed: {e}. Using defaults.")
        weather_forecasts = []

    # Prediction confidence based on model MAPE
    mape = model_metrics.get('mape', 5.0)
    confidence_pct = max(mape / 100, 0.02)  # At least 2% interval

    # Multi-step prediction loop
    predictions = []
    current_history = history.copy()
    today = datetime.now().date()

    for step in range(days):
        target_date = today + timedelta(days=step)

        # Get weather for this day
        weather_day = {}
        if weather_forecasts and step < len(weather_forecasts):
            weather_day = weather_forecasts[step]

        # Build feature row
        try:
            features = _build_feature_row(
                current_history, target_date, weather_day, commodity
            )
        except Exception as e:
            logger.error(f"Feature building failed at step {step}: {e}")
            break

        # Predict
        dmatrix = xgb.DMatrix(
            features.reshape(1, -1),
            feature_names=DAILY_FEATURE_NAMES
        )
        pred_price = float(xgb_model.predict(dmatrix)[0])

        # Ensure price is positive and reasonable
        last_price = current_history['modal_price'].iloc[-1]
        max_daily_change = 0.15  # Max 15% change per day
        pred_price = max(pred_price, last_price * (1 - max_daily_change))
        pred_price = min(pred_price, last_price * (1 + max_daily_change))
        pred_price = max(pred_price, 0)

        # Confidence interval widens with prediction horizon
        horizon_factor = 1 + (step * 0.1)  # 10% wider per day
        low = pred_price * (1 - confidence_pct * horizon_factor)
        high = pred_price * (1 + confidence_pct * horizon_factor)

        predictions.append({
            "date": target_date.strftime("%Y-%m-%d"),
            "predicted_price": round(pred_price, 2),
            "confidence_low": round(low, 2),
            "confidence_high": round(high, 2),
            "source": "daily_model",
        })

        # Feed prediction back into history for next step
        new_row = {
            'date': pd.Timestamp(target_date),
            'modal_price': pred_price,
            'total_arrival_state': current_history['total_arrival_state'].iloc[-1]
                if 'total_arrival_state' in current_history.columns else 0,
            'rainfall_flag': weather_day.get('rain_mm', 0) > 0 if weather_day else 0,
        }
        # Copy over weather columns
        for col in ['temperature_2m_max', 'temperature_2m_min', 'temp_avg',
                     'precipitation_sum', 'windspeed_10m_max',
                     'is_weekend', 'is_festival_week', 'days_to_next_festival']:
            if col in current_history.columns:
                new_row[col] = current_history[col].iloc[-1]

        current_history = pd.concat(
            [current_history, pd.DataFrame([new_row])],
            ignore_index=True
        )

    return predictions


def has_daily_model(commodity: str) -> bool:
    """Check if a daily model exists for a commodity."""
    safe_name = _safe_commodity_name(commodity)
    model_path = os.path.join(DAILY_MODELS_DIR, f"daily_{safe_name}.joblib")
    return os.path.exists(model_path)


def get_model_info(commodity: str) -> dict:
    """Get info about a trained daily model."""
    model_data = load_daily_model(commodity)
    if model_data is None:
        return None
    return {
        'commodity': model_data['commodity'],
        'mape': model_data['metrics']['mape'],
        'rmse': model_data['metrics']['rmse'],
        'r2': model_data['metrics']['r2'],
        'dir_accuracy': model_data['metrics']['dir_accuracy'],
        'training_rows': model_data['training_rows'],
        'trained_at': model_data.get('trained_at', 'unknown'),
    }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    # Quick test: predict first commodity found
    if os.path.exists(MERGED_FILE):
        df = pd.read_csv(MERGED_FILE)
        test_commodity = df['commodity'].iloc[0]
        print(f"\nTesting prediction for: {test_commodity}")
        preds = predict_daily(test_commodity, days=7)
        for p in preds:
            print(f"  {p['date']}: ₹{p['predicted_price']} "
                  f"[{p['confidence_low']} - {p['confidence_high']}]")
