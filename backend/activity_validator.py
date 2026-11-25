"""
AP Mandi Predict — Activity Validator
Validates crop activity before running predictions.
Acts as middleware between the API endpoint and the prediction engine.
"""

import logging
from datetime import datetime

from arrival_checker import check_crop_activity
from vegetable_config import VEGETABLES, DEFAULT_CONFIDENCE_BAND_PCT

logger = logging.getLogger(__name__)


def validate_and_predict(district: str, crop: str) -> dict:
    """
    Validate crop activity, then run prediction if allowed.

    Flow:
        1. Check crop activity status via arrival data
        2. If Active → run XGBoost prediction, return full results
        3. If Low Activity → run prediction + attach warning
        4. If Inactive → block prediction, return informative message

    Args:
        district: District name (e.g., "Guntur")
        crop: Commodity name (e.g., "Tomato")

    Returns:
        Dict with prediction results or error message.
    """
    # Step 1: Check activity — always use state-wide for comprehensive data
    activity = check_crop_activity(district, crop, statewide=True)
    status = activity["status"]

    logger.info(
        f"Activity check for {crop} in {district}: "
        f"status={status}, 3d={activity['arrival_3d']}, 7d={activity['arrival_7d']}"
    )

    # Step 3: Run prediction
    prediction = _run_prediction(district, crop)

    # Step 4: Attach activity metadata
    result = {
        "status": "success",
        "crop": crop,
        "district": district,
        "activity_status": status,
        "arrival_3d": activity["arrival_3d"],
        "arrival_7d": activity["arrival_7d"],
        **prediction,
    }

    # Step 5: Add warning for low activity
    if status == "Low Activity":
        result["warning"] = (
            "Low recent trading activity. "
            "Prediction may be less reliable due to limited recent data."
        )

    return result


def _run_prediction(district: str, crop: str) -> dict:
    """
    Run the actual price prediction using the best available model.
    Priority: Daily XGBoost → Legacy per-crop model → Smart fallback.

    Returns:
        {
            "predicted_price": float,
            "confidence_interval": [low, high],
            "direction": "UP" | "DOWN" | "STABLE",
            "model_used": str,
            "predictions_7d": [...],
        }
    """
    from master_data import DISTRICT_MANDIS

    # Get a representative mandi for this district
    mandis = DISTRICT_MANDIS.get(district, [])
    if not mandis:
        # Try case-insensitive
        for d, m in DISTRICT_MANDIS.items():
            if d.lower().strip() == district.lower().strip():
                mandis = m
                break

    if not mandis:
        return {
            "predicted_price": None,
            "confidence_interval": None,
            "direction": None,
            "model_used": None,
            "predictions_7d": [],
            "error": f"No mandis found for district: {district}",
        }

    # Use first mandi as representative
    mandi = mandis[0]

    # Try Daily XGBoost Model first
    try:
        from daily_predictor import predict_daily, has_daily_model

        if has_daily_model(crop):
            preds = predict_daily(
                commodity=crop,
                mandi=mandi,
                days=7,
                district=district,
            )

            if preds and len(preds) > 0:
                today_pred = preds[0]
                predicted_price = today_pred["predicted_price"]

                # Confidence interval from model or default band
                conf_low = today_pred.get(
                    "confidence_low",
                    round(predicted_price * (1 - DEFAULT_CONFIDENCE_BAND_PCT / 100), 2),
                )
                conf_high = today_pred.get(
                    "confidence_high",
                    round(predicted_price * (1 + DEFAULT_CONFIDENCE_BAND_PCT / 100), 2),
                )

                # Direction: compare today vs day 2
                direction = "STABLE"
                if len(preds) >= 2:
                    diff = preds[1]["predicted_price"] - predicted_price
                    if diff > predicted_price * 0.01:
                        direction = "UP"
                    elif diff < -predicted_price * 0.01:
                        direction = "DOWN"

                return {
                    "predicted_price": round(predicted_price, 2),
                    "confidence_interval": [round(conf_low, 2), round(conf_high, 2)],
                    "direction": direction,
                    "model_used": "XGBoost Daily Model",
                    "predictions_7d": preds,
                }

    except Exception as e:
        logger.warning(f"Daily model failed for {crop}: {e}")

    # Fallback: use _get_future_prices from main module
    try:
        # Import the internal prediction function
        import importlib
        main_module = importlib.import_module("main")
        preds = main_module._get_future_prices(mandi, crop, days=7)

        if preds and len(preds) > 0:
            today_pred = preds[0]
            predicted_price = today_pred["predicted_price"]

            conf_low = round(predicted_price * (1 - DEFAULT_CONFIDENCE_BAND_PCT / 100), 2)
            conf_high = round(predicted_price * (1 + DEFAULT_CONFIDENCE_BAND_PCT / 100), 2)

            direction = "STABLE"
            if len(preds) >= 2:
                diff = preds[1]["predicted_price"] - predicted_price
                if diff > predicted_price * 0.01:
                    direction = "UP"
                elif diff < -predicted_price * 0.01:
                    direction = "DOWN"

            source = today_pred.get("source", "fallback")
            model_name = {
                "daily_model": "XGBoost Daily Model",
                "legacy_model": "RandomForest Legacy Model",
                "estimated": "Statistical Estimate",
            }.get(source, f"Fallback ({source})")

            return {
                "predicted_price": round(predicted_price, 2),
                "confidence_interval": [conf_low, conf_high],
                "direction": direction,
                "model_used": model_name,
                "predictions_7d": preds,
            }

    except Exception as e:
        logger.error(f"Fallback prediction failed for {crop} at {mandi}: {e}")

    return {
        "predicted_price": None,
        "confidence_interval": None,
        "direction": None,
        "model_used": None,
        "predictions_7d": [],
        "error": f"No prediction model available for {crop}",
    }


def is_vegetable(crop: str) -> bool:
    """Check if a crop is in our target vegetable list."""
    return crop in VEGETABLES
