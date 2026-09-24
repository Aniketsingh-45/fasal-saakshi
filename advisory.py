"""
Advisory engine: combines the disease diagnosis, weather, and vegetation-trend
signals into one plain-language recommendation.

Design choice: thresholds and logic are explicit, readable rules — not left to
the LLM to decide — so the advisory is explainable and consistent. This keeps
the "AI does the reading, code does the deciding" separation from the FLN
Class Map project, applied here too.

Crop-specific knowledge (irrigation/pest notes, regenerative tips) is kept in
the CROP_KNOWLEDGE dict below so it can be swapped or extended per crop/region/
country without touching the logic — this is the "config, not hardcoded logic"
approach that supports cross-border/BRICS applicability (Rule 04 of the
Code for Communities guidelines).
"""

CROP_KNOWLEDGE = {
    "Wheat": {
        "en": {
            "irrigation": "Wheat needs consistent moisture at the crown-root and flowering stages.",
            "pest_watch": "Watch for aphids and rust in humid, moderate-temperature weeks.",
            "regenerative_tip": "Consider leaving crop residue as mulch instead of burning it — it returns organic matter to the soil.",
        },
        "hi": {
            "irrigation": "गेहूं को जड़ बनने और फूल आने के समय लगातार नमी चाहिए।",
            "pest_watch": "नम और सामान्य तापमान वाले हफ्तों में एफिड और रतुआ रोग पर नज़र रखें।",
            "regenerative_tip": "फसल अवशेष जलाने के बजाय खेत में मल्च के रूप में छोड़ने पर विचार करें — इससे मिट्टी को पोषण मिलता है।",
        },
    },
    "Rice (Paddy)": {
        "en": {
            "irrigation": "Paddy needs standing water at key growth stages, but avoid prolonged waterlogging beyond need.",
            "pest_watch": "Watch for stem borer and blast disease, especially after heavy rain.",
            "regenerative_tip": "Alternate wetting and drying (AWD) can reduce water use and methane emissions.",
        },
        "hi": {
            "irrigation": "धान को मुख्य अवस्थाओं में खड़ा पानी चाहिए, पर ज़रूरत से ज़्यादा पानी रोकना नुकसानदेह हो सकता है।",
            "pest_watch": "भारी बारिश के बाद तना छेदक कीट और ब्लास्ट रोग पर नज़र रखें।",
            "regenerative_tip": "बारी-बारी से गीला और सूखा (AWD) तरीका पानी की खपत और मीथेन कम कर सकता है।",
        },
    },
    "Cotton": {
        "en": {
            "irrigation": "Cotton is drought-tolerant but sensitive to waterlogging during boll formation.",
            "pest_watch": "Watch for bollworm and whitefly, especially in warm, dry spells.",
            "regenerative_tip": "Intercropping with legumes can improve soil nitrogen and reduce pest pressure.",
        },
        "hi": {
            "irrigation": "कपास सूखा सह सकता है, पर बॉल बनने के समय जलभराव नुकसानदेह है।",
            "pest_watch": "गर्म और सूखे मौसम में सुंडी (bollworm) और सफेद मक्खी पर नज़र रखें।",
            "regenerative_tip": "दलहनी फसलों के साथ मिश्रित खेती मिट्टी में नाइट्रोजन बढ़ा सकती है।",
        },
    },
    "Other": {
        "en": {
            "irrigation": "Follow local agriculture department guidance for this crop's water needs.",
            "pest_watch": "Consult your nearest Krishi Vigyan Kendra for crop-specific pest alerts.",
            "regenerative_tip": "Crop rotation and reduced tillage generally support long-term soil health.",
        },
        "hi": {
            "irrigation": "इस फसल की पानी की ज़रूरत के लिए स्थानीय कृषि विभाग की सलाह लें।",
            "pest_watch": "फसल से जुड़ी कीट चेतावनी के लिए नज़दीकी कृषि विज्ञान केंद्र से संपर्क करें।",
            "regenerative_tip": "फसल चक्र और कम जुताई आमतौर पर मिट्टी की सेहत के लिए अच्छी होती है।",
        },
    },
}


def build_advisory(crop: str, diagnosis: dict, weather: dict, ndvi: dict, lang: str = "en") -> dict:
    """
    Combine the three AI/data signals into a headline + list of point
    recommendations + one regenerative-practice tip.
    """
    kb = CROP_KNOWLEDGE.get(crop, CROP_KNOWLEDGE["Other"])[lang]
    points = []

    severity = (diagnosis.get("severity") or "unknown").lower()
    rain_7d = weather.get("rain_7d_mm")
    change_pct = ndvi.get("change_pct", 0)

    # --- Disease/health signal ---
    if severity in ("medium", "high"):
        if lang == "hi":
            points.append(f"⚠️ फोटो में {severity} स्तर की समस्या दिख रही है: {diagnosis.get('condition')}")
        else:
            points.append(f"⚠️ Photo shows a {severity}-severity concern: {diagnosis.get('condition')}")
    elif severity == "low":
        if lang == "hi":
            points.append(f"ℹ️ हल्की समस्या दिख रही है: {diagnosis.get('condition')}")
        else:
            points.append(f"ℹ️ Minor concern visible: {diagnosis.get('condition')}")
    if diagnosis.get("recommended_action"):
        points.append(diagnosis["recommended_action"])

    # --- Weather signal ---
    if isinstance(rain_7d, (int, float)):
        if rain_7d > 100:
            points.append(
                "🌧️ " + ("भारी बारिश हुई है — जलभराव से बचाव करें, नालियाँ साफ़ रखें।"
                          if lang == "hi" else
                          "Heavy rain recently — check drainage to avoid waterlogging.")
            )
        elif rain_7d < 5:
            points.append("💧 " + (kb["irrigation"] if lang == "hi" else kb["irrigation"]))

    points.append("🐛 " + kb["pest_watch"])

    # --- Vegetation trend signal ---
    if change_pct <= -15:
        headline = (
            "आपके खेत में तनाव के संकेत हैं — जल्द जांच करें"
            if lang == "hi" else
            "Your field shows signs of stress — worth checking soon"
        )
    elif change_pct <= -5:
        headline = (
            "आपका खेत सामान्य से थोड़ा कमज़ोर दिख रहा है"
            if lang == "hi" else
            "Your field looks slightly weaker than usual"
        )
    else:
        headline = (
            "आपका खेत सामान्य या बेहतर स्थिति में दिख रहा है"
            if lang == "hi" else
            "Your field looks stable or improving"
        )

    return {
        "headline": headline,
        "points": points,
        "regenerative_tip": kb["regenerative_tip"],
    }
