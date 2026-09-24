"""
Vegetation-trend (NDVI-style) signal for a plot.

*** CURRENT STATE: SIMULATED DATA — READ THIS BEFORE YOUR DEMO ***

A real implementation would query Google Earth Engine for Sentinel-2 NDVI
(or Sentinel-1 radar for flood/cloud-covered cases) before and after the
date of interest, for the plot and for nearby unaffected fields, and report
the difference. That requires:
  1. A Google Earth Engine account (sign up at https://earthengine.google.com,
     free for research/non-commercial use, approval is not instant)
  2. A service account + credentials JSON
  3. The `earthengine-api` Python package

Because that approval step doesn't fit a short hackathon build window, this
module currently returns clearly-labelled sample/illustrative data so the
rest of the product (advisory engine, evidence packet) can be built and
demoed end-to-end. Swap `get_ndvi_trend` below for a real Earth Engine query
— the function signature and return shape are already what the rest of the
app expects, so nothing else needs to change.

Example of what the real query would look like (pseudocode, not run here):

    import ee
    ee.Initialize()
    point = ee.Geometry.Point([lon, lat])
    before = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
              .filterBounds(point)
              .filterDate(event_date - 14days, event_date - 7days)
              .median())
    after = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
              .filterBounds(point)
              .filterDate(event_date, event_date + 7days)
              .median())
    ndvi_before = before.normalizedDifference(['B8', 'B4'])
    ndvi_after = after.normalizedDifference(['B8', 'B4'])
    # ... reduceRegion() over the plot polygon to get mean NDVI for each
"""

import datetime as dt
import hashlib


def get_ndvi_trend(lat: float, lon: float, event_date: dt.date) -> dict:
    """
    Returns an illustrative vegetation-trend signal for the plot.

    NOTE: This is SIMULATED, deterministic-per-location sample data, not a
    live satellite pull. It is seeded from the lat/lon/date so the same plot
    always shows the same demo number (useful for a consistent demo), but it
    is NOT real. See module docstring for how to wire up real Earth Engine data.
    """
    seed_str = f"{round(lat, 2)}-{round(lon, 2)}-{event_date.isocalendar()[1]}"
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16) % 1000

    # Deterministic pseudo-random change between -25% and +15%, biased slightly
    # negative to represent "typical" seasonal stress for the demo.
    change_pct = round((seed / 1000) * 40 - 25, 1)

    if change_pct <= -15:
        note = (
            "[SIMULATED DATA] Vegetation index has dropped notably vs. 2 weeks ago — "
            "consistent with crop stress or damage. Replace with real Earth Engine "
            "NDVI before relying on this for any real decision."
        )
    elif change_pct <= -5:
        note = (
            "[SIMULATED DATA] Small decline in vegetation index — could be normal "
            "seasonal variation or early stress. Not yet verified against real satellite data."
        )
    else:
        note = (
            "[SIMULATED DATA] Vegetation index is stable or improving. "
            "Not yet verified against real satellite data."
        )

    return {
        "change_pct": change_pct,
        "note": note,
        "source": "simulated — see satellite.py for real Earth Engine integration",
    }
