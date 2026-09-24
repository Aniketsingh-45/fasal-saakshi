"""
Weather lookup using Open-Meteo (https://open-meteo.com) — free, no API key
needed for non-commercial use. Check their terms before any commercial/production use.

Provides:
  - current/recent conditions for a lat/lon
  - total rainfall over the last 7 days (a simple proxy signal for waterlogging/flood risk)

This is real, live data — not mocked — as long as the app has internet access.
"""

import datetime as dt
import requests
import streamlit as st

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


@st.cache_data(ttl=1800, show_spinner=False)
def get_weather_summary(lat: float, lon: float, event_date: dt.date) -> dict:
    """
    Returns a dict with today's temperature, 7-day rainfall total ending on
    `event_date`, and a short plain-language summary.

    Uses the forecast API for recent/upcoming dates, and the archive API for
    dates more than a couple of days in the past.
    """
    today = dt.date.today()
    is_recent = (today - event_date).days <= 2

    try:
        if is_recent:
            resp = requests.get(
                FORECAST_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,precipitation,weather_code",
                    "daily": "precipitation_sum",
                    "past_days": 7,
                    "forecast_days": 1,
                    "timezone": "auto",
                },
                timeout=10,
            )
            data = resp.json()
            temp_c = data.get("current", {}).get("temperature_2m")
            rain_series = data.get("daily", {}).get("precipitation_sum", [])
        else:
            start = (event_date - dt.timedelta(days=7)).isoformat()
            end = event_date.isoformat()
            resp = requests.get(
                ARCHIVE_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "start_date": start,
                    "end_date": end,
                    "daily": "precipitation_sum,temperature_2m_max",
                    "timezone": "auto",
                },
                timeout=10,
            )
            data = resp.json()
            rain_series = data.get("daily", {}).get("precipitation_sum", [])
            temps = data.get("daily", {}).get("temperature_2m_max", [])
            temp_c = temps[-1] if temps else None

        rain_7d = round(sum(v for v in rain_series if v is not None), 1) if rain_series else 0.0

        if rain_7d > 100:
            summary = "Heavy rainfall in the last 7 days — consistent with waterlogging/flood risk."
        elif rain_7d > 40:
            summary = "Moderate rainfall in the last 7 days."
        elif rain_7d < 5:
            summary = "Very little rain in the last 7 days — dry conditions."
        else:
            summary = "Normal rainfall range for the last 7 days."

        return {
            "temp_c": round(temp_c, 1) if temp_c is not None else "—",
            "rain_7d_mm": rain_7d,
            "summary": summary,
            "source": "Open-Meteo (live)",
        }

    except Exception as e:  # noqa: BLE001
        return {
            "temp_c": "—",
            "rain_7d_mm": "—",
            "summary": f"[Weather lookup failed: {e}]",
            "source": "unavailable",
        }
