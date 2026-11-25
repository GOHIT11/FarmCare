"""Test daily model prediction."""
import sys
sys.path.insert(0, '.')
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

from daily_predictor import predict_daily, has_daily_model

# Test with a common commodity
test_commodities = ['Tomato', 'Onion', 'Paddy(Common)', 'Cotton']

for commodity in test_commodities:
    if has_daily_model(commodity):
        print(f"\n--- {commodity} (Daily XGBoost) ---")
        preds = predict_daily(commodity, days=7)
        for p in preds:
            print(f"  {p['date']}: Rs.{p['predicted_price']:,.2f} "
                  f"[{p['confidence_low']:,.2f} - {p['confidence_high']:,.2f}] "
                  f"({p['source']})")
    else:
        print(f"\n--- {commodity}: No daily model available ---")
