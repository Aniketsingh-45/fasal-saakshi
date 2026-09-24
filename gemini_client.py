"""
Thin wrapper around the Gemini API (Google AI Studio) for:
  - diagnosing a crop photo (disease / health / severity)
  - extracting a structured report from free-text/voice-transcript input

Uses the current `google-genai` SDK (the older `google-generativeai` package
is deprecated as of 2025 — do not use it). You need a free API key from
https://aistudio.google.com/apikey, placed in .streamlit/secrets.toml as:

    GEMINI_API_KEY = "your-key-here"

If no key is configured, this module falls back to a clearly-labelled mock
response so the rest of the app can still be demoed/tested offline.

Model name note: "gemini-2.5-flash" is used below as a fast, cheap, vision-
capable default at the time of writing. Model names and availability change —
check https://ai.google.dev/gemini-api/docs/models before your demo and
update MODEL_NAME below if needed.
"""

import json
import re

import streamlit as st

try:
    from google import genai
    from google.genai import types
    _HAS_SDK = True
except ImportError:
    _HAS_SDK = False

MODEL_NAME = "gemini-3.6-flash"


import os
import io
from PIL import Image

def get_api_key() -> str:
    """Retrieve Gemini API key from session state, st.secrets, environment, or secrets.toml file."""
    # 1. Check session state
    try:
        if "user_gemini_api_key" in st.session_state and st.session_state["user_gemini_api_key"].strip():
            return st.session_state["user_gemini_api_key"].strip()
    except Exception:
        pass

    # 2. Check environment variable
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key and env_key not in ("paste-your-key-here", "your-key-here"):
        return env_key

    # 3. Check st.secrets
    try:
        secret_key = st.secrets.get("GEMINI_API_KEY", "")
        if isinstance(secret_key, str) and secret_key.strip() and secret_key.strip() not in ("paste-your-key-here", "your-key-here"):
            return secret_key.strip()
    except Exception:
        pass

    # 4. Check .streamlit/secrets.toml directly from disk
    secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        try:
            import tomllib
            with open(secrets_path, "rb") as f:
                data = tomllib.load(f)
                k = str(data.get("GEMINI_API_KEY", "")).strip()
                if k and k not in ("paste-your-key-here", "your-key-here"):
                    return k
        except Exception:
            pass

    return ""


def is_gemini_available() -> bool:
    """Return True if the SDK is installed and an API key is configured."""
    return _HAS_SDK and bool(get_api_key())


def _get_client():
    if not _HAS_SDK:
        return None
    api_key = get_api_key()
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def _extract_json(text: str) -> dict:
    """Pull the first {...} block out of a model response, defensively."""
    # Strip markdown code blocks ```json ... ```
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model response: {text[:100]}")
    return json.loads(match.group(0))


DIAGNOSIS_PROMPT = """You are an agricultural assistant looking at a photo of a
{crop} plant, provided by a small farmer in India. The farmer's note (may be empty): "{note}"

Look ONLY at what is visible in the photo. Do not invent details.

Return ONLY a JSON object with this exact shape, no other text:
{{
  "crop_visible": "yes" | "no" | "unsure",
  "condition": "short plain-language description of what you see, e.g. 'yellowing on lower leaves, possible nitrogen deficiency or early blight'",
  "severity": "none" | "low" | "medium" | "high",
  "confidence": "low" | "medium" | "high",
  "recommended_action": "one short, practical, non-branded suggestion (e.g. consult local Krishi Vigyan Kendra / agriculture officer to confirm before applying any treatment)"
}}
"""


def diagnose_crop_photo(img_bytes: bytes, crop: str, note: str = "") -> dict:
    """Send a crop photo to Gemini vision and return a structured diagnosis dict."""
    client = _get_client()
    prompt = DIAGNOSIS_PROMPT.format(crop=crop, note=note or "none")

    if client is None:
        # Offline / no-API-key fallback so the UI remains testable.
        return {
            "crop_visible": "unsure",
            "condition": "[DEMO MODE — no Gemini API key configured. This is placeholder "
                         "text, not a real diagnosis. Add GEMINI_API_KEY in "
                         ".streamlit/secrets.toml or sidebar to get real results.]",
            "severity": "unknown",
            "confidence": "low",
            "recommended_action": "Configure your Gemini API key to enable real diagnosis.",
        }

    try:
        # Convert any input format (PNG, WebP, JPEG) to a standardized RGB JPEG byte stream
        pil_img = Image.open(io.BytesIO(img_bytes))
        buf = io.BytesIO()
        pil_img.convert("RGB").save(buf, format="JPEG")
        clean_jpeg_bytes = buf.getvalue()

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                prompt,
                types.Part.from_bytes(data=clean_jpeg_bytes, mime_type="image/jpeg"),
            ],
        )
        return _extract_json(response.text)
    except Exception as e:  # noqa: BLE001 - surface any API/parsing error to the UI
        return {
            "crop_visible": "unsure",
            "condition": f"[Error calling Gemini: {e}]",
            "severity": "unknown",
            "confidence": "low",
            "recommended_action": "Retry, or check your API key and quota.",
        }


EXTRACTION_PROMPT = """Extract a structured incident report from this farmer's message
(may be in Hindi, English, or Hinglish): "{text}"

Return ONLY a JSON object with this exact shape, no other text:
{{
  "crop": "string or null",
  "issue_type": "disease" | "pest" | "weather_damage" | "other" | "unknown",
  "description": "short plain-language summary",
  "area_value": number or null,
  "area_unit": "acre" | "hectare" | "bigha" | null,
  "uncertain_fields": ["list", "of", "field", "names", "that", "were", "unclear"]
}}
"""


def extract_report_from_text(text: str) -> dict:
    """Turn a free-text (or voice-transcript) farmer message into structured JSON."""
    client = _get_client()
    if client is None or not text.strip():
        return {
            "crop": None,
            "issue_type": "unknown",
            "description": text or "[no input]",
            "area_value": None,
            "area_unit": None,
            "uncertain_fields": ["all — demo mode or empty input"],
        }
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=EXTRACTION_PROMPT.format(text=text),
        )
        return _extract_json(response.text)
    except Exception as e:  # noqa: BLE001
        return {
            "crop": None,
            "issue_type": "unknown",
            "description": f"[Error calling Gemini: {e}]",
            "area_value": None,
            "area_unit": None,
            "uncertain_fields": ["all"],
        }
