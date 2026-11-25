"""Quick test script for the vegetable prediction system."""
from arrival_checker import get_active_crops, check_crop_activity
import json

districts = ["Guntur", "Chittoor", "Annamayya"]

for district in districts:
    print(f"\n=== {district} ===")
    r = get_active_crops(district)
    print(f"  Active:       {[c['crop'] for c in r['active']]}")
    print(f"  Low Activity: {[c['crop'] for c in r['low_activity']]}")
    print(f"  Inactive:     {[c['crop'] for c in r['inactive']]}")

# Detailed check for a few crops
print("\n=== Detailed Activity Checks ===")
for crop in ["Tomato", "Onion", "Green Chilli"]:
    result = check_crop_activity("Chittoor", crop)
    print(f"  {crop}: {json.dumps(result)}")

print("\n=== Test activity_validator ===")
from activity_validator import validate_and_predict
result = validate_and_predict("Chittoor", "Tomato")
print(f"  Status: {result.get('status')}")
print(f"  Activity: {result.get('activity_status')}")
print(f"  Price: {result.get('predicted_price')}")
print(f"  Direction: {result.get('direction')}")
print(f"  Model: {result.get('model_used')}")
if result.get('warning'):
    print(f"  Warning: {result['warning']}")
if result.get('message'):
    print(f"  Message: {result['message']}")

print("\nDone!")
