"""
Fasal Saakshi — AI-powered, localised crop advisory for small farmers.

Built for: Build with AI — Code for Communities, Second Edition
Track 4 — AgriN & Regenerative Agricultural Intelligence

Core flow:
  1. Farmer uploads/takes a photo of their crop -> Gemini vision diagnoses disease/health
  2. Farmer's plot location + date -> weather is fetched (Open-Meteo, free, no key needed)
  3. A simple vegetation-trend proxy (NDVI-style) is shown for the plot (demo data,
     to be swapped for a real Google Earth Engine query — see satellite.py)
  4. An advisory engine combines disease + weather + vegetation trend into one
     plain-language recommendation (irrigation, pest risk, sowing/harvest timing,
     and a regenerative-practice tip)
  5. Bonus tab: if the farmer suffered a loss, the same evidence (photo + weather +
     vegetation change) is bundled into a downloadable "loss evidence packet" PDF
     that can support an insurance claim intimation

IMPORTANT — run this yourself before demoing:
  - You need a free Gemini API key from https://aistudio.google.com/apikey
  - Put it in .streamlit/secrets.toml as GEMINI_API_KEY = "..."
    (a template file, secrets.toml.example, is included)
  - All farmer photos/voice used in your demo should be your own or clearly
    synthetic/staged. Do not use real children's or real farmers' data without consent.
"""

import os
import io
import json
import datetime as dt

# pyrefly: ignore [missing-import]
import streamlit as st

from gemini_client import (
    diagnose_crop_photo,
    extract_report_from_text,
    get_api_key,
    is_gemini_available,
)
from weather import get_weather_summary
from satellite import get_ndvi_trend
from advisory import build_advisory
from evidence_pdf import build_evidence_pdf

st.set_page_config(page_title="Fasal Saakshi", page_icon="🌾", layout="wide")

# ---------------------------------------------------------------------------
# Sidebar — plot + language setup (kept once per session)
# ---------------------------------------------------------------------------
st.sidebar.title("🌾 Fasal Saakshi")
st.sidebar.caption("AI crop advisory + loss-evidence assistant for small farmers")

st.sidebar.markdown("### Plot details")
crop = st.sidebar.selectbox("Crop", ["Wheat", "Rice (Paddy)", "Cotton", "Other"])
state = st.sidebar.selectbox(
    "State (demo plots have real weather/NDVI data)",
    ["Bihar — demo plot A", "Punjab — demo plot B", "Other (no demo data)"],
)
lat, lon = {
    "Bihar — demo plot A": (25.0961, 85.3131),   # Patna region
    "Punjab — demo plot B": (30.7333, 76.7794),  # near Chandigarh
    "Other (no demo data)": (20.5937, 78.9629),  # India centroid fallback
}[state]
plot_date = st.sidebar.date_input("Date of concern / event", dt.date.today())
lang = st.sidebar.radio("Language / भाषा", ["English", "हिंदी (Hindi)"], horizontal=True)

st.sidebar.markdown("---")
st.sidebar.caption(
    "⚠️ Demo prototype. Weather is live (Open-Meteo). Vegetation trend uses "
    "illustrative sample data — replace `satellite.py` with a real Google Earth "
    "Engine query before relying on it. AI outputs are suggestions, not agronomic "
    "or insurance decisions."
)

L = lang.startswith("हिंदी")

def t(en, hi):
    """Tiny inline translation helper."""
    return hi if L else en

# Sidebar Gemini Status & API Key configuration
st.sidebar.markdown("---")
st.sidebar.markdown(f"### {t('🤖 Gemini AI Setup', '🤖 Gemini AI सेटअप')}")
current_key = get_api_key()
if is_gemini_available():
    st.sidebar.success(t("🟢 Gemini Vision AI: Active", "🟢 Gemini AI: सक्रिय"))
else:
    st.sidebar.warning(t("🟠 Gemini AI: Demo Mode (No Key)", "🟠 Gemini AI: डेमो मोड (की नहीं मिली)"))

