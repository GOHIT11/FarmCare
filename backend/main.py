from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import os
import datetime
import logging
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from fastapi import Depends

# Import Database tools
from database import engine, get_db, Base
from models import Farmer, Mandi, Crop
from auth import get_password_hash, verify_password, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES

# Load environment variables from .env
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# Load environment variables from .env
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

from model_utils import DataLoader, FeatureEngineer, MODELS_DIR
from weather_service import get_forecast
from ap_config import AP_STATE_CENTER, get_district_coords

from contextlib import asynccontextmanager

# Models cache: key = commodity name
loaded_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the data catch-up process in background
    from catchup import run_catchup_in_background
    run_catchup_in_background()
    
    # Start the daily auto-scheduler
    from scheduler import start_scheduler
    start_scheduler()
    logger.info("AP Mandi Predict server starting... Models loaded on demand.")
    yield
    # Shutdown scheduler on exit
    from scheduler import stop_scheduler
    stop_scheduler()
    loaded_models.clear()

app = FastAPI(title="AP Mandi Price Predictor", lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "models_loaded": len(loaded_models), "region": "Andhra Pradesh"}

from master_data import MASTER_DATA, DISTRICT_MANDIS, MANDI_TO_DISTRICT

@app.get("/options")
def get_options():
    """Returns AP-only options with district mapping."""
    import copy

    options = copy.deepcopy(MASTER_DATA) if MASTER_DATA else {}

    # Merge any real CSV data for AP only
    csv_path = os.path.join(os.path.dirname(__file__), "mandi_data.csv")
    if not os.path.exists(csv_path):
        return options

    try:
        df = pd.read_csv(csv_path)
        # Filter to AP only
        if 'state' in df.columns:
            df = df[df['state'] == 'Andhra Pradesh']

        grouped = df.groupby(['mandi'])['commodity'].unique()

        state_key = "Andhra Pradesh"
        if state_key not in options:
            options[state_key] = {}

        for mandi, comms in grouped.items():
            if mandi not in options[state_key]:
                options[state_key][mandi] = []

            current_list = set(options[state_key][mandi])
            for c in comms:
                current_list.add(c)

            options[state_key][mandi] = sorted(list(current_list))

        return options
    except Exception as e:
        print(f"Error generating options: {e}")
        return MASTER_DATA


@app.get("/districts")
def get_districts():
    """Returns district → mandi mapping for frontend cascade dropdowns."""
    return DISTRICT_MANDIS


class PredictRequest(BaseModel):
    mandi: str
    commodity: str

@app.post("/predict")
def predict(request: PredictRequest):
    preds = _get_future_prices(request.mandi, request.commodity, days=7)
    return {
        "mandi": request.mandi,
        "commodity": request.commodity,
        "currency": "INR",
        "predictions": preds,
        "meta": {
             "model_name": "ap_crop_model_v1",
             "note": "Per-crop ML model with 6 factors (arrivals, seasonality, weather, MSP, trends, export)"
        }
    }

# --- FIELD ASSISTANT CHATBOT ---
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
import google.generativeai as genai
from fastapi import File, UploadFile, Form
from typing import Optional
from PIL import Image
import io

# Configure Gemini (API key from .env)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not set in .env — chat endpoint will fail")
genai.configure(api_key=GEMINI_API_KEY)

def health_check():
    return {"status": "ok"}

import asyncio

try:
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    logger.error(f"Failed to initialize gemini-2.5-flash: {e}")
    model = None

