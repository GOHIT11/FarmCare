"""
AP Mandi Predict - ML Model Utilities
Per-crop model training with 6 advanced features:
1. State-level arrivals (total AP arrivals per crop)
2. Seasonality (month, quarter, kharif/rabi/lean)
3. Weather (rainfall, temp deviation, cyclone indicator)
4. MSP (price vs MSP ratio)
5. Price trend lags (t-1, t-7, MA-7, MA-14, volatility)
6. Export demand (export crop flag, export season)
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import os

from ap_config import (
    get_msp, get_seasonality_features, get_export_features,
    AP_STATE_CENTER, CYCLONE_MONTHS
)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)


class DataLoader:
    """Loads and caches mandi_data.csv, filtered to AP only."""
    _cached_df = None

    def __init__(self, filepath=None):
        if filepath is None:
            self.filepath = os.path.join(os.path.dirname(__file__), "mandi_data.csv")
        else:
            self.filepath = filepath

    def load_data(self):
        if DataLoader._cached_df is not None:
            return DataLoader._cached_df.copy()

        print(f"Loading data from {self.filepath}...")
        try:
            df = pd.read_csv(self.filepath)
            df['date'] = pd.to_datetime(df['date'])
        except FileNotFoundError:
            print(f"Warning: {self.filepath} not found. Returning empty DataFrame.")
            empty_df = pd.DataFrame(columns=['date', 'mandi', 'commodity', 'modal_price', 'arrivals', 'state'])
            DataLoader._cached_df = empty_df
            return empty_df.copy()

        # Filter to AP only
        if 'state' in df.columns:
            df = df[df['state'] == 'Andhra Pradesh'].copy()
            print(f"Filtered to AP: {len(df)} rows")

        # Fill missing modal_price forward
        df.sort_values(by=['mandi', 'commodity', 'date'], inplace=True)
        df['modal_price'] = df.groupby(['mandi', 'commodity'])['modal_price'].ffill()

        # Ensure arrivals column exists
        if 'arrivals' not in df.columns:
            df['arrivals'] = 0

        DataLoader._cached_df = df
        return df.copy()

    def invalidate_cache(self):
        """Force reload on next call."""
        DataLoader._cached_df = None

    def filter_data(self, df, mandi, commodity):
        mask = (df['mandi'] == mandi) & (df['commodity'] == commodity)
        return df[mask].copy()

    def get_crop_data(self, df, commodity):
        """Get ALL AP data for a single crop (across all mandis)."""
        mask = df['commodity'] == commodity
        return df[mask].copy()


class FeatureEngineer:
    """Creates feature set with 6 advanced factors for AP crop prediction."""

    # The full feature list used during training and prediction
    FEATURE_NAMES = [
        # Factor 1: State-level arrivals
        'state_total_arrivals',
        'state_arrivals_ma7',

        # Factor 2: Seasonality
        'month', 'quarter', 'day_of_week',
        'is_kharif_harvest', 'is_rabi_harvest', 'is_lean_season',

        # Factor 3: Weather
        'temp_avg', 'humidity', 'rain_mm', 'cyclone_indicator',

        # Factor 4: MSP
        'msp', 'price_vs_msp_ratio',

        # Factor 5: Price trend lags
        'lag_price_1', 'lag_price_2', 'lag_price_3', 'lag_price_7',
        'ma_7day', 'ma_14day', 'price_volatility_7d',
        'lag_arrivals_1', 'lag_arrivals_7',
        'avg_arrivals_7',

        # Factor 6: Export demand
        'is_export_crop', 'is_export_season',
    ]

    def compute_state_arrivals(self, full_df, commodity):
        """
        Factor 1: Aggregate total AP arrivals per day for this crop.
        Returns a Series indexed by date.
        """
        crop_df = full_df[full_df['commodity'] == commodity].copy()
        if crop_df.empty or 'arrivals' not in crop_df.columns:
            return pd.Series(dtype=float)
        state_arrivals = crop_df.groupby('date')['arrivals'].sum()
        return state_arrivals

    def create_features(self, df, commodity, full_df=None, is_training=True):
        """
        Creates feature set for a single crop.
        df: DataFrame for this specific crop (all mandis or specific mandi), sorted by date.
        commodity: crop name for seasonality/MSP lookup.
        full_df: Full AP dataset for computing state-level arrivals.
        """
        df = df.copy()

        # --- Factor 1: State-level arrivals ---
        if full_df is not None:
            state_arrivals = self.compute_state_arrivals(full_df, commodity)
            df['state_total_arrivals'] = df['date'].map(state_arrivals).fillna(0)
        else:
            df['state_total_arrivals'] = df['arrivals'] if 'arrivals' in df.columns else 0

        df['state_arrivals_ma7'] = df['state_total_arrivals'].shift(1).rolling(window=7).mean()

        # --- Factor 2: Seasonality ---
        df['month'] = df['date'].dt.month
        df['day_of_week'] = df['date'].dt.dayofweek

        # Get seasonality features per row
        season_features = df['month'].apply(
            lambda m: pd.Series(get_seasonality_features(commodity, m))
        )
        df['quarter'] = season_features['quarter']
        df['is_kharif_harvest'] = season_features['is_kharif_harvest']
        df['is_rabi_harvest'] = season_features['is_rabi_harvest']
        df['is_lean_season'] = season_features['is_lean_season']

        # --- Factor 3: Weather ---
        if 'temp_avg' not in df.columns:
            df['temp_avg'] = 0
        if 'humidity' not in df.columns:
            df['humidity'] = 0
        if 'rain_mm' not in df.columns:
            df['rain_mm'] = 0
        # Cyclone indicator: 1 if in cyclone month AND heavy rain
        df['cyclone_indicator'] = (
            (df['month'].isin(CYCLONE_MONTHS)) & (df['rain_mm'] > 20)
        ).astype(int)

        # --- Factor 4: MSP ---
        msp_value = get_msp(commodity)
        df['msp'] = msp_value
        if msp_value > 0:
            df['price_vs_msp_ratio'] = df['modal_price'] / msp_value
        else:
            df['price_vs_msp_ratio'] = 0

        # --- Factor 5: Price trend lags ---
        df['lag_price_1'] = df['modal_price'].shift(1)
        df['lag_price_2'] = df['modal_price'].shift(2)
        df['lag_price_3'] = df['modal_price'].shift(3)
        df['lag_price_7'] = df['modal_price'].shift(7)
        df['ma_7day'] = df['modal_price'].shift(1).rolling(window=7).mean()
        df['ma_14day'] = df['modal_price'].shift(1).rolling(window=14).mean()
        df['price_volatility_7d'] = df['modal_price'].shift(1).rolling(window=7).std()

        # Arrival lags
        if 'arrivals' not in df.columns:
            df['arrivals'] = 0
        df['lag_arrivals_1'] = df['arrivals'].shift(1)
        df['lag_arrivals_7'] = df['arrivals'].shift(7)
        df['avg_arrivals_7'] = df['arrivals'].shift(1).rolling(window=7).mean()

        # --- Factor 6: Export demand ---
        export_features = get_export_features(commodity, df['month'].iloc[-1] if len(df) > 0 else 1)
        df['is_export_crop'] = export_features['is_export_crop']
        # Per-row export season
        df['is_export_season'] = df['month'].apply(
            lambda m: get_export_features(commodity, m)['is_export_season']
        )

        # Drop NaN rows from shifts (only during training)
        if is_training:
            df.dropna(inplace=True)

        return df

    def prepare_features_for_prediction(self, history_df, weather_forecast=None,
                                         commodity=None, full_df=None):
        """
        Constructs a SINGLE feature row for next-day prediction.
        history_df: DataFrame containing past data up to T-1.
        weather_forecast: dict with 'temp_avg', 'humidity', 'rain_mm'
        commodity: crop name for seasonality/MSP/export lookup
        full_df: Full AP dataset for state-level arrivals
        """
        last_date = history_df['date'].max()
        target_date = last_date + pd.Timedelta(days=1)
        month = target_date.month

        # --- Factor 1: State arrivals ---
        state_total = 0
        state_ma7 = 0
        if full_df is not None and commodity:
            state_arrivals = self.compute_state_arrivals(full_df, commodity)
            # Use last known state arrivals
            recent_state = state_arrivals.tail(7)
            state_total = recent_state.iloc[-1] if len(recent_state) > 0 else 0
            state_ma7 = recent_state.mean() if len(recent_state) > 0 else 0

        # --- Factor 2: Seasonality ---
        season = get_seasonality_features(commodity or "", month)

        # --- Factor 3: Weather ---
        temp_avg = weather_forecast.get('temp_avg', 0) if weather_forecast else 0
        humidity = weather_forecast.get('humidity', 0) if weather_forecast else 0
        rain_mm = weather_forecast.get('rain_mm', 0) if weather_forecast else 0
        cyclone = 1 if (month in CYCLONE_MONTHS and rain_mm > 20) else 0

        # --- Factor 4: MSP ---
        msp_value = get_msp(commodity or "")
        last_price = history_df['modal_price'].iloc[-1]
        price_vs_msp = (last_price / msp_value) if msp_value > 0 else 0

        # --- Factor 5: Price lags ---
        p_last = history_df['modal_price'].iloc[-1]
        p_lag2 = history_df['modal_price'].iloc[-2] if len(history_df) >= 2 else p_last
        p_lag3 = history_df['modal_price'].iloc[-3] if len(history_df) >= 3 else p_last
        p_lag7 = history_df['modal_price'].iloc[-7] if len(history_df) >= 7 else p_last
        ma_7 = history_df['modal_price'].tail(7).mean()
        ma_14 = history_df['modal_price'].tail(14).mean()
        volatility = history_df['modal_price'].tail(7).std()
        if pd.isna(volatility):
            volatility = 0

        arrivals_col = history_df['arrivals'] if 'arrivals' in history_df.columns else pd.Series([0]*len(history_df))
        a_last = arrivals_col.iloc[-1] if len(arrivals_col) > 0 else 0
        a_lag7 = arrivals_col.iloc[-7] if len(arrivals_col) >= 7 else a_last
        avg_a7 = arrivals_col.tail(7).mean()

        # --- Factor 6: Export ---
        export = get_export_features(commodity or "", month)

        row = {
            'state_total_arrivals': state_total,
            'state_arrivals_ma7': state_ma7,
            'month': month,
            'quarter': season['quarter'],
            'day_of_week': target_date.dayofweek,
            'is_kharif_harvest': season['is_kharif_harvest'],
            'is_rabi_harvest': season['is_rabi_harvest'],
            'is_lean_season': season['is_lean_season'],
            'temp_avg': temp_avg,
            'humidity': humidity,
            'rain_mm': rain_mm,
            'cyclone_indicator': cyclone,
            'msp': msp_value,
            'price_vs_msp_ratio': price_vs_msp,
            'lag_price_1': p_last,
            'lag_price_2': p_lag2,
            'lag_price_3': p_lag3,
            'lag_price_7': p_lag7,
            'ma_7day': ma_7,
            'ma_14day': ma_14,
            'price_volatility_7d': volatility,
            'lag_arrivals_1': a_last,
            'lag_arrivals_7': a_lag7,
            'avg_arrivals_7': avg_a7,
            'is_export_crop': export['is_export_crop'],
            'is_export_season': export['is_export_season'],
        }

        return pd.DataFrame([row])


def train_models():
    """
    Train one GradientBoosting model PER CROP using all AP data.
    Each crop gets its own model that learns from ALL mandis in AP.
    """
    print("Loading AP data...")
    loader = DataLoader()
    df = loader.load_data()

    if df.empty:
        print("No data found! Cannot train.")
        return

    # Get all unique crops
    crops = df['commodity'].unique().tolist()
    print(f"Found {len(crops)} unique crops to train")

    fe = FeatureEngineer()
    features = FeatureEngineer.FEATURE_NAMES
    target = 'modal_price'

    trained_count = 0
    skipped_count = 0

    for commodity in crops:
        print(f"\n{'='*60}")
        print(f"Training model for: {commodity}")

        # Get ALL AP data for this crop (across all mandis)
        crop_df = loader.get_crop_data(df, commodity)

        if crop_df.empty:
            print(f"  No data found, skipping.")
            skipped_count += 1
            continue

        # Sort by date for time-series integrity
        crop_df = crop_df.sort_values('date')

        # Add features
        train_df = fe.create_features(
            crop_df, commodity=commodity, full_df=df, is_training=True
        )

        if len(train_df) < 30:
            print(f"  Only {len(train_df)} rows after feature engineering, need at least 30. Skipping.")
            skipped_count += 1
            continue

        # Ensure all features exist
        for f in features:
            if f not in train_df.columns:
                train_df[f] = 0

        # Time-based split (80/20)
        split_idx = int(len(train_df) * 0.8)
        train = train_df.iloc[:split_idx]
        test = train_df.iloc[split_idx:]

        X_train = train[features]
        y_train = train[target]
        X_test = test[features]
        y_test = test[target]

        if len(X_train) == 0 or len(X_test) == 0:
            print(f"  Split resulted in empty set. Skipping.")
            skipped_count += 1
            continue

        # RandomForest for robust crop price prediction
        model = RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X_train, y_train)

        # Evaluate
        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        avg_price = y_test.mean()
        mape = (mae / avg_price * 100) if avg_price > 0 else 0

        print(f"  Rows: {len(train_df)}, Train: {len(train)}, Test: {len(test)}")
        print(f"  MAE: ₹{mae:.2f}, RMSE: ₹{rmse:.2f}, MAPE: {mape:.1f}%")

        # Feature importance (top 5)
        importances = pd.Series(model.feature_importances_, index=features)
        top5 = importances.nlargest(5)
        print(f"  Top features: {', '.join([f'{n}({v:.2f})' for n,v in top5.items()])}")

        # Save model
        safe_commodity = commodity.replace("/", "_").replace("\\", "_").replace(":", "_").replace("(", "_").replace(")", "_")
        model_path = os.path.join(MODELS_DIR, f"model_crop_{safe_commodity}.joblib")

        joblib.dump({
            'model': model,
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'features': features,
            'commodity': commodity,
            'training_rows': len(train_df),
        }, model_path)

        trained_count += 1
        print(f"  ✓ Saved: {model_path}")

    print(f"\n{'='*60}")
    print(f"Training Complete: {trained_count} models trained, {skipped_count} skipped")


if __name__ == "__main__":
    train_models()