key_input = st.sidebar.text_input(
    t("Gemini API Key", "Gemini API कुंजी"),
    value=current_key,
    type="password",
    help=t(
        "Free key from https://aistudio.google.com/apikey",
        "https://aistudio.google.com/apikey से मुफ्त की प्राप्त करें",
    ),
    key="sidebar_gemini_key",
)
if key_input and key_input.strip() != current_key:
    new_key = key_input.strip()
    st.session_state["user_gemini_api_key"] = new_key
    secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
    try:
        os.makedirs(os.path.dirname(secrets_path), exist_ok=True)
        with open(secrets_path, "w", encoding="utf-8") as f:
            f.write(f'GEMINI_API_KEY = "{new_key}"\n')
    except Exception:
        pass
    st.sidebar.success(t("API Key saved!", "API कुंजी सहेजी गई!"))
    st.rerun()

st.title(t("Fasal Saakshi — Crop Advisory", "फसल साक्षी — फसल सलाह"))
st.caption(
    t(
        "Photo-based disease check, weather- and satellite-aware advisory, "
        "and a loss-evidence packet — all from one photo and a few taps.",
        "फोटो से बीमारी की पहचान, मौसम और उपग्रह डेटा पर आधारित सलाह, "
        "और नुकसान का सबूत — एक फोटो और कुछ टैप से।",
    )
)

tab_advisory, tab_evidence, tab_about = st.tabs(
    [
        t("🌱 Crop Advisory", "🌱 फसल सलाह"),
        t("📋 Loss Evidence (bonus)", "📋 नुकसान का सबूत"),
        t("ℹ️ About / Limitations", "ℹ️ जानकारी"),
    ]
)

