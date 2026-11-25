"""
AP Mandi Predict - Central Configuration for Andhra Pradesh
Contains MSP values, seasonality calendars, crop metadata, and coordinates.
"""

# ============================================================
# 1. MSP (Minimum Support Price) Lookup — 2025-26 Values (₹/Quintal)
# Source: Government of India, Commission for Agricultural Costs & Prices
# ============================================================
MSP_2025_26 = {
    "Paddy(Common)":        2300,
    "Paddy":                2300,
    "Rice":                 2300,   # Derived from paddy MSP
    "Jowar(Sorghum)":       3371,
    "Jowar":                3371,
    "Bajra(Pearl Millet/Cumbu)": 2625,
    "Bajra":                2625,
    "Maize":                2225,
    "Ragi":                 4290,
    "Ragi(Finger Millet)":  4290,
    "Foxtail Millet(Navane)": 3570,
    "Barley(Jau)":          1735,
    "Arhar(Tur/Red Gram)(Whole)": 7550,
    "Arhar Dal(Tur Dal)":   7550,
    "Green Gram(Moong)(Whole)": 8682,
    "Bengal Gram(Gram)(Whole)": 5650,
    "Bengal Gram":          5650,
    "Black Gram(Urd Beans)(Whole)": 7400,
    "Black Gram":           7400,
    "Lentil(Masur)(Whole)": 6425,
    "Groundnut":            6377,
    "Ground Nut Seed":      6377,
    "Sunflower Seed":       6760,
    "Sunflower":            6760,
    "Soyabean":             4892,
    "Sesamum(Sesame,Gingelly,Til)": 9267,
    "Safflower":            5800,
    "Niger Seed(Ramtil)":   8717,
    "Mustard":              5950,
    "Rapeseed(Toria)":      5950,
    "Cotton":               7020,
    "Castor Seed":          6015,
    "Copra":                11582,
    "Jute":                 5050,
    "Sugarcane":            3150,   # FRP
    "Tobacco":              6800,   # Approximate
    "Wheat":                2275,
}

def get_msp(commodity: str) -> float:
    """Returns MSP for a commodity, or 0 if not an MSP crop."""
    return MSP_2025_26.get(commodity, 0)


# ============================================================
# 2. Seasonality Calendar for AP
# ============================================================
# Kharif: June-Oct sowing, Oct-Jan harvest → prices DROP during harvest
# Rabi: Nov-Feb sowing, Mar-May harvest → prices DROP during harvest
# Lean: Jun-Sep (before kharif harvest) → prices RISE