@app.post("/chat")
async def chat_endpoint(
    message: str = Form(""),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None)
):
    try:
        system_prompt = """
        You are an expert Andhra Pradesh Farming Assistant (AP Kisan Sahayak).
        You provide practical, accurate advice for AP farmers.
        
        CRITICAL MULTILINGUAL RULES:
        - If the user asks in TELUGU (text or voice), ALWAYS reply completely in TELUGU script. 
          Example constraint: Do not mix languages.
        - If the user asks in ENGLISH, reply entirely in ENGLISH.
        
        RESPONSE FORMAT:
        1. Problem explanation
        2. Suggested solution (e.g. fertilizer, pesticide)
        3. Optional prevention tip
        
        GUIDELINES:
        - Analyze uploaded crop images to diagnose pest/disease or nutrient issues.
        - Transcribe and answer voice queries natively.
        - If image analysis confidence is low, say: "The issue may be related to nutrient deficiency. Please consult a local agriculture officer."
        - Keep answers fast, concise, and practical. Avoid long paragraphs.
        """

        prompt_parts = [system_prompt, "\nUser Question: " + message]

        if image:
            image_data = await image.read()
            img = Image.open(io.BytesIO(image_data))
            prompt_parts.append(img)
            
        if audio:
            audio_data = await audio.read()
            prompt_parts.append({"mime_type": audio.content_type or "audio/m4a", "data": audio_data})

        # Run non-blocking in thread pool with 20-second timeout
        if model:
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(model.generate_content, prompt_parts),
                    timeout=20.0
                )
                return {"response": response.text}
            except asyncio.TimeoutError:
                logger.warning("Gemini AI request timed out. Returning friendly advisory.")
                return {
                    "response": "నమస్కారం రైతు సోదరా / Hello Farmer. The AI assistant server took too long to respond. Please check your internet connection or ask again shortly."
                }
            except Exception as ai_err:
                logger.warning(f"Gemini API error ({ai_err}). Returning advisory.")
                return {
                    "response": f"AI Assistant Notice: Currently receiving high query volume. For crop health, ensure proper irrigation, balanced N-P-K fertilizer application, and consult your local Rythu Bharosa Kendra (RBK) officer."
                }
        else:
            return {"response": "AI Assistant is currently offline. Please configure GEMINI_API_KEY in .env."}

    except Exception as e:
        logger.error(f"Chat Error: {e}")
        return {"response": f"Unable to process query right now: {str(e)}"}



class OptimizeRequest(BaseModel):
    mandis: list[str]
    commodity: str
    quantity_quintal: float
    storage_days_max: int
    storage_cost_per_quintal_per_day: float
    transport_cost_per_km_per_quintal: float
    distance_to_mandi: dict[str, float]

@app.post("/optimize")
def optimize(request: OptimizeRequest):
    best_action = None
    max_profit = -float('inf')
    alternatives = []

    for mandi in request.mandis:
        prices = _get_future_prices(mandi, request.commodity, days=7)

        if not prices:
             continue

        for day_idx, p_data in enumerate(prices):
            if day_idx > request.storage_days_max:
                break

            predicted_price = p_data['predicted_price']

            revenue = predicted_price * request.quantity_quintal
            storage_cost = request.storage_cost_per_quintal_per_day * request.quantity_quintal * day_idx
            dist = request.distance_to_mandi.get(mandi, 0)
            transport_cost = request.transport_cost_per_km_per_quintal * request.quantity_quintal * dist

            net_profit = revenue - storage_cost - transport_cost

            action_summary = {
                "mandi": mandi,
                "day_offset": day_idx,
                "date": p_data['date'],
                "predicted_price": predicted_price,
                "revenue": round(revenue, 2),
                "costs": round(storage_cost + transport_cost, 2),
                "net_profit": round(net_profit, 2)
            }

            alternatives.append(action_summary)

            if net_profit > max_profit:
                max_profit = net_profit
                best_action = action_summary

    alternatives.sort(key=lambda x: x['net_profit'], reverse=True)

    rec_text = "No option found."
    if best_action:
        mandi = best_action['mandi']
        days = best_action['day_offset']
        profit = best_action['net_profit']

        if profit >= 0:
            if days == 0:
                rec_text = f"Sell TODAY at {mandi} for best profit of ₹{profit}."
            else:
                rec_text = f"Store for {days} days and sell at {mandi}. Expected profit: ₹{profit}."
        else:
            if days == 0:
                rec_text = f"Minimize Loss: Sell TODAY at {mandi}. Loss: ₹{abs(profit)}."
            else:
                rec_text = f"Minimize Loss: Store for {days} days and sell at {mandi}. Projected Loss: ₹{abs(profit)}."

    return {
        "best_action": best_action,
        "recommendation_text": rec_text,
        "alternatives": alternatives[:5]
    }