# ---------------------------------------------------------------------------
# TAB 1 — Crop Advisory (the core of the Track 4 submission)
# ---------------------------------------------------------------------------
with tab_advisory:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader(t("1. Photograph the crop", "1. फसल की फोटो लें"))

        # Camera On/Off Toggle button
        enable_camera = st.toggle(
            t("📷 Camera: ON / OFF", "📷 कैमरा: चालू / बंद"),
            value=False,
            help=t(
                "Turn ON only when taking a photo. Keep OFF to close camera and save battery/privacy.",
                "फोटो लेने के लिए चालू करें। कैमरा बंद रखने के लिए ऑफ रखें।",
            ),
            key="camera_toggle",
        )

        if enable_camera:
            cam_photo = st.camera_input(t("Take a photo", "फोटो लें"), key="crop_camera")
            if cam_photo is not None:
                st.session_state["active_crop_photo"] = cam_photo.getvalue()
            st.caption(
                t(
                    "💡 Camera is active. After snapping the photo, you can turn the toggle OFF to close the camera.",
                    "💡 कैमरा चालू है। फोटो खींचने के बाद आप कैमरा बंद करने के लिए टॉगल OFF कर सकते हैं।",
                )
            )

        uploaded_photo = st.file_uploader(
            t("📁 ...or upload a photo", "📁 ...या फोटो अपलोड करें"),
            type=["jpg", "jpeg", "png"],
            key="crop_uploader",
        )
        if uploaded_photo is not None:
            st.session_state["active_crop_photo"] = uploaded_photo.getvalue()

        img_bytes = st.session_state.get("active_crop_photo")

        if img_bytes:
            if not enable_camera:
                st.image(
                    img_bytes,
                    caption=t("Photo ready for analysis", "जांच के लिए चुनी गई फोटो"),
                    width=260,
                )
            if st.button(t("🗑️ Remove photo", "🗑️ फोटो हटाएं"), key="clear_crop_photo"):
                st.session_state.pop("active_crop_photo", None)
                st.rerun()

        note = st.text_area(
            t(
                "Optional: describe what you see (voice note would go here in production)",
                "वैकल्पिक: जो दिख रहा है वह लिखें (असली ऐप में यहाँ आवाज़ का संदेश होगा)",
            ),
            placeholder=t(
                "e.g. yellow spots on lower leaves since 3 days",
                "जैसे: नीचे के पत्तों पर 3 दिन से पीले धब्बे",
            ),
        )
        run = st.button(t("Get advisory", "सलाह पाएं"), type="primary", use_container_width=True)

    with col2:
        st.subheader(t("2. What Fasal Saakshi checks", "2. फसल साक्षी क्या जांचता है"))
        st.markdown(
            t(
                """
- 🩺 **Disease/health check** — Gemini vision reads the photo
- 🌦️ **Weather** — live forecast and recent conditions for your plot
- 🛰️ **Vegetation trend** — is the field greener or more stressed than 2 weeks ago
- 🌍 **Regenerative tip** — one practical, low-cost practice for this crop and season
                """,
                """
- 🩺 **बीमारी की जांच** — फोटो से Gemini AI बीमारी पहचानता है
- 🌦️ **मौसम** — आपके खेत के लिए ताज़ा पूर्वानुमान
- 🛰️ **वनस्पति रुझान** — खेत 2 हफ्ते पहले से बेहतर है या कमज़ोर
- 🌍 **टिकाऊ खेती सुझाव** — इस फसल और मौसम के लिए एक आसान उपाय
                """,
            )
        )

    if run:
        if not img_bytes:
            st.warning(t("Please add a photo first (take a photo or upload).", "कृपया पहले एक फोटो जोड़ें (फोटो लें या अपलोड करें)।"))
        else:

            with st.spinner(t("Analysing photo with AI...", "AI से फोटो जांची जा रही है...")):
                diagnosis = diagnose_crop_photo(img_bytes, crop=crop, note=note)

            with st.spinner(t("Fetching weather...", "मौसम की जानकारी ली जा रही है...")):
                weather = get_weather_summary(lat, lon, plot_date)

            with st.spinner(t("Checking vegetation trend...", "वनस्पति रुझान देखा जा रहा है...")):
                ndvi = get_ndvi_trend(lat, lon, plot_date)

            advisory = build_advisory(crop, diagnosis, weather, ndvi, lang="hi" if L else "en")

            st.session_state["last_result"] = {
                "img_bytes": img_bytes,
                "diagnosis": diagnosis,
                "weather": weather,
                "ndvi": ndvi,
                "advisory": advisory,
                "crop": crop,
                "state": state,
                "date": str(plot_date),
            }

    result = st.session_state.get("last_result")
    if result:
        st.markdown("---")
        r1, r2, r3 = st.columns(3)

        with r1:
            st.markdown(f"#### {t('🩺 Diagnosis', '🩺 बीमारी जांच')}")
            d = result["diagnosis"]
            st.metric(t("Crop visible", "फसल दिखी"), d.get("crop_visible", "unsure"))
            st.write(f"**{t('Condition', 'हालत')}:** {d.get('condition', '—')}")
            st.write(f"**{t('Confidence', 'भरोसा')}:** {d.get('confidence', '—')}")
            if d.get("recommended_action"):
                st.info(d["recommended_action"])

        with r2:
            st.markdown(f"#### {t('🌦️ Weather', '🌦️ मौसम')}")
            w = result["weather"]
            st.metric(t("Today", "आज"), f"{w.get('temp_c', '—')}°C")
            st.write(f"**{t('Rain (7 days)', 'बारिश (7 दिन)')}:** {w.get('rain_7d_mm', '—')} mm")
            st.write(f"**{t('Condition', 'हालत')}:** {w.get('summary', '—')}")

        with r3:
            st.markdown(f"#### {t('🛰️ Vegetation trend', '🛰️ वनस्पति रुझान')}")
            n = result["ndvi"]
            st.metric(
                t("Change vs 2 weeks ago", "2 हफ्ते पहले से बदलाव"),
                f"{n.get('change_pct', 0):+.1f}%",
            )
            st.caption(n.get("note", ""))

        st.markdown("---")
        st.markdown(f"### {t('✅ Advisory for your field', '✅ आपके खेत के लिए सलाह')}")
        st.success(result["advisory"]["headline"])
        for point in result["advisory"]["points"]:
            st.markdown(f"- {point}")
        st.caption(
            t(
                "🌍 Regenerative tip: " + result["advisory"]["regenerative_tip"],
                "🌍 टिकाऊ खेती सुझाव: " + result["advisory"]["regenerative_tip"],
            )
        )

