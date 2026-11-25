# AP Mandi Predict - Master Data
# Contains ONLY Andhra Pradesh data organized by District → Mandi → Crops
# All 26 districts of Andhra Pradesh (post-2022 reorganization)
# Each mandi lists the actual crops traded there
# CROPS VERIFIED FROM AGMARKNET.GOV.IN (Official Government Data)

MASTER_DATA = {
    "Andhra Pradesh": {
        # =============================================
        # ANANTAPUR DISTRICT
        # =============================================
        "Anantapur APMC": [
            "Banana", "Groundnut", "Mousambi(Sweet Lime)", "Tomato",
            "Sunflower Seed", "Paddy(Common)", "Bengal Gram(Gram)(Whole)",
            "Maize", "Red Gram", "Cotton", "Castor Seed",
            "Sesamum(Sesame,Gingelly,Til)", "Soyabean", "Safflower",
            "Niger Seed(Ramtil)"
        ],
        "Dharmavaram APMC": [
            "Groundnut", "Paddy(Common)", "Sunflower Seed", "Cotton",
            "Bengal Gram(Gram)(Whole)", "Castor Seed", "Maize",
            "Sesamum(Sesame,Gingelly,Til)", "Soyabean", "Safflower"
        ],
        "Penukonda APMC": [
            "Groundnut", "Paddy(Common)", "Tomato", "Onion",
            "Sunflower Seed", "Bengal Gram(Gram)(Whole)",
            "Green Gram(Moong)(Whole)", "Sesamum(Sesame,Gingelly,Til)"
        ],
        "Hindupur APMC": [
            "Groundnut", "Paddy(Common)", "Tomato", "Banana",
            "Onion", "Cotton", "Sunflower Seed", "Ragi(Finger Millet)"
        ],
        "Guntakal APMC": [
            "Groundnut", "Castor Seed", "Sunflower Seed",
            "Bengal Gram(Gram)(Whole)", "Paddy(Common)",
            "Sesamum(Sesame,Gingelly,Til)", "Niger Seed(Ramtil)"
        ],
        "Gooty APMC": [
            "Groundnut", "Castor Seed", "Cotton", "Sunflower Seed",
            "Safflower", "Sesamum(Sesame,Gingelly,Til)"
        ],
        "Kalyandurg APMC": [
            "Groundnut", "Sunflower Seed", "Paddy(Common)", "Castor Seed",
            "Sesamum(Sesame,Gingelly,Til)", "Safflower"
        ],
        "Uravakonda APMC": [
            "Groundnut", "Sunflower Seed", "Cotton", "Castor Seed",
            "Niger Seed(Ramtil)"
        ],

        # =============================================
        # SRI SATHYA SAI DISTRICT (carved from Anantapur)
        # =============================================
        "Puttaparthi APMC": [
            "Groundnut", "Paddy(Common)", "Sunflower Seed", "Maize",
            "Sesamum(Sesame,Gingelly,Til)"
        ],
        "Kadiri APMC": [
            "Groundnut", "Castor Seed", "Sunflower Seed",
            "Tomato", "Onion", "Sesamum(Sesame,Gingelly,Til)"
        ],

        # =============================================
        # KURNOOL DISTRICT
        # =============================================
        "Kurnool APMC": [
            "Arhar(Tur/Red Gram)(Whole)", "Bajra(Pearl Millet/Cumbu)",
            "Bengal Gram(Gram)(Whole)", "Black Gram(Urd Beans)(Whole)",
            "Castor Seed", "Dry Chillies", "Foxtail Millet(Navane)",
            "Groundnut", "Maize", "Onion", "Sunflower Seed",
            "Jowar(Sorghum)", "Cotton", "Paddy(Common)",
            "Mustard", "Sesamum(Sesame,Gingelly,Til)",
            "Green Gram(Moong)(Whole)", "Safflower"
        ],
        "Adoni APMC": [
            "Castor Seed", "Cotton", "Groundnut", "Sunflower",
            "Jowar(Sorghum)", "Paddy(Common)", "Bengal Gram(Gram)(Whole)",
            "Mustard", "Sesamum(Sesame,Gingelly,Til)"
        ],
        "Yemmiganur APMC": [
            "Castor Seed", "Groundnut", "Cotton", "Sunflower Seed",
            "Paddy(Common)", "Sesamum(Sesame,Gingelly,Til)"
        ],
        "Nandyal APMC": [
            "Jowar(Sorghum)", "Maize", "Paddy(Common)",
            "Bengal Gram(Gram)(Whole)", "Black Gram(Urd Beans)(Whole)",
            "Groundnut", "Sunflower Seed", "Green Gram(Moong)(Whole)"
        ],
        "Pattikonda APMC": [
            "Tomato", "Groundnut", "Castor Seed", "Cotton",
            "Sesamum(Sesame,Gingelly,Til)"
        ],
        "Atmakur(Kurnool) APMC": [
            "Groundnut", "Castor Seed", "Bengal Gram(Gram)(Whole)",
            "Paddy(Common)", "Safflower"
        ],

        # =============================================
        # NANDYAL DISTRICT (carved from Kurnool)
        # =============================================
        "Nandikotkur APMC": [
            "Paddy(Common)", "Bengal Gram(Gram)(Whole)", "Maize",
            "Groundnut", "Jowar(Sorghum)"
        ],
        "Banaganapalle APMC": [
            "Mango", "Paddy(Common)", "Groundnut"
        ],

        # =============================================
        # GUNTUR DISTRICT
        # =============================================
        "Guntur APMC": [
            "Cotton", "Dry Chillies", "Red Chilli", "Turmeric",
            "Tobacco", "Bengal Gram(Gram)(Whole)", "Paddy(Common)",
            "Black Gram(Urd Beans)(Whole)", "Maize",
            "Green Gram(Moong)(Whole)", "Sesamum(Sesame,Gingelly,Til)",
            "Jowar(Sorghum)", "Lentil(Masur)(Whole)", "Mustard",
            "Arhar(Tur/Red Gram)(Whole)"
        ],
        "Tenali APMC": [
            "Lime", "Paddy(Common)", "Cotton", "Black Gram(Urd Beans)(Whole)",
            "Banana", "Tobacco", "Green Gram(Moong)(Whole)"
        ],
        "Narasaraopet APMC": [
            "Cotton", "Red Chilli", "Paddy(Common)", "Tobacco",
            "Bengal Gram(Gram)(Whole)", "Turmeric",
            "Green Gram(Moong)(Whole)"
        ],
        "Chilakaluripet APMC": [
            "Cotton", "Red Chilli", "Tobacco", "Paddy(Common)",
            "Turmeric", "Sesamum(Sesame,Gingelly,Til)"
        ],
        "Sattenapalli APMC": [
            "Cotton", "Paddy(Common)", "Red Chilli", "Tobacco",
            "Sesamum(Sesame,Gingelly,Til)"
        ],
        "Mangalagiri APMC": [
            "Paddy(Common)", "Cotton", "Red Chilli", "Banana",
            "Green Gram(Moong)(Whole)"
        ],

        # =============================================
        # PALNADU DISTRICT (carved from Guntur)
        # =============================================
        "Gurazala APMC": [
            "Chili Red", "Cotton", "Paddy(Common)", "Tobacco",
            "Jowar(Sorghum)"
        ],
        "Macherla APMC": [
            "Cotton", "Paddy(Common)", "Red Chilli", "Bengal Gram(Gram)(Whole)",
            "Green Gram(Moong)(Whole)"
        ],
        "Piduguralla APMC": [
            "Cotton", "Paddy(Common)", "Lime", "Bengal Gram(Gram)(Whole)",
            "Sesamum(Sesame,Gingelly,Til)"
        ],

        # =============================================
        # BAPATLA DISTRICT (carved from Guntur)
        # =============================================
        "Bapatla APMC": [
            "Paddy(Common)", "Cotton", "Black Gram(Urd Beans)(Whole)",
            "Tobacco", "Green Gram(Moong)(Whole)"
        ],
        "Chirala APMC": [
            "Red Chilli", "Cotton", "Paddy(Common)", "Tobacco",
            "Turmeric"
        ],

        # =============================================
        # PRAKASAM DISTRICT
        # =============================================
        "Ongole APMC": [
            "Bengal Gram", "Red Chilli", "Tobacco", "Cotton",
            "Paddy(Common)", "Black Gram(Urd Beans)(Whole)",
            "Green Gram(Moong)(Whole)", "Sesamum(Sesame,Gingelly,Til)",
            "Groundnut", "Castor Seed"
        ],
        "Markapur APMC": [
            "Red Chilli", "Bengal Gram(Gram)(Whole)", "Paddy(Common)",
            "Cotton", "Castor Seed", "Sesamum(Sesame,Gingelly,Til)"
        ],
        "Kandukur APMC": [
            "Red Chilli", "Bengal Gram(Gram)(Whole)", "Tobacco",
            "Paddy(Common)", "Green Gram(Moong)(Whole)"
        ],
        "Darsi APMC": [
            "Paddy(Common)", "Cotton", "Red Chilli",
            "Bengal Gram(Gram)(Whole)", "Green Gram(Moong)(Whole)"
        ],

        # =============================================
        # NELLORE (SRI POTTI SRIRAMULU NELLORE) DISTRICT
        # =============================================
        "Nellore APMC": [
            "Paddy(Common)", "Red Chilli", "Onion", "Tomato",
            "Banana", "Coconut", "Black Gram(Urd Beans)(Whole)",
            "Green Gram(Moong)(Whole)", "Groundnut", "Jute"
        ],
        "Kavali APMC": [
            "Paddy(Common)", "Red Chilli", "Bengal Gram(Gram)(Whole)",
            "Onion", "Green Gram(Moong)(Whole)"
        ],
        "Gudur APMC": [
            "Paddy(Common)", "Red Chilli", "Tomato", "Onion",
            "Groundnut", "Green Gram(Moong)(Whole)"
        ],
        "Atmakur(Nellore) APMC": [
            "Paddy(Common)", "Red Chilli", "Black Gram(Urd Beans)(Whole)",
            "Green Gram(Moong)(Whole)"
        ],

        # =============================================
        # KRISHNA DISTRICT / NTR DISTRICT
        # =============================================
        "Vijayawada APMC": [
            "Banana", "Black Gram", "Rice", "Paddy(Common)",
            "Red Chilli", "Cotton", "Turmeric", "Onion", "Tomato",
            "Mango", "Coconut", "Green Gram(Moong)(Whole)",
            "Sesamum(Sesame,Gingelly,Til)"
        ],
        "Machilipatnam APMC": [
            "Paddy(Common)", "Cotton", "Black Gram(Urd Beans)(Whole)",
            "Coconut", "Banana", "Green Gram(Moong)(Whole)"
        ],
        "Gudivada APMC": [
            "Paddy(Common)", "Black Gram(Urd Beans)(Whole)", "Cotton",
            "Coconut", "Banana", "Mango", "Green Gram(Moong)(Whole)"
        ],
        "Nuzvid APMC": [
            "Mango", "Banana", "Paddy(Common)", "Cotton",
            "Black Gram(Urd Beans)(Whole)", "Green Gram(Moong)(Whole)"
        ],
        "Jaggaiahpeta APMC": [
            "Paddy(Common)", "Cotton", "Turmeric", "Banana",
            "Sugarcane", "Jaggery"
        ],

        # =============================================
        # WEST GODAVARI / ELURU DISTRICT
        # =============================================
        "Eluru APMC": [
            "Coconut", "Lemon", "Paddy", "Paddy(Common)", "Banana",
            "Black Gram(Urd Beans)(Whole)", "Turmeric",
            "Jute", "Green Gram(Moong)(Whole)"
        ],
        "Bhimavaram APMC": [
            "Paddy(Common)", "Coconut", "Banana", "Black Gram(Urd Beans)(Whole)",
            "Oil Palm", "Green Gram(Moong)(Whole)", "Jute"
        ],
        "Tadepalligudem APMC": [
            "Paddy(Common)", "Coconut", "Banana", "Turmeric",
            "Jute", "Green Gram(Moong)(Whole)"
        ],
        "Narsapuram APMC": [
            "Paddy(Common)", "Coconut", "Banana",
            "Black Gram(Urd Beans)(Whole)", "Jute"
        ],
        "Chintalapudi APMC": [
            "Lemon", "Paddy(Common)", "Cotton", "Turmeric",
            "Green Gram(Moong)(Whole)"
        ],
        "Denduluru APMC": [
            "Lemon", "Paddy(Common)", "Coconut", "Jute"
        ],

        # =============================================
        # EAST GODAVARI / KAKINADA / KONASEEMA DISTRICTS
        # =============================================
        "Rajahmundry APMC": [
            "Banana", "Coconut", "Paddy", "Paddy(Common)", "Turmeric",
            "Black Gram(Urd Beans)(Whole)", "Jaggery",
            "Copra", "Green Gram(Moong)(Whole)", "Jute"
        ],
        "Kakinada APMC": [
            "Paddy(Common)", "Coconut", "Banana", "Cashewnut",
            "Black Gram(Urd Beans)(Whole)", "Copra",
            "Green Gram(Moong)(Whole)", "Jute"
        ],
        "Amalapuram APMC": [
            "Paddy(Common)", "Coconut", "Banana",
            "Black Gram(Urd Beans)(Whole)", "Copra", "Jute"
        ],
        "Rampachodavaram APMC": [
            "Paddy(Common)", "Turmeric", "Cashewnut", "Jute"
        ],
        "Ambajipeta APMC": [
            "Banana", "Paddy(Common)", "Coconut", "Copra"
        ],
        "Ravulapelem APMC": [
            "Banana", "Paddy(Common)", "Coconut", "Copra"
        ],
        "Peddapuram APMC": [
            "Paddy(Common)", "Banana", "Coconut", "Jaggery", "Copra"
        ],
        "Anakapally APMC": [
            "Jaggery", "Paddy(Common)", "Cashewnut", "Banana", "Copra"
        ],

        # =============================================
        # VISAKHAPATNAM / ANAKAPALLI DISTRICT
        # =============================================
        "Visakhapatnam APMC": [
            "Paddy(Common)", "Cashewnut", "Coconut", "Banana",
            "Onion", "Tomato", "Potato", "Turmeric",
            "Copra", "Green Gram(Moong)(Whole)"
        ],
        "Narsipatnam APMC": [
            "Paddy(Common)", "Cashewnut", "Turmeric", "Jaggery",
            "Copra"
        ],
        "Paderu APMC": [
            "Turmeric", "Coffee", "Paddy(Common)", "Cashewnut",
            "Copra", "Ragi(Finger Millet)"
        ],

        # =============================================
        # ALLURI SITHARAMA RAJU DISTRICT
        # =============================================
        "Chintapalli APMC": [
            "Turmeric", "Paddy(Common)", "Cashewnut", "Coffee",
            "Ragi(Finger Millet)"
        ],

        # =============================================
        # VIZIANAGARAM DISTRICT
        # =============================================
        "Vizianagaram APMC": [
            "Paddy(Common)", "Jaggery", "Sugarcane", "Cashewnut",
            "Black Gram(Urd Beans)(Whole)", "Green Gram(Moong)(Whole)",
            "Ragi(Finger Millet)", "Copra"
        ],
        "Bobbili APMC": [
            "Paddy(Common)", "Jaggery", "Sugarcane", "Cashewnut",
            "Ragi(Finger Millet)"
        ],

        # =============================================
        # PARVATHIPURAM MANYAM DISTRICT
        # =============================================
        "Parvathipuram APMC": [
            "Paddy(Common)", "Jaggery", "Cashewnut", "Sugarcane",
            "Ragi(Finger Millet)", "Copra"
        ],

        # =============================================
        # SRIKAKULAM DISTRICT
        # =============================================
        "Srikakulam APMC": [
            "Paddy(Common)", "Cashewnut", "Sugarcane", "Jaggery",
            "Black Gram(Urd Beans)(Whole)", "Green Gram(Moong)(Whole)",
            "Ragi(Finger Millet)", "Niger Seed(Ramtil)", "Sesamum(Sesame,Gingelly,Til)"
        ],
        "Narasannapeta APMC": [
            "Paddy(Common)", "Cashewnut", "Jaggery",
            "Ragi(Finger Millet)", "Niger Seed(Ramtil)"
        ],
        "Palasa APMC": [
            "Paddy(Common)", "Cashewnut", "Sugarcane",
            "Niger Seed(Ramtil)", "Sesamum(Sesame,Gingelly,Til)"
        ],

        # =============================================
        # CHITTOOR DISTRICT / TIRUPATI / ANNAMAYYA DISTRICTS
        # =============================================
        "Chittoor APMC": [
            "Groundnut", "Gur(Jaggery)", "Mango", "Sugarcane",
            "Tomato", "Onion", "Paddy(Common)",
            "Sesamum(Sesame,Gingelly,Til)", "Safflower"
        ],
        "Madanapalle APMC": [
            "Groundnut", "Mango", "Tomato", "Potato",
            "Onion", "Brinjal", "Green Chilli",
            "Sesamum(Sesame,Gingelly,Til)"
        ],
        "Madanapalli APMC": [
            "Tomato", "Potato", "Onion", "Brinjal",
            "Cauliflower", "Green Chilli", "Ragi(Finger Millet)"
        ],
        "Tirupati APMC": [
            "Groundnut", "Mango", "Tomato", "Paddy(Common)",
            "Sugarcane", "Banana", "Ragi(Finger Millet)"
        ],
        "Palamaner APMC": [
            "Brinjal", "Cauliflower", "Cluster beans", "Green Chilli",
            "Potato", "Ridgeguard(Tori)", "Tomato",
            "Groundnut", "Paddy(Common)", "Ragi(Finger Millet)"
        ],
        "Punganur APMC": [
            "Tomato", "Groundnut", "Paddy(Common)", "Onion",
            "Ragi(Finger Millet)"
        ],
        "Kalikiri APMC": [
            "Tomato", "Groundnut", "Paddy(Common)", "Ragi(Finger Millet)"
        ],
        "Valmikipuram APMC": [
            "Tomato", "Groundnut", "Ragi(Finger Millet)"
        ],
        "Rapur APMC": [
            "Wood", "Groundnut", "Paddy(Common)", "Sesamum(Sesame,Gingelly,Til)"
        ],
        "Sarvepalli APMC": [
            "Lime", "Paddy(Common)", "Groundnut", "Black Gram(Urd Beans)(Whole)"
        ],

        # =============================================
        # YSR KADAPA DISTRICT
        # =============================================
        "Kadapa APMC": [
            "Banana", "Onion", "Turmeric", "Groundnut",
            "Paddy(Common)", "Red Chilli", "Sunflower Seed",
            "Sesamum(Sesame,Gingelly,Til)", "Safflower",
            "Green Gram(Moong)(Whole)", "Castor Seed"
        ],
        "Cuddapah APMC": [
            "Groundnut", "Paddy(Common)", "Sunflower Seed",
            "Red Chilli", "Sesamum(Sesame,Gingelly,Til)", "Safflower"
        ],
        "Pulivendala APMC": [
            "Mousambi(Sweet Lime)", "Groundnut", "Paddy(Common)",
            "Sunflower Seed", "Sesamum(Sesame,Gingelly,Til)"
        ],
        "Proddatur APMC": [
            "Groundnut", "Paddy(Common)", "Sunflower Seed",
            "Bengal Gram(Gram)(Whole)", "Sesamum(Sesame,Gingelly,Til)",
            "Castor Seed"
        ],
        "Rajampet APMC": [
            "Groundnut", "Paddy(Common)", "Sunflower Seed",
            "Citrus", "Tomato", "Sesamum(Sesame,Gingelly,Til)"
        ],
        "Jammalamadugu APMC": [
            "Groundnut", "Paddy(Common)", "Sunflower Seed",
            "Castor Seed", "Sesamum(Sesame,Gingelly,Til)"
        ],

        # =============================================
        # DUGGIRALA / TURMERIC BELT
        # =============================================
        "Duggirala APMC": [
            "Turmeric", "Paddy(Common)", "Cotton",
            "Sesamum(Sesame,Gingelly,Til)"
        ],
    }
}