def _get_future_prices(mandi: str, commodity: str, days: int = 7, weather_cache: list = None):
    """
    Predict future prices.
    Priority: Daily XGBoost model → Old per-crop model → Smart fallback.
    """
    # FALLBACK GENERATOR
    def generate_mock(start_price=5000, seed_str=""):
        import random
        today_str = datetime.date.today().strftime("%Y%m%d")
        full_seed = f"{seed_str}_{today_str}"
        rng = random.Random(full_seed)

        base = start_price
        mock_preds = []
        today = datetime.date.today()
        for i in range(days):
            date = today + datetime.timedelta(days=i)
            change = rng.uniform(-start_price*0.02, start_price*0.02)
            base += change
            mock_preds.append({
                "date": date.strftime("%Y-%m-%d"),
                "predicted_price": round(base, 2),
                "source": "estimated"
            })
        return mock_preds

    try:
        # ============================================================
        # PRIORITY 1: Try Daily XGBoost Model (industry-standard)
        # ============================================================
        try:
            from daily_predictor import predict_daily, has_daily_model
            from master_data import MANDI_TO_DISTRICT

            if has_daily_model(commodity):
                district = MANDI_TO_DISTRICT.get(mandi, "")
                daily_preds = predict_daily(
                    commodity=commodity,
                    mandi=mandi,
                    days=days,
                    district=district
                )
                if daily_preds and len(daily_preds) > 0:
                    logger.info(f"Daily model prediction for {commodity} at {mandi}: {len(daily_preds)} days")
                    return daily_preds
        except Exception as e:
            logger.warning(f"Daily model failed for {commodity}: {e}. Falling back to old model.")

        # ============================================================
        # PRIORITY 2: Old per-crop RandomForest model (legacy)
        # ============================================================

        # 1. Get last real price for smart fallback
        last_real_price = None
        commodity_avg_price = None

        try:
            loader = DataLoader()
            df = loader.load_data()

            sub_df = loader.filter_data(df, mandi, commodity)
            if not sub_df.empty:
                last_real_price = sub_df['modal_price'].iloc[-1]

            if not last_real_price:
                comm_df = df[df['commodity'] == commodity]
                if not comm_df.empty:
                    commodity_avg_price = comm_df['modal_price'].mean()
        except:
            pass

        default_price = last_real_price if last_real_price else (commodity_avg_price if commodity_avg_price else 4000)

        # 2. LAZY LOAD CROP-SPECIFIC MODEL
        model_key = commodity

        if model_key not in loaded_models:
            safe_commodity = commodity.replace("/", "_").replace("\\", "_").replace(":", "_").replace("(", "_").replace(")", "_")
            model_filename = f"model_crop_{safe_commodity}.joblib"
            model_path = os.path.join(MODELS_DIR, model_filename)

            if os.path.exists(model_path):
                logger.info(f"Lazy loading legacy model for {commodity}...")
                try:
                    loaded_models[model_key] = joblib.load(model_path)
                except Exception as e:
                    logger.error(f"Failed to load legacy model: {e}")

        # 3. Use Model if Available, else Fallback
        if model_key not in loaded_models:
            logger.info(f"No model for {commodity}. Using Smart Fallback: {default_price}")
            return generate_mock(default_price, seed_str=f"{mandi}_{commodity}")

        model_data = loaded_models[model_key]
        ml_model = model_data['model']
        features_list = model_data['features']

        # 4. Load Data
        loader = DataLoader()
        df = loader.load_data()

        # 5. Filter Data
        sub_df = loader.filter_data(df, mandi, commodity)
        if sub_df.empty:
            sub_df = loader.get_crop_data(df, commodity)
            if sub_df.empty:
                return generate_mock(default_price, seed_str=f"{mandi}_{commodity}")

        # 6. Prepare prediction loop
        preds = []
        current_history = sub_df.copy()
        fe = FeatureEngineer()
        last_date = current_history['date'].max()

        # Weather
        try:
            if weather_cache and len(weather_cache) > 0:
                weather_forecasts = weather_cache
            else:
                district = MANDI_TO_DISTRICT.get(mandi, "")
                if district:
                    coords = get_district_coords(district)
                else:
                    coords = AP_STATE_CENTER
                lat, lon = coords['lat'], coords['lon']
                weather_forecasts = get_forecast(lat, lon, days=days+20)
        except Exception as e:
            logger.warning(f"Weather error: {e}. Using empty weather.")
            weather_forecasts = []

        today = pd.Timestamp(datetime.date.today())
        needed = days
        max_steps = 365
        step = 0

        # 7. Prediction Loop
        while needed > 0 and step < max_steps:
            step += 1
            target_date = last_date + datetime.timedelta(days=1)

            w_day = {}
            if target_date >= today:
                delta = (target_date - today).days
                if weather_forecasts and 0 <= delta < len(weather_forecasts):
                    w_day = weather_forecasts[delta]

            feat_df = fe.prepare_features_for_prediction(
                current_history, weather_forecast=w_day,
                commodity=commodity, full_df=df
            )

            for f in features_list:
                if f not in feat_df.columns:
                    feat_df[f] = 0

            X = feat_df[features_list]
            pred_price = ml_model.predict(X)[0]

            avg_arrivals = current_history['arrivals'].tail(7).mean() if 'arrivals' in current_history.columns else 100
            if pd.isna(avg_arrivals):
                avg_arrivals = 100

            new_row = {
                "date": target_date, "mandi": mandi, "commodity": commodity,
                "modal_price": pred_price, "arrivals": avg_arrivals,
                "min_price": pred_price, "max_price": pred_price
            }
            current_history = pd.concat([current_history, pd.DataFrame([new_row])], ignore_index=True)
            last_date = target_date

            if target_date >= today:
                preds.append({
                    "date": target_date.strftime("%Y-%m-%d"),
                    "predicted_price": round(float(pred_price), 2),
                    "source": "legacy_model"
                })
                needed -= 1

        return preds

    except Exception as e:
        logger.error(f"CRITICAL ERROR in prediction logic: {e}. Returning fallback.")
        import traceback
        traceback.print_exc()
        return generate_mock(5200, seed_str=f"{mandi}_{commodity}")