# ---------------------------------------------------------------------------
# TAB 2 — Loss evidence packet (bonus feature, reuses the same data)
# ---------------------------------------------------------------------------
with tab_evidence:
    st.subheader(t("Prepare loss evidence for an insurance claim", "बीमा दावे के लिए सबूत तैयार करें"))
    st.caption(
        t(
            "If your crop was damaged by a calamity (hail, flood, pest), this uses the "
            "same photo, weather and satellite check to prepare a document you can attach "
            "when you report the loss. This tool does not decide your claim or payout.",
            "अगर आपकी फसल को नुकसान हुआ है (ओला, बाढ़, कीट), तो यह वही फोटो, मौसम और "
            "उपग्रह जांच इस्तेमाल करके एक दस्तावेज़ बनाता है, जिसे आप नुकसान की सूचना "
            "देते समय जोड़ सकते हैं। यह टूल दावा या भुगतान तय नहीं करता।",
        )
    )

    result = st.session_state.get("last_result")
    if not result:
        st.info(
            t(
                "Run the Crop Advisory tab first — this reuses that photo, weather and "
                "vegetation data.",
                "पहले 'फसल सलाह' टैब चलाएं — यह वही फोटो, मौसम और वनस्पति डेटा उपयोग करता है।",
            )
        )
    else:
        calamity = st.selectbox(
            t("Type of calamity", "आपदा का प्रकार"),
            ["Hail", "Flood", "Pest attack", "Drought", "Fire", "Other"],
        )
        area = st.number_input(t("Approx. affected area (acres)", "प्रभावित क्षेत्र (एकड़)"), min_value=0.1, value=1.0, step=0.1)
        farmer_name = st.text_input(t("Farmer name (for the document header)", "किसान का नाम"))

        if st.button(t("Generate evidence packet (PDF)", "सबूत दस्तावेज़ बनाएं (PDF)")):
            pdf_bytes = build_evidence_pdf(
                farmer_name=farmer_name or "—",
                crop=result["crop"],
                calamity=calamity,
                area_acres=area,
                event_date=result["date"],
                diagnosis=result["diagnosis"],
                weather=result["weather"],
                ndvi=result["ndvi"],
                img_bytes=result["img_bytes"],
            )
            st.download_button(
                t("⬇️ Download evidence packet", "⬇️ सबूत दस्तावेज़ डाउनलोड करें"),
                data=pdf_bytes,
                file_name="fasal_saakshi_evidence_packet.pdf",
                mime="application/pdf",
            )
            st.warning(
                t(
                    "This packet supports your claim; it is not a substitute for the official "
                    "intimation channel (app/helpline/bank) or the reporting deadline under your scheme.",
                    "यह दस्तावेज़ आपके दावे में मदद करता है; यह आधिकारिक सूचना (ऐप/हेल्पलाइन/बैंक) "
                    "या आपकी योजना की समय-सीमा का विकल्प नहीं है।",
                )
            )

# ---------------------------------------------------------------------------
# TAB 3 — About / limitations (for judges)
# ---------------------------------------------------------------------------
with tab_about:
    st.markdown(
        """
### What this prototype demonstrates
- **Google AI (Gemini) integration**: crop photo → structured diagnosis (JSON), used to
  drive the advisory — not just a raw chat prompt.
- **Real weather data**: live Open-Meteo API call for the selected plot and date.
- **Vegetation trend**: currently **illustrative sample data** standing in for a Google
  Earth Engine NDVI query (see `satellite.py` — the real query is stubbed and documented,
  since Earth Engine needs a registered service account which is outside a quick demo).
- **Advisory engine**: combines all three signals with simple, explainable rules — the
  LLM phrases the message, code decides the thresholds.
- **Bonus**: the same evidence turns into a downloadable loss-evidence PDF for insurance
  claims, showing the data has more than one real use.

### Honest limitations (please read before judging the "vegetation trend" numbers)
1. **NDVI is currently simulated**, not a live satellite pull. Swapping in a real Earth
   Engine call is the top item on the roadmap — the interface is already built for it.
2. Disease diagnosis is a **suggestion**, not a lab-verified diagnosis. It should always
   be confirmed by a local agriculture officer before acting on it for high-value decisions.
3. Weather-based rain/heat signals are **conditions consistent with** a risk, not proof.
4. No real farmer data was used in this demo — photos are either the developer's own or
   clearly staged/sample images.
5. Multilingual support currently covers English and Hindi; more Indian languages are the
   next step, using Cloud Translation / Speech-to-Text as listed in the challenge's tech list.

### Cross-border / BRICS applicability
Crop names, calamity types, weather thresholds and scheme references are kept in
`advisory.py` and `evidence_pdf.py` as simple, swappable lists/config rather than hardcoded
logic, so the same core (photo diagnosis + weather + vegetation trend + advisory) can be
re-pointed at another country's crops and climate by changing that config, not the code.
        """
    )
