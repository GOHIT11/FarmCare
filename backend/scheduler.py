"""
AP Mandi Predict — Automated Daily Scheduler
Runs the full data pipeline automatically every day at scheduled times.

Schedule (IST):
  11:30 AM → Fetch previous day data (arrivals, weather, calendar)
  11:32 AM → Validate data completeness
  11:35 AM → Run feature engineering (merge all sources)
  11:40 AM → Train/update models & generate predictions
  11:45 AM → Refresh prediction cache for dashboard/app
"""

import os
import logging
import pandas as pd
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

logger = logging.getLogger(__name__)

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BACKEND_DIR, 'daily_data')

# Timezone from .env (default: Asia/Kolkata)
TIMEZONE = os.getenv('AP_TIMEZONE', 'Asia/Kolkata')

# Pipeline status (shared across steps)
_pipeline_status = {
    "last_run": None,
    "status": "idle",
    "steps": {},
}


def get_pipeline_status() -> dict:
    """Returns the current pipeline status for API access."""
    return _pipeline_status.copy()


# =============================================================================
# STEP 1: Fetch Previous Day Data (11:30 AM)
# =============================================================================

def step_1_fetch_data():
    """Fetch arrivals, weather, and calendar data for the previous day."""
    logger.info("=" * 60)
    logger.info("SCHEDULER STEP 1/5: Fetching previous day data...")
    logger.info("=" * 60)

    _pipeline_status["status"] = "running"
    _pipeline_status["last_run"] = datetime.now().isoformat()
    step_result = {"status": "started", "timestamp": datetime.now().isoformat()}

    try:
        yesterday = datetime.now() - timedelta(days=1)

        # 1a. Fetch OGD Prices (Core Data)
        try:
            from ogd_service import OGDService
            service = OGDService()
            service.update_database(days_history=3) # Safely fetch last 3 days to catch delayed govt entries
            step_result["ogd_prices"] = "success"
            logger.info("  OGD Prices: updated")
        except Exception as e:
            step_result["ogd_prices"] = f"error: {e}"
            logger.error(f"  OGD Prices failed: {e}")

        # 1b. Fetch arrivals
        try:
            from services.arrivals_service import update_arrivals
            arrivals_df = update_arrivals(yesterday)
            step_result["arrivals"] = f"success ({len(arrivals_df)} rows)"
            logger.info(f"  Arrivals: {len(arrivals_df)} rows fetched")
        except Exception as e:
            step_result["arrivals"] = f"error: {e}"
            logger.error(f"  Arrivals failed: {e}")

        # 1b. Fetch weather
        try:
            from services.weather_service import update_weather
            weather_df = update_weather(yesterday)
            step_result["weather"] = f"success ({len(weather_df)} rows)"
            logger.info(f"  Weather: {len(weather_df)} rows fetched")
        except Exception as e:
            step_result["weather"] = f"error: {e}"
            logger.error(f"  Weather failed: {e}")

        # 1c. Fetch calendar/holidays
        try:
            from services.calendar_service import update_calendar
            calendar_df = update_calendar(yesterday)
            step_result["calendar"] = f"success ({len(calendar_df)} rows)"
            logger.info(f"  Calendar: {len(calendar_df)} rows fetched")
        except Exception as e:
            step_result["calendar"] = f"error: {e}"
            logger.error(f"  Calendar failed: {e}")

        step_result["status"] = "completed"

    except Exception as e:
        step_result["status"] = f"failed: {e}"
        logger.error(f"Step 1 failed: {e}")

    _pipeline_status["steps"]["fetch_data"] = step_result
    logger.info(f"Step 1 complete: {step_result['status']}")


# =============================================================================
# STEP 2: Validate Data Completeness (11:32 AM)
# =============================================================================

