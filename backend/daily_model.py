"""
AP Mandi Predict — Daily XGBoost Model
Industry-standard daily price prediction using XGBoost with:
- 40+ engineered features (lags, momentum, seasonality, weather, calendar, MSP, exports)
- Time-series cross-validation (expanding window, no data leakage)
- Early stopping on validation RMSE
- Per-commodity model training
- Comprehensive evaluation metrics (MAPE, RMSE, R², directional accuracy)
"""

import os
import logging
import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from datetime import datetime
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

logger = logging.getLogger(__name__)

# Paths
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BACKEND_DIR, 'daily_data')
DAILY_MODELS_DIR = os.path.join(BACKEND_DIR, 'models', 'daily')
MERGED_FILE = os.path.join(DATA_DIR, 'merged_features.csv')
TRAINING_REPORT_FILE = os.path.join(DATA_DIR, 'training_report.csv')

os.makedirs(DAILY_MODELS_DIR, exist_ok=True)

# Import AP config for seasonality, MSP, and export features
from ap_config import (
    get_msp, get_seasonality_features, get_export_features, CYCLONE_MONTHS
)

# Minimum data points required per commodity to train
MIN_TRAINING_ROWS = 50

# =============================================================================
# FEATURE ENGINEERING
# =============================================================================

# Complete list of features used by the daily model
DAILY_FEATURE_NAMES = [
    # --- Group 1: Price Lags (short-term dynamics) ---
    'price_lag_1', 'price_lag_2', 'price_lag_3',
    'price_lag_7', 'price_lag_14',

    # --- Group 2: Rolling Price Statistics ---
    'price_ma_3', 'price_ma_7', 'price_ma_14', 'price_ma_30',
    'price_std_7', 'price_std_14',

    # --- Group 3: Momentum & Price Change ---
    'momentum_1',   # price_change vs yesterday
    'momentum_3',   # price_change vs 3 days ago
    'momentum_7',   # price_change vs 7 days ago
    'price_pct_change_1',  # % change day-over-day

    # --- Group 4: Arrival Features ---
    'total_arrival_state',
    'arrival_lag_1',
    'arrival_ma_7',

    # --- Group 5: Weather Features ---
    'temp_avg', 'temperature_2m_max', 'temperature_2m_min',
    'precipitation_sum', 'rainfall_flag', 'rainfall_lag_1',
    'windspeed_10m_max',
    'cyclone_indicator',

    # --- Group 6: Calendar & Seasonality ---
    'day_of_week',     # 0=Monday ... 6=Sunday
    'week_of_year',
    'month',
    'quarter',
    'is_weekend',
    'is_festival_week', 'days_to_next_festival',

    # --- Group 7: Crop Seasonality (from ap_config) ---
    'is_kharif_harvest', 'is_rabi_harvest', 'is_lean_season',

    # --- Group 8: MSP ---
    'msp', 'price_vs_msp_ratio',

    # --- Group 9: Export Demand ---
    'is_export_crop', 'is_export_season',
]


