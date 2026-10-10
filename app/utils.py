"""Utility helpers: AI client, PDF generation, data validation."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

import matplotlib
import pandas as pd
from groq import Groq
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

try:
    from .formatting import indian_currency
except ImportError:
    from formatting import indian_currency

try:
    from .config import CONFIG
except ImportError:
    from config import CONFIG

logger = logging.getLogger(__name__)
def _register_report_font(text: str) -> str | None:
    if not any(ord(character) > 127 for character in text):
        return None
    arabic_text = any(0x0600 <= ord(character) <= 0x08FF for character in text)
    bundled_dejavu = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"
    if arabic_text:
        font_candidates = [
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            bundled_dejavu,
        ]
        font_name = "NorthstarArabic"
    else:
        font_candidates = [
            Path("C:/Windows/Fonts/Nirmala.ttc"),
            Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            bundled_dejavu,
        ]
        font_name = "NorthstarIndic"
    if font_name in pdfmetrics.getRegisteredFontNames():
        return font_name
    font_path = next((candidate for candidate in font_candidates if candidate.is_file()), None)
    if font_path is None:
        raise FileNotFoundError(
            "A Unicode font is required for this translated PDF. Install Nirmala UI or Noto Sans."
        )
    pdfmetrics.registerFont(TTFont(font_name, str(font_path), subfontIndex=0))
    return font_name


# ── AI client ──────────────────────────────────────────────────────────────

_groq_client: Groq | None = None


def get_groq_client() -> Groq | None:
    global _groq_client
    if _groq_client is None and CONFIG.groq_api_key:
        _groq_client = Groq(api_key=CONFIG.groq_api_key)
    return _groq_client


def ask_genai(prompt: str, system: str = "You are a senior business data analyst.") -> str:
    """Return a GenAI response or a user-friendly error string."""
    client = get_groq_client()
    if client is None:
        return "⚠️ GenAI unavailable — set GROQ_API_KEY in your .env file."

    try:
        response = client.chat.completions.create(
            model=CONFIG.groq_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=CONFIG.groq_temperature,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as exc:
        logger.error("GenAI request failed: %s", exc)
        return f"⚠️ GenAI request failed: {exc}"


# ── PDF generation ──────────────────────────────────────────────────────────

def generate_pdf(report_text: str, title: str = "Business Intelligence Report") -> Path:
    """Render *report_text* to a styled PDF and return its path."""
    font_name = _register_report_font(f"{title}\n{report_text}")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    out_path = CONFIG.reports_dir / f"BI_Report_{timestamp}.pdf"

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=20,
        spaceAfter=20,
        fontName=font_name or "Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=11,
        leading=16,
        spaceAfter=8,
        fontName=font_name or "Helvetica",
    )
    heading_style = ParagraphStyle(
        "ReportHeading",
        parent=styles["Heading2"],
        fontName=font_name or "Helvetica-Bold",
    )

    story = [Paragraph(escape(title), title_style), Spacer(1, 0.5 * cm)]
    for line in report_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 0.3 * cm))
        elif stripped.startswith("#"):
            heading_text = stripped.lstrip("#").strip()
            story.append(Paragraph(escape(heading_text), heading_style))
        else:
            story.append(Paragraph(escape(stripped), body_style))

    doc.build(story)
    return out_path


# ── Data validation ──────────────────────────────────────────────────────────

class DataValidationError(ValueError):
    pass


def validate_dataframe(df: pd.DataFrame) -> list[str]:
    """Return a list of warning strings (empty = all OK)."""
    warnings: list[str] = []
    missing_cols = [c for c in CONFIG.required_columns if c not in df.columns]
    if missing_cols:
        warnings.append(f"Missing columns: {', '.join(missing_cols)}")
    null_count = int(df.isnull().sum().sum())
    if null_count:
        warnings.append(f"{null_count:,} null values found — consider cleaning before analysis.")
    if len(df) < 10:
        warnings.append("Dataset is very small (< 10 rows); insights may not be meaningful.")
    return warnings


def format_currency(value: float) -> str:
    return indian_currency(value)


def format_pct(value: float) -> str:
    return f"{value:.1%}"