CROP_SEASONS = {
    # crop_name: {"kharif_harvest_months": [...], "rabi_harvest_months": [...]}
    "Paddy(Common)":    {"kharif_harvest": [10, 11, 12],    "rabi_harvest": [3, 4, 5]},
    "Paddy":            {"kharif_harvest": [10, 11, 12],    "rabi_harvest": [3, 4, 5]},
    "Rice":             {"kharif_harvest": [10, 11, 12],    "rabi_harvest": [3, 4, 5]},
    "Red Chilli":       {"kharif_harvest": [1, 2, 3],       "rabi_harvest": []},
    "Dry Chillies":     {"kharif_harvest": [1, 2, 3],       "rabi_harvest": []},
    "Chili Red":        {"kharif_harvest": [1, 2, 3],       "rabi_harvest": []},
    "Green Chilli":     {"kharif_harvest": [],               "rabi_harvest": []},  # Year-round
    "Cotton":           {"kharif_harvest": [10, 11, 12, 1], "rabi_harvest": []},
    "Groundnut":        {"kharif_harvest": [9, 10, 11],     "rabi_harvest": [3, 4]},
    "Ground Nut Seed":  {"kharif_harvest": [9, 10, 11],     "rabi_harvest": [3, 4]},
    "Sunflower":        {"kharif_harvest": [10, 11],        "rabi_harvest": [3, 4]},
    "Sunflower Seed":   {"kharif_harvest": [10, 11],        "rabi_harvest": [3, 4]},
    "Castor Seed":      {"kharif_harvest": [11, 12, 1],     "rabi_harvest": []},
    "Maize":            {"kharif_harvest": [9, 10],         "rabi_harvest": [3, 4]},
    "Jowar(Sorghum)":   {"kharif_harvest": [10, 11],        "rabi_harvest": [3, 4]},
    "Jowar":            {"kharif_harvest": [10, 11],        "rabi_harvest": [3, 4]},
    "Bajra(Pearl Millet/Cumbu)": {"kharif_harvest": [9, 10], "rabi_harvest": []},
    "Bajra":            {"kharif_harvest": [9, 10],          "rabi_harvest": []},
    "Turmeric":         {"kharif_harvest": [1, 2, 3],       "rabi_harvest": []},
    "Bengal Gram(Gram)(Whole)": {"kharif_harvest": [],       "rabi_harvest": [2, 3, 4]},
    "Bengal Gram":      {"kharif_harvest": [],               "rabi_harvest": [2, 3, 4]},
    "Black Gram(Urd Beans)(Whole)": {"kharif_harvest": [10, 11], "rabi_harvest": []},
    "Black Gram":       {"kharif_harvest": [10, 11],        "rabi_harvest": []},
    "Arhar(Tur/Red Gram)(Whole)": {"kharif_harvest": [12, 1, 2], "rabi_harvest": []},
    "Tomato":           {"kharif_harvest": [],               "rabi_harvest": []},  # Year-round
    "Onion":            {"kharif_harvest": [10, 11],        "rabi_harvest": [3, 4, 5]},
    "Banana":           {"kharif_harvest": [],               "rabi_harvest": []},  # Year-round
    "Mango":            {"kharif_harvest": [4, 5, 6, 7],    "rabi_harvest": []},
    "Coconut":          {"kharif_harvest": [],               "rabi_harvest": []},  # Year-round
    "Tobacco":          {"kharif_harvest": [],               "rabi_harvest": [2, 3, 4]},
    "Sugarcane":        {"kharif_harvest": [11, 12, 1, 2, 3, 4], "rabi_harvest": []},
    "Soyabean":         {"kharif_harvest": [10, 11],        "rabi_harvest": []},
    # NEW CROPS from AGMARKNET
    "Ragi(Finger Millet)":       {"kharif_harvest": [9, 10, 11], "rabi_harvest": []},
    "Barley(Jau)":               {"kharif_harvest": [],          "rabi_harvest": [3, 4]},
    "Mustard":                   {"kharif_harvest": [],          "rabi_harvest": [2, 3, 4]},
    "Rapeseed(Toria)":           {"kharif_harvest": [],          "rabi_harvest": [2, 3, 4]},
    "Sesamum(Sesame,Gingelly,Til)": {"kharif_harvest": [9, 10], "rabi_harvest": [3, 4]},
    "Safflower":                 {"kharif_harvest": [],          "rabi_harvest": [3, 4, 5]},
    "Niger Seed(Ramtil)":        {"kharif_harvest": [10, 11, 12], "rabi_harvest": []},
    "Green Gram(Moong)(Whole)": {"kharif_harvest": [9, 10],     "rabi_harvest": [3, 4]},
    "Lentil(Masur)(Whole)":     {"kharif_harvest": [],           "rabi_harvest": [2, 3, 4]},
    "Copra":                    {"kharif_harvest": [3, 4, 5, 6], "rabi_harvest": []},
    "Jute":                     {"kharif_harvest": [8, 9, 10],   "rabi_harvest": []},
    "Wheat":                    {"kharif_harvest": [],           "rabi_harvest": [3, 4, 5]},
    "Foxtail Millet(Navane)":   {"kharif_harvest": [9, 10],     "rabi_harvest": []},
}

def get_seasonality_features(commodity: str, month: int):
    """
    Returns seasonality features for a given crop and month.
    Returns dict with: is_kharif_harvest, is_rabi_harvest, is_lean_season
    """
    seasons = CROP_SEASONS.get(commodity, {"kharif_harvest": [], "rabi_harvest": []})
    
    is_kharif = 1 if month in seasons.get("kharif_harvest", []) else 0
    is_rabi = 1 if month in seasons.get("rabi_harvest", []) else 0
    # Lean season: not in any harvest period
    is_lean = 1 if (is_kharif == 0 and is_rabi == 0) else 0
    
    quarter = (month - 1) // 3 + 1  # Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec
    
    return {
        "is_kharif_harvest": is_kharif,
        "is_rabi_harvest": is_rabi,
        "is_lean_season": is_lean,
        "quarter": quarter,
    }