class UpdateProfileRequest(BaseModel):
    name: str
    district: str = ""
    state: str = "Andhra Pradesh"
    mandi: str
    crops: list[str]

@app.post("/update_profile")
def update_profile(req: UpdateProfileRequest, db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(Farmer.name == req.name).first()
    
    if farmer:
        farmer.state = req.state
        farmer.district = req.district
        farmer.mandi = req.mandi
        farmer.crops = "|".join(req.crops)
        db.commit()
        return {"status": "success", "message": "Profile updated"}
        
    # If user not found, create new one to match old fallback behavior
    import uuid
    new_farmer = Farmer(
        id=str(uuid.uuid4()),
        name=req.name,
        password=get_password_hash("auto_recovered"),
        state=req.state,
        district=req.district,
        mandi=req.mandi,
        crops="|".join(req.crops)
    )
    db.add(new_farmer)
    db.commit()
    return {"status": "success", "message": "Profile updated"}


import uuid

class RegisterRequest(BaseModel):
    name: str
    password: str
    district: str = ""
    state: str = "Andhra Pradesh"
    mandi: str
    crops: list[str]

@app.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(Farmer).filter(Farmer.name == req.name).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    user_id = str(uuid.uuid4())
    crops_str = "|".join(req.crops)

    hashed_password = get_password_hash(req.password)
    
    new_farmer = Farmer(
        id=user_id,
        name=req.name,
        password=hashed_password,
        state=req.state,
        district=req.district,
        mandi=req.mandi,
        crops=crops_str
    )
    
    db.add(new_farmer)
    db.commit()

    return {"status": "success", "user_id": user_id, "message": "Registration successful"}

class LoginRequest(BaseModel):
    name: str
    password: str

@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Farmer).filter(Farmer.name == req.name).first()
    
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    # Format crops array
    crops_list = user.crops.split("|") if user.crops else []
    
    # Ensure district field exists
    district = user.district
    if not district:
        district = MANDI_TO_DISTRICT.get(user.mandi, "")
        
    # AUTO-FIX: If crops contain mandi names (old data bug)
    ap_data = MASTER_DATA.get("Andhra Pradesh", {})
    fixed_crops = []
    for crop in crops_list:
        crop = crop.strip()
        if not crop: continue
        if crop in ap_data:
            fixed_crops.extend(ap_data[crop])
        else:
            fixed_crops.append(crop)
            
    final_crops = sorted(list(set(fixed_crops)))
    
    # Generate JWT Token
    from datetime import timedelta
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.name}, expires_delta=access_token_expires
    )
    
    return {
        "status": "success", 
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "district": district,
            "mandi": user.mandi,
            "crops": final_crops,
            "state": user.state
        }
    }

