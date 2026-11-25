class DataLocalization {
  static String get(String key, String locale) {
    if (locale == 'en') return key;

    // Check Districts
    if (_districts.containsKey(key)) {
      return _districts[key]?[locale] ?? key;
    }

    // Check States
    if (_states.containsKey(key)) {
      return _states[key]?[locale] ?? key;
    }

    // Check Mandis
    if (_mandis.containsKey(key)) {
      return _mandis[key]?[locale] ?? key;
    }

    // Check Commodities
    if (_commodities.containsKey(key)) {
      return _commodities[key]?[locale] ?? key;
    }

    return key;
  }

  // Only AP state
  static const Map<String, Map<String, String>> _states = {
    "Andhra Pradesh": {"hi": "आंध्र प्रदेश", "te": "ఆంధ్ర ప్రదేశ్"},
  };

  // All 26 AP Districts
  static const Map<String, Map<String, String>> _districts = {
    "Anantapur": {"hi": "अनंतपुर", "te": "అనంతపురం"},
    "Sri Sathya Sai": {"hi": "श्री सत्य साई", "te": "శ్రీ సత్యసాయి"},
    "Kurnool": {"hi": "कुर्नूल", "te": "కర్నూలు"},
    "Nandyal": {"hi": "नंदयाल", "te": "నంద్యాల"},
    "Guntur": {"hi": "गुंटूर", "te": "గుంటూరు"},
    "Palnadu": {"hi": "पालनाडु", "te": "పల్నాడు"},
    "Bapatla": {"hi": "बापटला", "te": "బాపట్ల"},
    "Prakasam": {"hi": "प्रकाशम", "te": "ప్రకాశం"},
    "Nellore": {"hi": "नेल्लोर", "te": "నెల్లూరు"},
    "Krishna": {"hi": "कृष्णा", "te": "కృష్ణా"},
    "NTR": {"hi": "एनटीआर", "te": "ఎన్‌టి‌ఆర్"},
    "West Godavari": {"hi": "पश्चिम गोदावरी", "te": "పశ్చిమ గోదావరి"},
    "Eluru": {"hi": "एलुरु", "te": "ఏలూరు"},
    "East Godavari": {"hi": "पूर्व गोदावरी", "te": "తూర్పు గోదావరి"},
    "Kakinada": {"hi": "काकीनाडा", "te": "కాకినాడ"},
    "Konaseema": {"hi": "कोनसीमा", "te": "కోనసీమ"},
    "Alluri Sitharama Raju": {
      "hi": "अल्लूरी सीताराम राजू",
      "te": "అల్లూరి సీతారామ రాజు"
    },
    "Visakhapatnam": {"hi": "विशाखापत्तनम", "te": "విశాఖపట్నం"},
    "Anakapalli": {"hi": "अनकापल्ली", "te": "అనకాపల్లి"},
    "Vizianagaram": {"hi": "विजयनगरम", "te": "విజయనగరం"},
    "Parvathipuram Manyam": {
      "hi": "पार्वतीपुरम मन्यम",
      "te": "పార్వతీపురం మన్యం"
    },
    "Srikakulam": {"hi": "श्रीकाकुलम", "te": "శ్రీకాకుళం"},
    "Chittoor": {"hi": "चित्तूर", "te": "చిత్తూరు"},
    "Tirupati": {"hi": "तिरुपति", "te": "తిరుపతి"},
    "Annamayya": {"hi": "अन्नमय्या", "te": "అన్నమయ్య"},
    "YSR Kadapa": {"hi": "वाईएसआर कड़पा", "te": "వైఎస్‌ఆర్ కడప"},
  };

  // AP Mandis
  static const Map<String, Map<String, String>> _mandis = {
    // Anantapur District
    "Anantapur APMC": {"hi": "अनंतपुर", "te": "అనంతపురం"},
    "Dharmavaram APMC": {"hi": "धर्मवरम", "te": "ధర్మవరం"},
    "Penukonda APMC": {"hi": "पेनुकोंडा", "te": "పెనుకొండ"},
    "Hindupur APMC": {"hi": "हिंदुपुर", "te": "హిందూపురం"},
    "Guntakal APMC": {"hi": "गुंटकल", "te": "గుంటకల్"},
    "Gooty APMC": {"hi": "गूटी", "te": "గూటి"},
    "Kalyandurg APMC": {"hi": "कल्याणदुर्ग", "te": "కళ్యాణదుర్గం"},
    "Uravakonda APMC": {"hi": "उरवकोंडा", "te": "ఉరవకొండ"},
    // Sri Sathya Sai District
    "Puttaparthi APMC": {"hi": "पुट्टपर्ती", "te": "పుట్టపర్తి"},
    "Kadiri APMC": {"hi": "कडिरी", "te": "కదిరి"},
    // Kurnool District
    "Kurnool APMC": {"hi": "कुर्नूल", "te": "కర్నూలు"},
    "Adoni APMC": {"hi": "अदोनी", "te": "ఆదోని"},
    "Yemmiganur APMC": {"hi": "येम्मिगनूर", "te": "ఎమ్మిగనూరు"},
    "Pattikonda APMC": {"hi": "पत्तिकोंडा", "te": "పత్తికొండ"},
    // Nandyal District
    "Nandyal APMC": {"hi": "नंदयाल", "te": "నంద్యాల"},
    "Nandikotkur APMC": {"hi": "नंदिकोटकूर", "te": "నందికోత్కూర్"},
    "Banaganapalle APMC": {"hi": "बनगानापल्ले", "te": "బనగానపల్లె"},
    // Guntur District
    "Guntur APMC": {"hi": "गुंटूर", "te": "గుంటూరు"},
    "Tenali APMC": {"hi": "तेनाली", "te": "తెనాలి"},
    "Narasaraopet APMC": {"hi": "नरसरावपेट", "te": "నరసరావుపేట"},
    "Chilakaluripet APMC": {"hi": "चिलकलूरीपेट", "te": "చిలకలూరిపేట"},
    "Sattenapalli APMC": {"hi": "सत्तेनपल्ली", "te": "సత్తెనపల్లి"},
    "Mangalagiri APMC": {"hi": "मंगलगिरी", "te": "మంగళగిరి"},
    "Duggirala APMC": {"hi": "दुग्गिराला", "te": "దుగ్గిరాల"},
    // Palnadu District
    "Gurazala APMC": {"hi": "गुराज़ाला", "te": "గురజాల"},
    "Macherla APMC": {"hi": "मचेर्ला", "te": "మాచర్ల"},
    "Piduguralla APMC": {"hi": "पिडुगुराल्ला", "te": "పిడుగురాళ్ళ"},
    // Bapatla District
    "Bapatla APMC": {"hi": "बापटला", "te": "బాపట్ల"},
    "Chirala APMC": {"hi": "चीराला", "te": "చీరాల"},
    // Prakasam District
    "Ongole APMC": {"hi": "ओंगोल", "te": "ఒంగోలు"},
    "Markapur APMC": {"hi": "मारकापुर", "te": "మార్కాపురం"},
    "Kandukur APMC": {"hi": "कंदुकूर", "te": "కందుకూరు"},
    "Darsi APMC": {"hi": "दर्शी", "te": "దర్శి"},
    // Nellore District
    "Nellore APMC": {"hi": "नेल्लोर", "te": "నెల్లూరు"},
    "Kavali APMC": {"hi": "कावली", "te": "కావలి"},
    "Gudur APMC": {"hi": "गुडूर", "te": "గూడూరు"},
    // Krishna/NTR District
    "Vijayawada APMC": {"hi": "विजयवाड़ा", "te": "విజయవాడ"},
    "Machilipatnam APMC": {"hi": "मछलीपट्टनम", "te": "మచిలీపట్నం"},
    "Gudivada APMC": {"hi": "गुडिवाड़ा", "te": "గుడివాడ"},
    "Nuzvid APMC": {"hi": "नूज़विड", "te": "నూజివీడు"},
    "Jaggaiahpeta APMC": {"hi": "जग्गैयापेट", "te": "జగ్గయ్యపేట"},
    // West Godavari/Eluru District
    "Eluru APMC": {"hi": "एलुरु", "te": "ఏలూరు"},
    "Bhimavaram APMC": {"hi": "भीमावरम", "te": "భీమవరం"},
    "Tadepalligudem APMC": {"hi": "तदेपल्लीगुडेम", "te": "తాడేపల్లిగూడెం"},
    "Narsapuram APMC": {"hi": "नरसापुरम", "te": "నర్సాపురం"},
    "Chintalapudi APMC": {"hi": "चिंतलपुडी", "te": "చింతలపూడి"},
    "Denduluru APMC": {"hi": "डेंडुलूरू", "te": "దెందులూరు"},
    // East Godavari/Kakinada/Konaseema
    "Rajahmundry APMC": {"hi": "राजमुंदरी", "te": "రాజమహేంద్రవరం"},
    "Kakinada APMC": {"hi": "काकीनाडा", "te": "కాకినాడ"},
    "Amalapuram APMC": {"hi": "अमलापुरम", "te": "అమలాపురం"},
    "Rampachodavaram APMC": {"hi": "रामपाचोदवरम", "te": "రంపచోడవరం"},
    "Ambajipeta APMC": {"hi": "अम्बाजीपेट", "te": "అంబాజీపేట"},
    "Ravulapelem APMC": {"hi": "रावुलापेलेम", "te": "రావులపాలెం"},
    "Peddapuram APMC": {"hi": "पेद्दापुरम", "te": "పెద్దాపురం"},
    // Visakhapatnam/Anakapalli
    "Visakhapatnam APMC": {"hi": "विशाखापत्तनम", "te": "విశాఖపట్నం"},
    "Anakapally APMC": {"hi": "अनकापल्ली", "te": "అనకాపల్లి"},
    "Narsipatnam APMC": {"hi": "नरसीपटनम", "te": "నర్సీపట్నం"},
    "Paderu APMC": {"hi": "पदेरु", "te": "పాడేరు"},
    // Alluri Sitharama Raju
    "Chintapalli APMC": {"hi": "चिंतापल्ली", "te": "చింతపల్లి"},
    // Vizianagaram
    "Vizianagaram APMC": {"hi": "विजयनगरम", "te": "విజయనగరం"},
    "Bobbili APMC": {"hi": "बोब्बिली", "te": "బొబ్బిలి"},
    // Parvathipuram Manyam
    "Parvathipuram APMC": {"hi": "पार्वतीपुरम", "te": "పార్వతీపురం"},
    // Srikakulam
    "Srikakulam APMC": {"hi": "श्रीकाकुलम", "te": "శ్రీకాకుళం"},
    "Narasannapeta APMC": {"hi": "नरसन्नपेट", "te": "నరసన్నపేట"},
    "Palasa APMC": {"hi": "पालासा", "te": "పాలస"},
    // Chittoor/Tirupati/Annamayya
    "Chittoor APMC": {"hi": "चित्तूर", "te": "చిత్తూరు"},
    "Madanapalle APMC": {"hi": "मदनपल्ले", "te": "మదనపల్లె"},
    "Madanapalli APMC": {"hi": "मदनपल्ली", "te": "మదనపల్లి"},
    "Tirupati APMC": {"hi": "तिरुपति", "te": "తిరుపతి"},
    "Palamaner APMC": {"hi": "पालमनेर", "te": "పాలమనేరు"},
    "Punganur APMC": {"hi": "पुंगनूर", "te": "పుంగనూరు"},
    "Kalikiri APMC": {"hi": "काळिकिरी", "te": "కాళహస్తి"},
    "Valmikipuram APMC": {"hi": "वाल्मीकिपुरम", "te": "వాల్మీకిపురం"},
    "Rapur APMC": {"hi": "रापूर", "te": "రాపూర్"},
    "Sarvepalli APMC": {"hi": "सर्वेपल्ली", "te": "సర్వేపల్లి"},
    // YSR Kadapa
    "Kadapa APMC": {"hi": "कड़पा", "te": "కడప"},
    "Cuddapah APMC": {"hi": "कड़पा", "te": "కడప"},
    "Pulivendala APMC": {"hi": "पुलिवेंदला", "te": "పులివెందల"},
    "Proddatur APMC": {"hi": "प्रोद्दटूर", "te": "ప్రొద్దటూరు"},
    "Rajampet APMC": {"hi": "राजमपेट", "te": "రాజంపేట"},
    "Jammalamadugu APMC": {"hi": "जम्मलमडुगु", "te": "జమ్మలమడుగు"},
  };

  static const Map<String, Map<String, String>> _commodities = {
    "Paddy": {"hi": "धान", "te": "వరి"},
    "Paddy(Common)": {"hi": "धान", "te": "వరి"},
    "Rice": {"hi": "चावल", "te": "బియ్యం"},
    "Wheat": {"hi": "गेंहू", "te": "గోధుమలు"},
    "Maize": {"hi": "मक्का", "te": "మొక్కజొన్న"},
    "Cotton": {"hi": "कपास", "te": "పత్తి"},
    "Red Chilli": {"hi": "लाल मिर्च", "te": "ఎండు మిర్చి"},
    "Dry Chillies": {"hi": "सूखी मिर्च", "te": "ఎండు మిర్చి"},
    "Chili Red": {"hi": "लाल मिर्च", "te": "ఎండు మిర్చి"},
    "Green Chilli": {"hi": "हरी मिर्च", "te": "పచ్చి మిర్చి"},
    "Turmeric": {"hi": "हल्दी", "te": "పసుపు"},
    "Groundnut": {"hi": "मूंगफली", "te": "వేరుశనగ"},
    "Ground Nut Seed": {"hi": "मूंगफली बीज", "te": "వేరుశనగ విత్తనం"},
    "Tomato": {"hi": "टमाटर", "te": "టమోటా"},
    "Onion": {"hi": "प्याज़", "te": "ఉల్లిపాయలు"},
    "Potato": {"hi": "आलू", "te": "బంగాళదుంప"},
    "Banana": {"hi": "केला", "te": "అరటిపండు"},
    "Mango": {"hi": "आम", "te": "మామిడి"},
    "Coconut": {"hi": "नारियल", "te": "కొబ్బరి"},
    "Sunflower": {"hi": "सूरजमुखी", "te": "పొద్దుతిరుగుడు"},
    "Sunflower Seed": {"hi": "सूरजमुखी बीज", "te": "పొద్దుతిరుగుడు విత్తనం"},
    "Black Gram": {"hi": "उड़द", "te": "మినుములు"},
    "Black Gram(Urd Beans)(Whole)": {"hi": "उड़द", "te": "మినుములు"},
    "Bengal Gram": {"hi": "चना", "te": "శనగలు"},
    "Bengal Gram(Gram)(Whole)": {"hi": "चना", "te": "శనగలు"},
    "Red Gram": {"hi": "अरहर", "te": "కందులు"},
    "Green Gram(Moong)(Whole)": {"hi": "मूंग", "te": "పెసలు"},
    "Arhar(Tur/Red Gram)(Whole)": {"hi": "अरहर", "te": "కందులు"},
    "Jowar(Sorghum)": {"hi": "ज्वार", "te": "జొన్నలు"},
    "Jowar": {"hi": "ज्वार", "te": "జొన్నలు"},
    "Bajra(Pearl Millet/Cumbu)": {"hi": "बाजरा", "te": "సజ్జలు"},
    "Bajra": {"hi": "बाजरा", "te": "సజ్జలు"},
    "Foxtail Millet(Navane)": {"hi": "कांगनी", "te": "కొర్రలు"},
    "Jaggery": {"hi": "गुड़", "te": "బెల్లం"},
    "Gur(Jaggery)": {"hi": "गुड़", "te": "బెల్లం"},
    "Sugarcane": {"hi": "गन्ना", "te": "చెరకు"},
    "Tobacco": {"hi": "तम्बाकू", "te": "పొగాకు"},
    "Castor Seed": {"hi": "अरंडी", "te": "ఆముదాలు"},
    "Coffee": {"hi": "कॉफ़ी", "te": "కాఫీ"},
    "Cashewnut": {"hi": "काजू", "te": "జీడిపప్పు"},
    "Lemon": {"hi": "नींबू", "te": "నిమ్మకాయ"},
    "Lime": {"hi": "नींबू", "te": "నిమ్మకాయ"},
    "Mousambi(Sweet Lime)": {"hi": "मौसंबी", "te": "మోసంబి"},
    "Brinjal": {"hi": "बैंगन", "te": "వంకాయ"},
    "Cauliflower": {"hi": "गोभी", "te": "గోబీ"},
    "Cluster beans": {"hi": "ग्वार", "te": "గోరుచిక్కుడు"},
    "Ridgeguard(Tori)": {"hi": "तोरी", "te": "బీరకాయ"},
    "Oil Palm": {"hi": "ऑयल पाम", "te": "ఆయిల్ పామ్"},
    "Citrus": {"hi": "खट्टे फल", "te": "నిమ్మజాతి పండ్లు"},
    "Wood": {"hi": "लकड़ी", "te": "కలప"},
    "Soyabean": {"hi": "सोयाबीन", "te": "సోయాబీన్"},
    "Sesamum(Sesame,Gingelly,Til)": {"hi": "तिल", "te": "నువ్వులు"},
    "Vegetables": {"hi": "सब्जियां", "te": "కూరగాయలు"},
    "Garlic": {"hi": "लहसुन", "te": "వెల్లుల్లి"},
  };
}