# ============================================================
# 3. Export Demand Proxy
# ============================================================
# Crops where export demand significantly affects AP prices
EXPORT_CROPS = {
    "Red Chilli":       {"export_months": [1, 2, 3, 4, 5], "hub": "Guntur"},
    "Dry Chillies":     {"export_months": [1, 2, 3, 4, 5], "hub": "Guntur"},
    "Chili Red":        {"export_months": [1, 2, 3, 4, 5], "hub": "Guntur"},
    "Turmeric":         {"export_months": [2, 3, 4, 5],    "hub": "Duggirala"},
    "Groundnut":        {"export_months": [11, 12, 1, 2],  "hub": "Kurnool"},
    "Castor Seed":      {"export_months": [1, 2, 3],       "hub": "Adoni"},
    "Tobacco":          {"export_months": [3, 4, 5, 6],    "hub": "Ongole"},
}

def get_export_features(commodity: str, month: int):
    """Returns export demand features."""
    if commodity in EXPORT_CROPS:
        info = EXPORT_CROPS[commodity]
        is_export_season = 1 if month in info["export_months"] else 0
        return {
            "is_export_crop": 1,
            "is_export_season": is_export_season,
        }
    return {
        "is_export_crop": 0,
        "is_export_season": 0,
    }


# ============================================================
# 4. AP Weather & Geographic Config
# ============================================================
# State center (for state-level weather aggregation)
AP_STATE_CENTER = {"lat": 15.9129, "lon": 79.7400}

# Cyclone-prone months for AP (Bay of Bengal cyclone season)
CYCLONE_MONTHS = [10, 11, 12]  # Oct-Dec

# District-level approximate coordinates
DISTRICT_COORDS = {
    "Anantapur":            {"lat": 14.6819, "lon": 77.6006},
    "Chittoor":             {"lat": 13.2172, "lon": 79.1003},
    "East Godavari":        {"lat": 17.3212, "lon": 82.0677},
    "Guntur":               {"lat": 16.3067, "lon": 80.4365},
    "Krishna":              {"lat": 16.5062, "lon": 80.6480},
    "Kurnool":              {"lat": 15.8281, "lon": 78.0373},
    "Nellore":              {"lat": 14.4426, "lon": 79.9865},
    "Prakasam":             {"lat": 15.3480, "lon": 79.5560},
    "Srikakulam":           {"lat": 18.2949, "lon": 83.8994},
    "Visakhapatnam":        {"lat": 17.6868, "lon": 83.2185},
    "Vizianagaram":         {"lat": 18.1067, "lon": 83.3956},
    "West Godavari":        {"lat": 16.9174, "lon": 81.3399},
    "YSR Kadapa":           {"lat": 14.4674, "lon": 78.8241},
    # New districts (2022 reorganization) — using parent district coords
    "Alluri Sitharama Raju": {"lat": 17.6000, "lon": 82.0000},
    "Anakapalli":           {"lat": 17.6910, "lon": 83.0040},
    "Annamayya":            {"lat": 14.0000, "lon": 78.7500},
    "Bapatla":              {"lat": 15.9000, "lon": 80.4700},
    "Eluru":                {"lat": 16.7107, "lon": 81.0952},
    "Kakinada":             {"lat": 16.9891, "lon": 82.2475},
    "Konaseema":            {"lat": 16.7400, "lon": 82.0700},
    "NTR":                  {"lat": 16.5062, "lon": 80.6480},
    "Palnadu":              {"lat": 16.2833, "lon": 79.7000},
    "Parvathipuram Manyam": {"lat": 18.7667, "lon": 83.4333},
    "Sri Potti Sriramulu Nellore": {"lat": 14.4426, "lon": 79.9865},
    "Sri Sathya Sai":       {"lat": 14.7500, "lon": 77.6000},
    "Tirupati":             {"lat": 13.6288, "lon": 79.4192},
}

def get_district_coords(district: str):
    """Returns lat/lon for a district, defaults to AP state center."""
    return DISTRICT_COORDS.get(district, AP_STATE_CENTER)