def step_2_validate_data():
    """Check that all CSV files have recent data and no gaps."""
    logger.info("=" * 60)
    logger.info("SCHEDULER STEP 2/5: Validating data completeness...")
    logger.info("=" * 60)

    step_result = {"status": "started", "timestamp": datetime.now().isoformat()}

    try:
        files_to_check = {
            'arrivals.csv': ['date', 'total_arrival_state'],
            'weather.csv': ['date', 'temp_avg', 'rainfall_flag'],
            'calendar_features.csv': ['date', 'is_weekend'],
        }

        all_valid = True

        for filename, required_cols in files_to_check.items():
            filepath = os.path.join(DATA_DIR, filename)

            if not os.path.exists(filepath):
                step_result[filename] = "MISSING"
                logger.warning(f"  {filename}: FILE MISSING")
                all_valid = False
                continue

            df = pd.read_csv(filepath)
            row_count = len(df)

            # Check required columns
            missing_cols = [c for c in required_cols if c not in df.columns]
            if missing_cols:
                step_result[filename] = f"MISSING COLUMNS: {missing_cols}"
                logger.warning(f"  {filename}: missing columns {missing_cols}")
                all_valid = False
                continue

            # Check recency (last date should be within 2 days)
            df['date'] = pd.to_datetime(df['date'])
            latest = df['date'].max()
            days_old = (datetime.now() - latest).days

            if days_old > 3:
                step_result[filename] = f"STALE (last: {latest.date()}, {days_old} days old)"
                logger.warning(f"  {filename}: stale data, last date {latest.date()}")
            else:
                step_result[filename] = f"OK ({row_count} rows, latest: {latest.date()})"
                logger.info(f"  {filename}: OK ({row_count} rows, latest: {latest.date()})")

        # Check mandi_data.csv (master file)
        master_path = os.path.join(BACKEND_DIR, 'mandi_data.csv')
        if os.path.exists(master_path):
            master_df = pd.read_csv(master_path)
            step_result['mandi_data.csv'] = f"OK ({len(master_df)} rows)"
        else:
            step_result['mandi_data.csv'] = "MISSING"
            all_valid = False

        step_result["status"] = "valid" if all_valid else "warnings"

    except Exception as e:
        step_result["status"] = f"failed: {e}"
        logger.error(f"Step 2 failed: {e}")

    _pipeline_status["steps"]["validate_data"] = step_result
    logger.info(f"Step 2 complete: {step_result['status']}")


# =============================================================================
# STEP 3: Feature Engineering (11:35 AM)
# =============================================================================

def step_3_feature_engineering():
    """Merge all data sources and create ML-ready features."""
    logger.info("=" * 60)
    logger.info("SCHEDULER STEP 3/5: Running feature engineering...")
    logger.info("=" * 60)

    step_result = {"status": "started", "timestamp": datetime.now().isoformat()}

    try:
        from services.feature_engineering import generate_prices_csv, merge_features

        # Regenerate prices.csv from mandi_data
        prices_df = generate_prices_csv()
        step_result["prices_rows"] = len(prices_df)
        logger.info(f"  Generated prices.csv: {len(prices_df)} rows")

        # Merge all features
        merged_df = merge_features()
        step_result["merged_rows"] = len(merged_df)
        step_result["merged_columns"] = len(merged_df.columns)
        logger.info(f"  Merged features: {len(merged_df)} rows × {len(merged_df.columns)} columns")

        step_result["status"] = "completed"

    except Exception as e:
        step_result["status"] = f"failed: {e}"
        logger.error(f"Step 3 failed: {e}")

    _pipeline_status["steps"]["feature_engineering"] = step_result
    logger.info(f"Step 3 complete: {step_result['status']}")


# =============================================================================
# STEP 4: Train Models & Generate Predictions (11:40 AM)
# =============================================================================

def step_4_train_and_predict():
    """Retrain XGBoost daily models with latest data."""
    logger.info("=" * 60)
    logger.info("SCHEDULER STEP 4/5: Training models & generating predictions...")
    logger.info("=" * 60)

    step_result = {"status": "started", "timestamp": datetime.now().isoformat()}

    try:
        from daily_model import train_all_daily_models

        results = train_all_daily_models(verbose=True)
        step_result["trained"] = results.get("trained", 0)
        step_result["skipped"] = results.get("skipped", 0)
        step_result["avg_mape"] = results.get("avg_mape", None)
        step_result["avg_r2"] = results.get("avg_r2", None)

        logger.info(f"  Trained: {step_result['trained']} models")
        logger.info(f"  Avg MAPE: {step_result['avg_mape']}")

        step_result["status"] = "completed"

    except Exception as e:
        step_result["status"] = f"failed: {e}"
        logger.error(f"Step 4 failed: {e}")

    _pipeline_status["steps"]["train_predict"] = step_result
    logger.info(f"Step 4 complete: {step_result['status']}")


# =============================================================================
# STEP 5: Refresh Dashboard Cache (11:45 AM)
# =============================================================================

