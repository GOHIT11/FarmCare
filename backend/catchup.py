import os
import threading
import logging
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def run_catchup_in_background():
    """Starts the catch-up process in a background thread so it doesn't block server startup."""
    thread = threading.Thread(target=_perform_catchup)
    thread.daemon = True
    thread.start()

def _perform_catchup():
    logger.info("=== STARTUP CATCH-UP INITIATED ===")
    
    # Quick connectivity check to avoid slow timeout loops if offline or OGD is down
    import requests
    try:
        requests.get("https://api.data.gov.in", timeout=3)
    except Exception as e:
        logger.warning(f"OGD API is offline or unreachable: {e}. Skipping startup catch-up data fetching.")
        logger.info("=== STARTUP CATCH-UP COMPLETE (OFFLINE) ===")
        return
        
    # 1. Check how many days we are behind
    prices_file = os.path.join(os.path.dirname(__file__), 'daily_data', 'prices.csv')
    
    days_to_fetch = 30 # Default safety fallback if file is missing
    last_date = None
    
    if os.path.exists(prices_file):
        try:
            df = pd.read_csv(prices_file)
            if not df.empty and 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                last_date = df['date'].max()
                
                # Use naive datetime to avoid offset-naive and offset-aware issues
                now = datetime.now().replace(tzinfo=None)
                last_dt = last_date.replace(tzinfo=None)
                
                days_behind = (now - last_dt).days
                if days_behind > 0:
                    days_to_fetch = min(days_behind + 1, 60) # Fetch up to 60 days
                else:
                    days_to_fetch = 0
        except Exception as e:
            logger.error(f"Error reading prices.csv during catch-up: {e}")
            
    if days_to_fetch <= 0:
        logger.info("Database is up to date. No catch-up needed.")
        return
        
    logger.info(f"Database is {days_to_fetch} days behind (Last date: {last_date.date() if last_date else 'None'}). Fetching missing data...")
    
    try:
        # 1. Update Core Prices (mandi_data.csv) from OGD
        logger.info(f"Step 1: Fetching {days_to_fetch} days of OGD price data...")
        from ogd_service import OGDService
        service = OGDService()
        service.update_database(days_history=days_to_fetch)
        
        # 2. Regenerate prices.csv
        logger.info("Step 2: Regenerating prices.csv...")
        from services.feature_engineering import generate_prices_csv, merge_features
        generate_prices_csv()
        
        # 3. Fetch missing daily context (Arrivals, Weather, Calendar) for each day
        logger.info("Step 3: Fetching contextual features for missing days...")
        from services.arrivals_service import update_arrivals
        from services.weather_service import update_weather
        from services.calendar_service import update_calendar
        
        start_date = last_date + timedelta(days=1) if last_date else datetime.now() - timedelta(days=days_to_fetch)
        end_date = datetime.now()
        
        current_date = start_date
        while current_date.date() <= end_date.date():
            logger.info(f"  Fetching context for {current_date.date()}...")
            try:
                update_arrivals(current_date)
            except Exception as e:
                logger.warning(f"  Arrivals fetch failed for {current_date.date()}: {e}")
            
            try:
                update_weather(current_date)
            except Exception as e:
                logger.warning(f"  Weather fetch failed for {current_date.date()}: {e}")
                
            try:
                update_calendar(current_date)
            except Exception as e:
                logger.warning(f"  Calendar fetch failed for {current_date.date()}: {e}")
                
            current_date += timedelta(days=1)
            
        # 4. Merge all features
        logger.info("Step 4: Merging features...")
        merge_features()
        
        # 5. Retrain Models
        logger.info("Step 5: Retraining daily ML models...")
        from daily_model import train_all_daily_models
        train_all_daily_models(verbose=False)
        
        # 6. Clear Caches
        logger.info("Step 6: Refreshing app caches...")
        try:
            from daily_predictor import _daily_model_cache
            _daily_model_cache.clear()
        except ImportError:
            pass
            
        try:
            from model_utils import DataLoader
            DataLoader._cached_df = None
        except ImportError:
            pass
            
        logger.info("=== STARTUP CATCH-UP COMPLETE ===")
        
    except Exception as e:
        logger.error(f"Catch-up pipeline failed: {e}")
