"""
Generates a simple loss-evidence PDF packet bundling the photo, diagnosis,
weather and vegetation-trend data captured in the Crop Advisory tab.

This is a BONUS feature (see app.py's second tab) — the core Track 4
submission is the advisory itself. This shows the same evidence has a
second real use.

Important framing, repeated here on purpose: this PDF supports a farmer's
own claim; it does not verify loss or decide any payout. Language reflects
that throughout.
"""

import io
import datetime as dt

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PIL import Image as PILImage


def build_evidence_pdf(
    farmer_name: str,
    crop: str,
    calamity: str,
    area_acres: float,
    event_date: str,
    diagnosis: dict,
    weather: dict,
    ndvi: dict,
    img_bytes: bytes,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
        title="Fasal Saakshi — Loss Evidence Packet",
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=18, textColor=colors.HexColor("#14532d"))
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12, textColor=colors.HexColor("#14532d"), spaceBefore=10)
    body = styles["BodyText"]
    warn = ParagraphStyle("warn", parent=body, textColor=colors.HexColor("#92400e"), fontSize=9)

    story = []
    story.append(Paragraph("Fasal Saakshi — Loss Evidence Packet", h1))
    story.append(Paragraph(f"Generated: {dt.datetime.now().strftime('%d %b %Y, %H:%M')}", body))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "This document supports a farmer-reported crop loss with photo, weather and "
        "vegetation-trend evidence. <b>It does not verify the loss or decide any claim "
        "or payout.</b> Please follow your scheme's official reporting channel and "
        "deadline in addition to this document.",
        warn,
    ))

    story.append(Paragraph("Report details", h2))
    rows = [
        ["Farmer name", farmer_name],
        ["Crop", crop],
        ["Calamity type", calamity],
        ["Affected area (approx.)", f"{area_acres} acres"],
        ["Date of event / concern", event_date],
    ]
    table = Table(rows, colWidths=[60 * mm, 100 * mm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0fdf4")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table)

    story.append(Paragraph("Photo evidence and AI-assisted read", h2))
    try:
        pil_img = PILImage.open(io.BytesIO(img_bytes))
        pil_img.thumbnail((400, 400))
        img_buf = io.BytesIO()
        pil_img.convert("RGB").save(img_buf, format="JPEG")
        img_buf.seek(0)
        story.append(RLImage(img_buf, width=80 * mm, height=80 * mm * pil_img.height / pil_img.width))
    except Exception:
        story.append(Paragraph("[photo could not be embedded]", body))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>Condition noted:</b> {diagnosis.get('condition', '—')}", body))
    story.append(Paragraph(f"<b>Severity:</b> {diagnosis.get('severity', '—')} &nbsp;&nbsp; <b>AI confidence:</b> {diagnosis.get('confidence', '—')}", body))

    story.append(Paragraph("Independent weather evidence", h2))
    story.append(Paragraph(
        f"Source: {weather.get('source', '—')}. Rainfall in the 7 days around the event: "
        f"<b>{weather.get('rain_7d_mm', '—')} mm</b>. Summary: {weather.get('summary', '—')}",
        body,
    ))
    story.append(Paragraph(
        "Note: weather data shows conditions <i>consistent with</i> the reported calamity; "
        "it does not confirm a specific field-level event such as hail.",
        warn,
    ))

    story.append(Paragraph("Vegetation-trend evidence", h2))
    story.append(Paragraph(
        f"Change vs. approx. 2 weeks earlier: <b>{ndvi.get('change_pct', '—')}%</b>. {ndvi.get('note', '')}",
        body,
    ))

    doc.build(story)
    return buf.getvalue()
