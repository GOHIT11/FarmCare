"""
AP Mandi Predict — Vegetable Configuration
Full Andhra Pradesh vegetable list and activity constants for dynamic prediction.
"""

# =====================================================================
# FULL ANDHRA PRADESH VEGETABLE LIST
# All commonly grown and traded vegetables in AP mandis.
# =====================================================================

VEGETABLES = [
    "Tomato",
    "Onion",
    "Potato",
    "Brinjal",
    "Bhindi(Ladies Finger)",
    "Cabbage",
    "Cauliflower",
    "Green Chilli",
    "Beans",
    "Carrot",
    "Beetroot",
    "Bitter gourd",
    "Bottle Gourd",
    "Ridge Gourd(Tori)",
    "Snake Gourd",
    "Drumstick",
    "Pumpkin",
    "Ash Gourd",
    "Radish",
    "Cucumber",
    "Capsicum",
    "Cluster Beans",
    "Field Beans",
    "Turnip",
]

# Alternate names used in Agmarknet data — maps to our canonical name
VEGETABLE_ALIASES = {
    # Bhindi / Okra variants
    "Lady Finger": "Bhindi(Ladies Finger)",
    "Bhindi": "Bhindi(Ladies Finger)",
    "Okra": "Bhindi(Ladies Finger)",
    "Ladies Finger": "Bhindi(Ladies Finger)",
    # Gourd variants
    "Ridgeguard(Tori)": "Ridge Gourd(Tori)",
    "Ridge gourd": "Ridge Gourd(Tori)",
    "Bittergourd": "Bitter gourd",
    "Bitter Gourd": "Bitter gourd",
    "Bottlegourd": "Bottle Gourd",
    "Bottle gourd": "Bottle Gourd",
    "Snakegourd": "Snake Gourd",
    "Snake gourd": "Snake Gourd",
    "Ashgourd": "Ash Gourd",
    "Ash gourd": "Ash Gourd",
    # Chilli variants
    "Green Chillies": "Green Chilli",
    "Chillies": "Green Chilli",
    # Drumstick
    "Drum Stick": "Drumstick",
    # Capsicum
    "Bell Pepper": "Capsicum",
    "Shimla Mirch": "Capsicum",
    # Beans variants
    "Cluster beans": "Cluster Beans",
    "Guar": "Cluster Beans",
    "Field beans": "Field Beans",
    # Others
    "Beet Root": "Beetroot",
    "Beet root": "Beetroot",
}

# =====================================================================
# ACTIVITY THRESHOLDS (simplified)
# arrivals > 0 in last 7 days → Active
# arrivals == 0 → Low Activity
# =====================================================================

ACTIVE_THRESHOLD_3D = 50  # quintals (still used for summary stats)
LOW_ACTIVITY_THRESHOLD_7D = 0  # any non-zero arrival means some activity

# =====================================================================
# PREDICTION CONFIDENCE BAND
# Used to compute confidence intervals around point predictions.
# =====================================================================

# Default confidence band (±%) when model doesn't provide its own
DEFAULT_CONFIDENCE_BAND_PCT = 5.0