@app.get("/me")
def read_users_me(current_user: Farmer = Depends(get_current_user)):
    crops_list = current_user.crops.split("|") if current_user.crops else []
    return {
        "id": current_user.id,
        "name": current_user.name,
        "district": current_user.district,
        "mandi": current_user.mandi,
        "crops": crops_list
    }

class DashboardRequest(BaseModel):
    state: str = "Andhra Pradesh"
    district: str = ""
    mandi: str  # Can be comma-separated for multi-mandi
    crops: list[str]

@app.post("/dashboard")
def get_dashboard(req: DashboardRequest):
    import traceback
    try:
        # Parse multi-mandi (comma-separated)
        mandis = [m.strip() for m in req.mandi.split(",") if m.strip()]
        if not mandis:
            mandis = [req.mandi]

        # AUTO-FIX: If crops contain mandi names (old data bug),
        # replace them with actual crops for that mandi
        ap_data = MASTER_DATA.get("Andhra Pradesh", {})
        fixed_crops = []
        for crop in req.crops:
            crop = crop.strip()
            if crop in ap_data:
                # This is a mandi name stored as crop! Get its actual crops
                fixed_crops.extend(ap_data[crop])
            elif crop:
                fixed_crops.append(crop)
        crops_to_use = list(set(fixed_crops)) if fixed_crops else req.crops

        # Weather: Use district coordinates for AP
        if req.district:
            coords = get_district_coords(req.district)
        else:
            # Try to find district from first mandi
            district = MANDI_TO_DISTRICT.get(mandis[0], "")
            coords = get_district_coords(district) if district else AP_STATE_CENTER

        lat, lon = coords['lat'], coords['lon']

        # Fetch 10-day forecast
        weather_forecast = get_forecast(lat, lon, days=10)

        today_weather = {"temp_max": 30, "condition": "Sunny"}
        if weather_forecast:
            daily = weather_forecast[0]
            current_temp = daily.get('temp_now', daily.get('temp_avg', 30))

            rain_mm = daily.get('rain_mm', 0)
            humidity = daily.get('humidity', 0)

            cond = "Sunny"
            if rain_mm >= 15:
                cond = "Heavy Rain"
            elif rain_mm >= 5:
                cond = "Rainy"
            elif rain_mm >= 1:
                cond = "Light Rain"
            elif humidity > 80:
                cond = "Cloudy"
            elif humidity > 65:
                cond = "Partly Cloudy"

            today_weather = {
                "temp_max": current_temp,
                "condition": cond,
                "humidity": daily.get('humidity_now', daily.get('humidity', 50)),
                "rain_mm": rain_mm
            }

        # Disaster Alert
        alert = None
        
        # Check for upcoming cyclones / high winds in next 3 days + LIVE wind
        if weather_forecast:
            # 1. Check live current wind first
            live_wind = weather_forecast[0].get("wind_now", 0)
            
            # 2. Check upcoming forecast
            high_winds = [day.get("wind_speed_max", 0) for day in weather_forecast[:3]]
            max_wind_upcoming = max(high_winds) if high_winds else 0
            
            if live_wind > 60:
                alert = f"🔴 LIVE CYCLONE ALERT: Currently experiencing severe winds ({live_wind} km/h). Stay safe!"
            elif live_wind > 40:
                alert = f"🔴 LIVE ALERT: High stormy winds right now ({live_wind} km/h)!"
            elif max_wind_upcoming > 60:
                alert = f"🌀 Cyclone Warning (Next 3 Days): High winds expected ({max_wind_upcoming} km/h). Secure crops!"
            elif max_wind_upcoming > 40:
                alert = f"⚠️ Storm Warning (Next 3 Days): Winds of {max_wind_upcoming} km/h approaching."

        # Rain-based alerts — graduated by actual intensity
        if not alert:
            rain_today = today_weather.get("rain_mm", 0)
            # Check upcoming 3-day rain totals too
            upcoming_rain = max([day.get("rain_mm", 0) for day in weather_forecast[:3]]) if weather_forecast else 0

            if rain_today >= 30 or upcoming_rain >= 30:
                alert = f"🌧️ Heavy rains expected ({max(rain_today, upcoming_rain):.0f}mm). Protect harvested crops."
            elif rain_today >= 10 or upcoming_rain >= 15:
                alert = f"☔ Moderate rain expected ({max(rain_today, upcoming_rain):.0f}mm). Plan field activities accordingly."
            elif rain_today >= 3:
                alert = f"🌦️ Light showers expected today ({rain_today:.0f}mm). No major impact on crops."
             
        # If still no alert, show a safe message
        if not alert:
             alert = "✅ Weather is clear. No cyclones or severe storms expected this week."

        # Crop Predictions — for each crop, show predictions from EACH mandi
        graph_data = []
        recommendations = []

        from real_time_data import get_real_time_price

        for crop in crops_to_use:
            # Find best price across all mandis for recommendation
            best_mandi = None
            best_price = 0
            best_date = ""

            for mandi in mandis:
                real_data = get_real_time_price(mandi, crop, "Andhra Pradesh")
                prices = _get_future_prices(mandi, crop, days=7, weather_cache=weather_forecast)

                today_label = "Not Updated"
                today_price_numeric = 0.0
                today_status = "unknown"

                if real_data:
                     today_label = f"₹{real_data['price']}"
                     today_price_numeric = real_data['price']
                     today_status = "verified"
                elif prices and len(prices) > 0:
                     first_pred = prices[0]
                     pred_price = first_pred['predicted_price']
                     today_label = f"₹{pred_price}"
                     today_price_numeric = pred_price
                     today_status = first_pred.get('source', 'estimated')

                # Label: "Crop (Mandi)" if multi-mandi, else just "Crop"
                series_name = f"{crop} ({mandi.replace(' APMC', '')})" if len(mandis) > 1 else crop

                series = {
                    "name": series_name,
                    "mandi": mandi,
                    "current_price_label": today_label,
                    "current_status": today_status,
                    "points": [{"date": p["date"], "price": p["predicted_price"], "source": p.get("source", "estimated")} for p in prices]
                }
                graph_data.append(series)

                # Track best price across mandis
                if prices and len(prices) > 0:
                    max_p = max(prices, key=lambda x: x['predicted_price'])
                    if max_p['predicted_price'] > best_price:
                        best_price = max_p['predicted_price']
                        best_date = max_p['date']
                        best_mandi = mandi

            if best_mandi:
                mandi_display = best_mandi.replace(' APMC', '')
                rec_text = f"Sell {crop} on {best_date}"
                
                details_text = f"Price expected to reach ₹{best_price} at {mandi_display}"
                if len(mandis) > 1:
                    details_text = f"Best price expected at {mandi_display}: ₹{best_price}"

                recommendations.append({
                    "crop": crop,
                    "action": rec_text,
                    "best_price": best_price,
                    "best_mandi": best_mandi,
                    "details": details_text,
                    "icon": "trending_up"
                })

        # Location label
        location_label = mandis[0] if len(mandis) == 1 else f"{req.district or mandis[0]} ({len(mandis)} mandis)"

        return {
            "weather": {
                "location": location_label,
                "today": today_weather,
                "alert": alert
            },
            "graph_data": graph_data,
            "recommendations": recommendations
        }
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/update_data")
def update_data(days: int = 7):
    """Triggers manual update from OGD API (AP data only)."""
    from ogd_service import OGDService
    try:
        service = OGDService()
        service.update_database(days_history=days)
        return {"status": "success", "message": f"AP database updated with last {days} days of data."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train")
def trigger_training():
    """Triggers per-crop model retraining for AP."""
    from model_utils import train_models
    try:
        train_models()
        return {"status": "success", "message": "AP crop models retrained successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- DAILY DATA PIPELINE ENDPOINT ---

@app.post("/update_daily")
def update_daily_endpoint(date_str: str = None):
    """
    Triggers daily data collection pipeline:
    arrivals → weather → calendar → feature engineering.
    
    Args:
        date_str: Optional date in YYYY-MM-DD format. Defaults to today.
    """
    from services.feature_engineering import update_daily_data
    try:
        target_date = None
        if date_str:
            target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")

        results = update_daily_data(target_date)
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Daily update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/daily_features")
def get_daily_features(commodity: str = None, limit: int = 30):
    """
    Returns the latest merged features for a commodity.
    Useful for debugging and verifying the pipeline output.
    """
    merged_path = os.path.join(os.path.dirname(__file__), 'daily_data', 'merged_features.csv')
    if not os.path.exists(merged_path):
        raise HTTPException(status_code=404, detail="No merged features found. Run /update_daily first.")

    df = pd.read_csv(merged_path)
    if commodity:
        df = df[df['commodity'] == commodity]

    # Return last N rows
    df = df.tail(limit)
    return df.to_dict(orient='records')


@app.post("/train_daily")
def train_daily_models():
    """
    Train XGBoost daily models for all commodities.
    This uses the merged_features.csv from the daily data pipeline.
    """
    from daily_model import train_all_daily_models
    try:
        results = train_all_daily_models(verbose=True)
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Daily training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model_info")
def model_info(commodity: str = None):
    """
    Returns info about trained daily models.
    If commodity is specified, returns that model's metrics.
    Otherwise returns summary of all models.
    """
    report_path = os.path.join(os.path.dirname(__file__), 'daily_data', 'training_report.csv')
    if not os.path.exists(report_path):
        return {"status": "no_models", "message": "No daily models trained yet. Run /train_daily first."}

    report = pd.read_csv(report_path)
    if commodity:
        row = report[report['commodity'] == commodity]
        if row.empty:
            return {"status": "not_found", "commodity": commodity}
        return row.to_dict(orient='records')[0]

    return {
        "total_models": len(report),
        "avg_mape": round(report['mape'].mean(), 2),
        "avg_r2": round(report['r2'].mean(), 3),
        "avg_dir_accuracy": round(report['dir_accuracy'].mean(), 1),
        "best_models": report.nsmallest(5, 'mape').to_dict(orient='records'),
    }


# =============================================================================
# DYNAMIC VEGETABLE PREDICTION ENDPOINTS
# =============================================================================

from arrival_checker import get_active_crops as _get_active_crops_data
from arrival_checker import get_crop_mandi_breakdown
from activity_validator import validate_and_predict


@app.get("/active-crops")
def active_crops(district: str):
    """
    Returns categorized vegetable activity for a district.
    Dynamically checks recent arrival data to classify each vegetable
    as Active, Low Activity, or Inactive.

    Query params:
        district: District name (e.g., "Guntur")

    Response:
        {
            "district": "Guntur",
            "active": [{"crop": "Tomato", "arrival_3d": 120, "arrival_7d": 350}],
            "low_activity": [{"crop": "Brinjal", ...}],
            "inactive": [{"crop": "Pumpkin", ...}]
        }
    """
    if not district:
        raise HTTPException(status_code=400, detail="district parameter is required")

    try:
        result = _get_active_crops_data(district)
        return result
    except Exception as e:
        logger.error(f"Error fetching active crops for {district}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predict-vegetable")
def predict_vegetable(district: str, crop: str):
    """
    Predict price for a vegetable with activity validation.

    Only runs prediction if the crop has recent trading activity.
    Returns structured response with confidence intervals and direction.

    Query params:
        district: District name (e.g., "Guntur")
        crop: Vegetable name (e.g., "Tomato")

    Response (active crop):
        {
            "status": "success",
            "crop": "Tomato",
            "district": "Guntur",
            "activity_status": "Active",
            "predicted_price": 2450,
            "confidence_interval": [2320, 2590],
            "direction": "UP",
            "model_used": "XGBoost Daily Model",
            "predictions_7d": [...]
        }

    Response (inactive crop):
        {
            "status": "inactive",
            "message": "No recent trading activity for this crop..."
        }
    """
    if not district:
        raise HTTPException(status_code=400, detail="district parameter is required")
    if not crop:
        raise HTTPException(status_code=400, detail="crop parameter is required")

    try:
        result = validate_and_predict(district, crop)
        return result
    except Exception as e:
        logger.error(f"Error predicting {crop} for {district}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vegetable-details")
def vegetable_details(crop: str, district: str = ""):
    """
    Returns detailed mandi-wise arrival breakdown + prediction for a vegetable.

    Shows which districts and mandis in AP received this vegetable,
    with 3d/7d arrival totals and latest prices.

    Query params:
        crop: Vegetable name (e.g., "Tomato")
        district: User's district for prediction context (optional)

    Response:
        {
            "crop": "Tomato",
            "prediction": { ... },
            "districts": [
                {
                    "district": "Annamayya",
                    "total_3d": 5200,
                    "total_7d": 18500,
                    "mandis": [
                        {
                            "mandi": "Madanapalle APMC",
                            "arrival_3d": 3500,
                            "arrival_7d": 12000,
                            "latest_price": 2450
                        }
                    ]
                }
            ]
        }
    """
    if not crop:
        raise HTTPException(status_code=400, detail="crop parameter is required")

    try:
        # Get mandi-wise breakdown
        breakdown = get_crop_mandi_breakdown(crop)

        # Get prediction using the user's district (or default mandi from most active district)
        pred_district = district if district else (
            breakdown["districts"][0]["district"] if breakdown["districts"] else "Guntur"
        )
        prediction = validate_and_predict(pred_district, crop)

        return {
            "crop": crop,
            "prediction": prediction,
            "districts": breakdown["districts"],
        }
    except Exception as e:
        logger.error(f"Error fetching vegetable details for {crop}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- SCHEDULER ENDPOINTS ---

@app.get("/pipeline_status")
def pipeline_status():
    """
    Returns the current status of the daily data pipeline.
    Shows which steps have run and their results.
    """
    from scheduler import get_pipeline_status, get_next_run_times
    status = get_pipeline_status()
    status["next_runs"] = get_next_run_times()
    return status


@app.post("/run_pipeline_now")
def run_pipeline_now():
    """
    Manually trigger the full 5-step pipeline immediately.
    Useful for testing or if you need fresh data right now.
    """
    from scheduler import (
        step_1_fetch_data, step_2_validate_data,
        step_3_feature_engineering, step_4_train_and_predict,
        step_5_refresh_dashboard
    )
    try:
        step_1_fetch_data()
        step_2_validate_data()
        step_3_feature_engineering()
        step_4_train_and_predict()
        step_5_refresh_dashboard()

        from scheduler import get_pipeline_status
        return {"status": "success", "pipeline": get_pipeline_status()}
    except Exception as e:
        logger.error(f"Manual pipeline run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import sys
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except OSError as e:
        if hasattr(e, 'winerror') and e.winerror == 10048:
            print("===============================================================")
            print("⚠️  SERVER ALREADY RUNNING  ⚠️")
            print("You tried to start the server, but it's already active.")
            print("You can safely IGNORE this error. Your app will work fine.")
            print("===============================================================")
            pass
        else:
            raise e
    except SystemExit:
        print("Server stopped (Port 8000 was active).")
        pass
