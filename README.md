# 🌾 Fasal Saakshi

AI-powered, localised crop advisory for small farmers — with a bonus loss-evidence
packet for insurance claims.

Built for **Build with AI: Code for Communities, Second Edition**
**Track 4 — AgriN & Regenerative Agricultural Intelligence**

## What it does

1. **Photo-based crop check** — farmer photographs their crop; Gemini vision gives a
   plain-language condition read, severity and a recommended next step.
2. **Localised weather** — live 7-day rainfall and current temperature for the plot
   (Open-Meteo, free, no key needed).
3. **Vegetation trend** — a change-vs-2-weeks-ago signal for the plot (**currently
   simulated sample data** standing in for a Google Earth Engine NDVI query — see
   `satellite.py` for exactly what to swap in and why).
4. **Advisory engine** — combines all three signals into one explainable
   recommendation (irrigation, pest watch, and a regenerative-practice tip),
   in English or Hindi.
5. **Bonus: loss-evidence packet** — if the farmer suffered a calamity, the same
   photo + weather + vegetation data becomes a downloadable PDF to support an
   insurance claim. This tool prepares evidence; it never decides a claim or payout.

## Why this design

- **AI does the reading, code does the deciding.** Gemini reads the photo and
  phrases advice; the advisory thresholds (severity, rainfall, vegetation change)
  are explicit rules in `advisory.py`, not left to the model — so the output is
  explainable and consistent.
- **Cross-border ready.** Crop-specific knowledge and thresholds live in a
  swappable config (`CROP_KNOWLEDGE` in `advisory.py`), not hardcoded logic, so
  the same core can be re-pointed at another country's crops/climate.
- **Honest about the one simulated piece.** The vegetation-trend signal is the one
  part of this prototype that is not live data. That's stated on-screen, in this
  README, and in code comments — see "Limitations" below.

## Run it locally

```bash
git clone <your-repo-url>
cd fasal-saakshi
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Add your Gemini API key (free): https://aistudio.google.com/apikey
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit .streamlit/secrets.toml and paste your key

streamlit run app.py
```

The app also runs **without** a key, in a clearly-labelled demo mode (diagnosis
text will say `[DEMO MODE]`) — useful for testing the UI, but get a real key
before recording your demo video.

## Deploy it (free, ~10 minutes)

**Streamlit Community Cloud** (recommended, easiest):
1. Push this repo to GitHub (public).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub.
3. "New app" → pick this repo → main file `app.py`.
4. In **App settings → Secrets**, paste the same content as your
   `secrets.toml` (with your real key).
5. Deploy. You'll get a public `*.streamlit.app` URL — this is your
   "working prototype link".

## Tech stack

- **Google AI**: Gemini API (`google-genai` SDK) for vision-based crop
  diagnosis and text extraction — required per the hackathon rules.
- **Weather**: Open-Meteo (free, live, no key).
- **Vegetation trend**: simulated placeholder; designed to be swapped for
  **Google Earth Engine** (see `satellite.py` docstring for the exact query shape).
- **PDF generation**: ReportLab.
- **UI**: Streamlit.

## Honest limitations

1. **Vegetation-trend data is simulated**, not a live satellite pull (Earth Engine
   needs an approved service account, which doesn't fit a short build window).
   The interface is built so a real query can be dropped in without touching
   the rest of the app.
2. Disease diagnosis is an **AI suggestion**, not a verified lab diagnosis —
   always confirm with a local agriculture officer before high-stakes decisions.
3. Weather signals show conditions *consistent with* a risk, not proof of a
   specific field-level event.
4. No real farmer data was used in building/testing this demo.
5. Currently English + Hindi only; more Indian languages are the next step
   (Cloud Translation / Speech-to-Text, as listed in the challenge's tech list).

## Roadmap

- Real Google Earth Engine NDVI integration (swap `satellite.py`)
- More Indian languages via Cloud Translation + Speech-to-Text
- Per-district crop/threshold config for state-by-state scaling
- Farmer-side WhatsApp interface (voice-first) instead of a web form
- Officer-side dashboard for the bonus evidence-packet flow

## Team

TheUnique — solo build.