def engineer_features(df: pd.DataFrame, commodity: str) -> pd.DataFrame:
    """
    Create the full feature set for a single commodity's data.
    Expects df sorted by date with columns: date, modal_price, and
    optionally all merged feature columns.

    Args:
        df: DataFrame for one commodity, sorted by date.
        commodity: Commodity name for MSP/seasonality lookup.

    Returns:
        DataFrame with all DAILY_FEATURE_NAMES columns added.
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values('date', inplace=True)
    df.reset_index(drop=True, inplace=True)

    # ---- Group 1: Price Lags ----
    for lag in [1, 2, 3, 7, 14]:
        df[f'price_lag_{lag}'] = df['modal_price'].shift(lag)

    # ---- Group 2: Rolling Price Statistics ----
    for window in [3, 7, 14, 30]:
        df[f'price_ma_{window}'] = df['modal_price'].shift(1).rolling(
            window=window, min_periods=1
        ).mean()

    df['price_std_7'] = df['modal_price'].shift(1).rolling(
        window=7, min_periods=2
    ).std()

    df['price_std_14'] = df['modal_price'].shift(1).rolling(
        window=14, min_periods=2
    ).std()

    # ---- Group 3: Momentum ----
    df['momentum_1'] = df['modal_price'] - df['modal_price'].shift(1)
    df['momentum_3'] = df['modal_price'] - df['modal_price'].shift(3)
    df['momentum_7'] = df['modal_price'] - df['modal_price'].shift(7)

    df['price_pct_change_1'] = df['modal_price'].pct_change(1) * 100

    # ---- Group 4: Arrival Features ----
    if 'total_arrival_state' not in df.columns:
        df['total_arrival_state'] = 0.0

    df['arrival_lag_1'] = df['total_arrival_state'].shift(1)

    df['arrival_ma_7'] = df['total_arrival_state'].shift(1).rolling(
        window=7, min_periods=1
    ).mean()

    # ---- Group 5: Weather Features ----
    weather_cols = [
        'temp_avg', 'temperature_2m_max', 'temperature_2m_min',
        'precipitation_sum', 'rainfall_flag', 'windspeed_10m_max'
    ]
    for col in weather_cols:
        if col not in df.columns:
            df[col] = 0.0

    df['rainfall_lag_1'] = df['rainfall_flag'].shift(1).fillna(0)

    # Cyclone indicator: cyclone month + heavy precipitation
    df['cyclone_indicator'] = (
        (df['date'].dt.month.isin(CYCLONE_MONTHS)) &
        (df['precipitation_sum'] > 20)
    ).astype(int)

    # ---- Group 6: Calendar & Seasonality ----
    df['day_of_week'] = df['date'].dt.dayofweek
    df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
    df['month'] = df['date'].dt.month
    df['quarter'] = df['date'].dt.quarter

    if 'is_weekend' not in df.columns:
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)

    if 'is_festival_week' not in df.columns:
        df['is_festival_week'] = 0

    if 'days_to_next_festival' not in df.columns:
        df['days_to_next_festival'] = 365

    # ---- Group 7: Crop Seasonality (from ap_config) ----
    season_df = df['month'].apply(
        lambda m: pd.Series(get_seasonality_features(commodity, m))
    )
    df['is_kharif_harvest'] = season_df['is_kharif_harvest']
    df['is_rabi_harvest'] = season_df['is_rabi_harvest']
    df['is_lean_season'] = season_df['is_lean_season']

    # ---- Group 8: MSP ----
    msp_value = get_msp(commodity)
    df['msp'] = msp_value
    if msp_value > 0:
        df['price_vs_msp_ratio'] = df['modal_price'] / msp_value
    else:
        df['price_vs_msp_ratio'] = 0.0

    # ---- Group 9: Export Demand ----
    df['is_export_crop'] = get_export_features(commodity, 1)['is_export_crop']
    df['is_export_season'] = df['month'].apply(
        lambda m: get_export_features(commodity, m)['is_export_season']
    )

    # Fill remaining NaNs
    for col in DAILY_FEATURE_NAMES:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = df[col].fillna(0.0)

    return df


# =============================================================================
# TIME-SERIES CROSS-VALIDATION
# =============================================================================

def time_series_cv_split(n_samples: int, n_folds: int = 5,
                         min_train_size: int = 30):
    """
    Expanding-window time-series cross-validation.
    No shuffling, no data leakage.

    Yields (train_indices, val_indices) tuples.
    """
    fold_size = (n_samples - min_train_size) // n_folds

    if fold_size < 10:
        # Not enough data for multiple folds; use single split
        split = int(n_samples * 0.8)
        yield list(range(split)), list(range(split, n_samples))
        return

    for fold in range(n_folds):
        val_start = min_train_size + fold * fold_size
        val_end = val_start + fold_size

        if fold == n_folds - 1:
            val_end = n_samples  # Last fold takes everything remaining

        train_idx = list(range(val_start))
        val_idx = list(range(val_start, min(val_end, n_samples)))

        if len(val_idx) > 0:
            yield train_idx, val_idx


# =============================================================================
# MODEL TRAINING
# =============================================================================

def train_single_commodity(commodity: str, crop_df: pd.DataFrame,
                           verbose: bool = True) -> dict:
    """
    Train XGBoost model for a single commodity using time-series CV.

    Args:
        commodity: Crop name.
        crop_df: DataFrame for this commodity (from merged_features.csv).
        verbose: Print training progress.

    Returns:
        Dict with model, metrics, and feature importances.
    """
    # Feature engineering
    df = engineer_features(crop_df, commodity)

    # Drop rows with NaN in target or lag features (first ~14 rows)
    df = df.dropna(subset=['price_lag_1', 'price_lag_7']).copy()

    if len(df) < MIN_TRAINING_ROWS:
        if verbose:
            logger.warning(
                f"  {commodity}: only {len(df)} rows after feature eng, "
                f"need {MIN_TRAINING_ROWS}. Skipping."
            )
        return None

    # Prepare X and y
    X = df[DAILY_FEATURE_NAMES].values
    y = df['modal_price'].values
    dates = df['date'].values

    # --- Time-Series Cross-Validation ---
    cv_metrics = []

    for fold, (train_idx, val_idx) in enumerate(
        time_series_cv_split(len(X), n_folds=5)
    ):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        # XGBoost with early stopping
        dtrain = xgb.DMatrix(X_train, label=y_train,
                             feature_names=DAILY_FEATURE_NAMES)
        dval = xgb.DMatrix(X_val, label=y_val,
                           feature_names=DAILY_FEATURE_NAMES)

        params = {
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'max_depth': 8,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 5,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
            'tree_method': 'hist',
            'verbosity': 0,
        }

        model = xgb.train(
            params,
            dtrain,
            num_boost_round=1000,
            evals=[(dtrain, 'train'), (dval, 'val')],
            early_stopping_rounds=50,
            verbose_eval=False,
        )

        # Evaluate
        y_pred = model.predict(dval)
        mae = mean_absolute_error(y_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        r2 = r2_score(y_val, y_pred)
        avg_price = y_val.mean()
        mape = (mae / avg_price * 100) if avg_price > 0 else 0

        # Directional accuracy
        if len(y_val) > 1:
            actual_direction = np.diff(y_val) > 0
            pred_direction = np.diff(y_pred) > 0
            dir_accuracy = np.mean(actual_direction == pred_direction) * 100
        else:
            dir_accuracy = 0

        cv_metrics.append({
            'fold': fold,
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'mape': mape,
            'dir_accuracy': dir_accuracy,
            'best_round': model.best_iteration,
            'train_size': len(train_idx),
            'val_size': len(val_idx),
        })

    # --- Final model: train on ALL data with best_round from CV ---
    avg_best_round = int(np.mean([m['best_round'] for m in cv_metrics]))
    avg_best_round = max(avg_best_round, 50)  # Minimum 50 rounds

    dtrain_full = xgb.DMatrix(X, label=y, feature_names=DAILY_FEATURE_NAMES)

    final_model = xgb.train(
        params,
        dtrain_full,
        num_boost_round=avg_best_round,
        verbose_eval=False,
    )

    # Aggregate CV metrics
    avg_metrics = {
        'mae': np.mean([m['mae'] for m in cv_metrics]),
        'rmse': np.mean([m['rmse'] for m in cv_metrics]),
        'r2': np.mean([m['r2'] for m in cv_metrics]),
        'mape': np.mean([m['mape'] for m in cv_metrics]),
        'dir_accuracy': np.mean([m['dir_accuracy'] for m in cv_metrics]),
    }

    # Feature importance
    importance = final_model.get_score(importance_type='gain')
    # Map feature indices back to names if needed
    importance_named = {}
    for key, val in importance.items():
        if key.startswith('f') and key[1:].isdigit():
            idx = int(key[1:])
            if idx < len(DAILY_FEATURE_NAMES):
                importance_named[DAILY_FEATURE_NAMES[idx]] = val
        else:
            importance_named[key] = val

    top_features = sorted(importance_named.items(), key=lambda x: x[1], reverse=True)[:10]

    if verbose:
        logger.info(f"  {commodity}: {len(df)} rows | "
                     f"MAPE: {avg_metrics['mape']:.1f}% | "
                     f"RMSE: ₹{avg_metrics['rmse']:.0f} | "
                     f"R²: {avg_metrics['r2']:.3f} | "
                     f"Dir: {avg_metrics['dir_accuracy']:.0f}% | "
                     f"Rounds: {avg_best_round}")
        logger.info(f"    Top features: {', '.join([f'{n}({v:.0f})' for n, v in top_features[:5]])}")

    return {
        'model': final_model,
        'metrics': avg_metrics,
        'cv_details': cv_metrics,
        'features': DAILY_FEATURE_NAMES,
        'commodity': commodity,
        'training_rows': len(df),
        'best_round': avg_best_round,
        'feature_importance': dict(top_features),
        'trained_at': datetime.now().isoformat(),
    }


def train_all_daily_models(verbose: bool = True) -> dict:
    """
    Train XGBoost daily models for ALL commodities in merged_features.csv.

    Returns:
        Dict with training summary and per-commodity metrics.
    """
    if not os.path.exists(MERGED_FILE):
        logger.error(f"Merged features not found: {MERGED_FILE}")
        logger.info("Run the daily data pipeline first: update_daily_data()")
        return {"error": "No merged_features.csv found"}

    logger.info("=" * 70)
    logger.info("DAILY MODEL TRAINING — XGBoost per Commodity")
    logger.info("=" * 70)

    df = pd.read_csv(MERGED_FILE)
    df['date'] = pd.to_datetime(df['date'])

    commodities = df['commodity'].unique().tolist()
    logger.info(f"Found {len(commodities)} commodities to train")

    results = []
    trained_count = 0
    skipped_count = 0

    for commodity in commodities:
        crop_df = df[df['commodity'] == commodity].copy()

        if len(crop_df) < MIN_TRAINING_ROWS:
            if verbose:
                logger.info(f"  SKIP {commodity}: {len(crop_df)} rows < {MIN_TRAINING_ROWS}")
            skipped_count += 1
            continue

        result = train_single_commodity(commodity, crop_df, verbose=verbose)

        if result is None:
            skipped_count += 1
            continue

        # Save model
        safe_name = (commodity.replace("/", "_").replace("\\", "_")
                     .replace(":", "_").replace("(", "_").replace(")", "_")
                     .replace(" ", "_"))
        model_path = os.path.join(DAILY_MODELS_DIR, f"daily_{safe_name}.joblib")

        joblib.dump(result, model_path)

        results.append({
            'commodity': commodity,
            'mape': result['metrics']['mape'],
            'rmse': result['metrics']['rmse'],
            'r2': result['metrics']['r2'],
            'dir_accuracy': result['metrics']['dir_accuracy'],
            'rows': result['training_rows'],
            'model_path': model_path,
        })

        trained_count += 1

    # Save training report
    if results:
        report_df = pd.DataFrame(results)
        report_df.sort_values('mape', inplace=True)
        report_df.to_csv(TRAINING_REPORT_FILE, index=False)

        logger.info("\n" + "=" * 70)
        logger.info("TRAINING SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Trained: {trained_count} | Skipped: {skipped_count}")
        logger.info(f"Average MAPE: {report_df['mape'].mean():.1f}%")
        logger.info(f"Average R²: {report_df['r2'].mean():.3f}")
        logger.info(f"Average Dir Accuracy: {report_df['dir_accuracy'].mean():.0f}%")
        logger.info(f"\nBest performers:")
        for _, row in report_df.head(5).iterrows():
            logger.info(f"  {row['commodity']}: MAPE {row['mape']:.1f}% | "
                         f"R² {row['r2']:.3f} | Dir {row['dir_accuracy']:.0f}%")
        logger.info(f"\nReport saved: {TRAINING_REPORT_FILE}")

    return {
        "trained": trained_count,
        "skipped": skipped_count,
        "avg_mape": round(report_df['mape'].mean(), 2) if results else None,
        "avg_r2": round(report_df['r2'].mean(), 3) if results else None,
        "report_path": TRAINING_REPORT_FILE,
    }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    train_all_daily_models()
