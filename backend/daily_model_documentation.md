# API and Feature Documentation: Daily Prediction Model

## Architecture: Core Concept

An industry-standard XGBoost daily price prediction system replacing the old RandomForest seasonal model.

### Modified & New Files

| File | Purpose |
|------|---------|
| `daily_model.py` | XGBoost training pipeline (40+ features, time-series CV, early stopping) |
| `daily_predictor.py` | Prediction engine (multi-step, confidence intervals) |
| `main.py` | `_get_future_prices` now tries **daily XGBoost first**, falls back to legacy. Added `/train_daily`, `/model_info` endpoints |

---

## Feature Groups (40+ Engineered Features)

| Group | Features |
|-------|----------|
| **Price Lags** | `price_lag_1, lag_2, lag_3, lag_7, lag_14` |
| **Rolling Stats** | `price_ma_3, ma_7, ma_14, ma_30, std_7, std_14` |
| **Momentum** | `momentum_1, momentum_3, momentum_7, pct_change_1` |
| **Arrivals** | `total_arrival_state, arrival_lag_1, arrival_ma_7` |
| **Weather** | `temp_avg, temp_max, temp_min, precip, rainfall_flag, rainfall_lag_1, windspeed, cyclone` |
| **Calendar** | `day_of_week, week_of_year, month, quarter, is_weekend, is_festival_week, days_to_next_festival` |
| **Crop Season** | `is_kharif_harvest, is_rabi_harvest, is_lean_season` |
| **MSP** | `msp, price_vs_msp_ratio` |
| **Export** | `is_export_crop, is_export_season` |

---

## Initial Training Results

| Metric | Value |
|--------|-------|
| **Models Trained** | 53 |
| **Average MAPE** | 7.95% |
| **Directional Accuracy** | 85.7% |
| Models with MAPE < 5% | 20 |
| Models with MAPE < 8% | 32 |
| Models with R² > 0.85 | 5 |

---

## Architecture: Prediction Priority Flow

1. **`/predict` or `/dashboard` request**
2. **Check:** Daily XGBoost model exists?
   - **Yes:** Use `daily_predictor.predict_daily` (returns predictions with confidence intervals)
   - **No:** Check legacy RF model exists?
     - **Yes:** Use old `model_utils` prediction
     - **No:** Use smart fallback estimation

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/update_daily` | POST | Runs the data pipeline. Fetches new arrivals, weather, and calendar data, merging them into `daily_data/merged_features.csv` |
| `/train_daily` | POST | Train XGBoost models for all commodities. Uses data from `merged_features.csv`. Run this right after `/update_daily`. |
| `/model_info` | GET | View training metrics (all or per commodity) |
| `/predict` | POST | Get predictions (auto-uses daily model) |
| `/dashboard` | POST | Dashboard predictions (auto-uses daily model) |

---

## How to Use & Operations

```bash
# 1. Run daily data pipeline + train models
curl -X POST http://localhost:8000/update_daily
curl -X POST http://localhost:8000/train_daily

# 2. Check model quality
curl http://localhost:8000/model_info

# 3. Predictions auto-use daily model now
curl -X POST http://localhost:8000/predict -d '{"mandi":"...", "commodity":"Tomato"}'
```