def step_5_refresh_dashboard():
    """Clear caches so the app serves fresh predictions."""
    logger.info("=" * 60)
    logger.info("SCHEDULER STEP 5/5: Refreshing dashboard & app caches...")
    logger.info("=" * 60)

    step_result = {"status": "started", "timestamp": datetime.now().isoformat()}

    try:
        # Clear the model cache so daily_predictor reloads updated models
        from daily_predictor import _daily_model_cache
        _daily_model_cache.clear()
        logger.info("  Cleared daily model cache")

        # Invalidate DataLoader cache so fresh data is used
        from model_utils import DataLoader
        DataLoader._cached_df = None
        logger.info("  Invalidated DataLoader cache")

        step_result["status"] = "completed"
        _pipeline_status["status"] = "completed"
        _pipeline_status["completed_at"] = datetime.now().isoformat()

        logger.info("=" * 60)
        logger.info("DAILY PIPELINE COMPLETE — App is serving fresh predictions!")
        logger.info("=" * 60)

    except Exception as e:
        step_result["status"] = f"failed: {e}"
        logger.error(f"Step 5 failed: {e}")
        _pipeline_status["status"] = "completed_with_errors"

    _pipeline_status["steps"]["refresh_dashboard"] = step_result


# =============================================================================
# SCHEDULER SETUP
# =============================================================================

_scheduler = None


def start_scheduler():
    """
    Start the background scheduler with the 5-step daily pipeline.

    Schedule (IST daily):
      11:30 AM → Step 1: Fetch data
      11:32 AM → Step 2: Validate
      11:35 AM → Step 3: Feature engineering
      11:40 AM → Step 4: Train & predict
      11:45 AM → Step 5: Refresh dashboard
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("Scheduler already running. Skipping start.")
        return

    _scheduler = BackgroundScheduler(timezone=TIMEZONE)

    # Step 1: 11:30 AM — Fetch data
    _scheduler.add_job(
        step_1_fetch_data,
        trigger=CronTrigger(hour=11, minute=30, timezone=TIMEZONE),
        id='daily_step_1_fetch',
        name='Daily Step 1: Fetch Data',
        replace_existing=True,
    )

    # Step 2: 11:32 AM — Validate
    _scheduler.add_job(
        step_2_validate_data,
        trigger=CronTrigger(hour=11, minute=32, timezone=TIMEZONE),
        id='daily_step_2_validate',
        name='Daily Step 2: Validate Data',
        replace_existing=True,
    )

    # Step 3: 11:35 AM — Feature engineering
    _scheduler.add_job(
        step_3_feature_engineering,
        trigger=CronTrigger(hour=11, minute=35, timezone=TIMEZONE),
        id='daily_step_3_features',
        name='Daily Step 3: Feature Engineering',
        replace_existing=True,
    )

    # Step 4: 11:40 AM — Train & predict
    _scheduler.add_job(
        step_4_train_and_predict,
        trigger=CronTrigger(hour=11, minute=40, timezone=TIMEZONE),
        id='daily_step_4_train',
        name='Daily Step 4: Train & Predict',
        replace_existing=True,
    )

    # Step 5: 11:45 AM — Refresh dashboard
    _scheduler.add_job(
        step_5_refresh_dashboard,
        trigger=CronTrigger(hour=11, minute=45, timezone=TIMEZONE),
        id='daily_step_5_refresh',
        name='Daily Step 5: Refresh Dashboard',
        replace_existing=True,
    )

    _scheduler.start()

    logger.info("=" * 60)
    logger.info("DAILY SCHEDULER STARTED")
    logger.info(f"  Timezone: {TIMEZONE}")
    logger.info("  11:30 AM → Fetch previous day data")
    logger.info("  11:32 AM → Validate data completeness")
    logger.info("  11:35 AM → Run feature engineering")
    logger.info("  11:40 AM → Train models & generate predictions")
    logger.info("  11:45 AM → Refresh dashboard/app caches")
    logger.info("=" * 60)


def stop_scheduler():
    """Stop the background scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Daily scheduler stopped.")


def get_next_run_times() -> list:
    """Get the next scheduled run times for all jobs."""
    if _scheduler is None:
        return []

    return [
        {
            "job": job.name,
            "next_run": str(job.next_run_time),
        }
        for job in _scheduler.get_jobs()
    ]