# ============================================================
# District → Mandi mapping for UI dropdown cascade
# ============================================================
DISTRICT_MANDIS = {
    "Anantapur": [
        "Anantapur APMC", "Dharmavaram APMC", "Penukonda APMC",
        "Hindupur APMC", "Guntakal APMC", "Gooty APMC",
        "Kalyandurg APMC", "Uravakonda APMC"
    ],
    "Sri Sathya Sai": [
        "Puttaparthi APMC", "Kadiri APMC"
    ],
    "Kurnool": [
        "Kurnool APMC", "Adoni APMC", "Yemmiganur APMC",
        "Pattikonda APMC", "Atmakur(Kurnool) APMC"
    ],
    "Nandyal": [
        "Nandyal APMC", "Nandikotkur APMC", "Banaganapalle APMC"
    ],
    "Guntur": [
        "Guntur APMC", "Tenali APMC", "Narasaraopet APMC",
        "Chilakaluripet APMC", "Sattenapalli APMC", "Mangalagiri APMC"
    ],
    "Palnadu": [
        "Gurazala APMC", "Macherla APMC", "Piduguralla APMC"
    ],
    "Bapatla": [
        "Bapatla APMC", "Chirala APMC"
    ],
    "Prakasam": [
        "Ongole APMC", "Markapur APMC", "Kandukur APMC", "Darsi APMC"
    ],
    "Nellore": [
        "Nellore APMC", "Kavali APMC", "Gudur APMC",
        "Atmakur(Nellore) APMC"
    ],
    "Krishna": [
        "Vijayawada APMC", "Machilipatnam APMC", "Gudivada APMC",
        "Nuzvid APMC"
    ],
    "NTR": [
        "Jaggaiahpeta APMC"
    ],
    "West Godavari": [
        "Bhimavaram APMC", "Narsapuram APMC"
    ],
    "Eluru": [
        "Eluru APMC", "Tadepalligudem APMC", "Chintalapudi APMC",
        "Denduluru APMC"
    ],
    "East Godavari": [
        "Rajahmundry APMC", "Peddapuram APMC"
    ],
    "Kakinada": [
        "Kakinada APMC", "Ravulapelem APMC", "Ambajipeta APMC"
    ],
    "Konaseema": [
        "Amalapuram APMC"
    ],
    "Alluri Sitharama Raju": [
        "Rampachodavaram APMC", "Chintapalli APMC"
    ],
    "Visakhapatnam": [
        "Visakhapatnam APMC"
    ],
    "Anakapalli": [
        "Anakapally APMC", "Narsipatnam APMC", "Paderu APMC"
    ],
    "Vizianagaram": [
        "Vizianagaram APMC", "Bobbili APMC"
    ],
    "Parvathipuram Manyam": [
        "Parvathipuram APMC"
    ],
    "Srikakulam": [
        "Srikakulam APMC", "Narasannapeta APMC", "Palasa APMC"
    ],
    "Chittoor": [
        "Chittoor APMC", "Palamaner APMC", "Punganur APMC"
    ],
    "Tirupati": [
        "Tirupati APMC", "Kalikiri APMC", "Valmikipuram APMC",
        "Sarvepalli APMC"
    ],
    "Annamayya": [
        "Madanapalle APMC", "Madanapalli APMC", "Rapur APMC"
    ],
    "YSR Kadapa": [
        "Kadapa APMC", "Cuddapah APMC", "Pulivendala APMC",
        "Proddatur APMC", "Rajampet APMC", "Jammalamadugu APMC"
    ],
}

# Reverse lookup: Mandi → District
MANDI_TO_DISTRICT = {}
for district, mandis in DISTRICT_MANDIS.items():
    for mandi in mandis:
        MANDI_TO_DISTRICT[mandi] = district

# Additional mandis from MASTER_DATA not yet in DISTRICT_MANDIS
MANDI_TO_DISTRICT["Duggirala APMC"] = "Guntur"