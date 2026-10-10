"""Reusable Streamlit components for the business intelligence dashboard."""
from __future__ import annotations

import streamlit as st

from formatting import indian_currency


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
        :root { --ink:#182230; --muted:#64748b; --line:#e2e8f0; --panel:#ffffff; --accent:#625bd8; }
        .stApp { background:#f5f7fb; color:var(--ink); }
        html, body, [class*="css"] { font-family:'DM Sans','Nirmala UI','Noto Sans',sans-serif; }
        h1,h2,h3 { font-family:'Manrope',sans-serif; letter-spacing:-.035em; }
        [data-testid="stSidebar"] { background:#ffffff; border-right:1px solid var(--line); }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#526174; }
        [data-testid="stSidebar"] [data-testid="stRadio"] label { border-radius:10px; padding:5px 8px; color:#243247; }
        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:#f1f2ff; }
        .block-container { max-width:1500px; padding-top:2rem; padding-bottom:3rem; }
        .hero { border:1px solid #e4e6f5; border-radius:22px; padding:26px 30px; margin:0 0 24px; background:linear-gradient(115deg,#f0efff,#f1fbf8 62%,#ffffff); box-shadow:0 8px 28px rgba(34,48,73,.04); }
        .hero-kicker { text-transform:uppercase; letter-spacing:.15em; font-size:.72rem; font-weight:700; color:#625bd8; }
        .hero h1 { margin:.3rem 0 .35rem; font-size:clamp(1.65rem,3vw,2.35rem); color:#182230 !important; }
        .hero p { color:#526174 !important; margin:0; font-size:.98rem; }
        .stApp h1, .stApp h2, .stApp h3, .stApp h4 { color:#182230 !important; }
        .stApp [data-testid="stMarkdownContainer"] p, .stApp [data-testid="stCaptionContainer"] { color:#526174 !important; }
        .eyebrow { color:#625bd8; text-transform:uppercase; letter-spacing:.14em; font-size:.7rem; font-weight:700; }
        .kpi-card { min-height:126px; padding:18px 20px; border:1px solid #e5eaf2; border-radius:16px; background:#ffffff; box-shadow:0 5px 20px rgba(34,48,73,.045); }
        .kpi-label { display:flex; align-items:center; gap:8px; color:#526174; font-size:.83rem; font-weight:600; }
        .kpi-value { margin-top:12px; color:#182230; font:700 1.65rem 'Manrope',sans-serif; letter-spacing:-.04em; overflow-wrap:anywhere; }
        .kpi-note { margin-top:3px; color:#748197; font-size:.75rem; }
        .panel { border:1px solid #e5eaf2; border-radius:16px; padding:18px 20px; background:#ffffff; box-shadow:0 5px 20px rgba(34,48,73,.04); }
        .signal-value { font-size:1.1rem; line-height:1.35; min-height:2.8em; overflow-wrap:anywhere; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; color:#182230; }
        div[data-testid="stMetric"] { border:1px solid #e5eaf2; border-radius:14px; padding:16px; background:#ffffff; }
        div[data-testid="stMetricLabel"] p { color:#526174; }
        div[data-testid="stButton"] > button, div[data-testid="stDownloadButton"] > button { border-radius:10px; border:1px solid #625bd8; background:#625bd8; color:white; font-weight:600; min-height:42px; }
        div[data-testid="stButton"] > button:hover, div[data-testid="stDownloadButton"] > button:hover { border-color:#4d47b8; color:white; background:#4d47b8; }
        div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input { border-radius:9px; background:#ffffff; }
        [data-testid="stFileUploaderDropzone"] { background:#f8fafc; border:1px dashed #cbd5e1; }
        [data-testid="stFileUploaderDropzone"] * { color:#344256; }
        [data-testid="stDataFrame"] { border:1px solid #e5eaf2; border-radius:12px; overflow:hidden; }
        div[data-testid="stAlert"] { border-radius:12px; }
        hr { border-color:var(--line); }
        .footer { margin-top:38px; padding-top:16px; color:#748197; border-top:1px solid var(--line); font-size:.78rem; }
        @media (max-width: 700px) { .block-container { padding-left:1rem; padding-right:1rem; } .hero { padding:20px; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, kicker: str = "Business intelligence") -> None:
    st.markdown(
        f"""<section class="hero"><div class="hero-kicker">{kicker}</div>
        <h1>{title}</h1><p>{subtitle}</p></section>""",
        unsafe_allow_html=True,
    )


def kpi_row(metrics: list[dict]) -> None:
    """Render responsive KPI cards. Each item uses label, value, and optional note/icon."""
    if not metrics:
        return
    columns_per_row = min(2, len(metrics))
    for offset in range(0, len(metrics), columns_per_row):
        row = metrics[offset:offset + columns_per_row]
        cols = st.columns(columns_per_row)
        for col, metric in zip(cols, row):
            with col:
                icon = metric.get("icon", "✨")
                note = metric.get("note", "")
                st.markdown(
                    f"""<div class="kpi-card">
                    <div class="kpi-label"><span>{icon}</span>{metric['label']}</div>
                    <div class="kpi-value">{metric['value']}</div>
                    <div class="kpi-note">{note}</div></div>""",
                    unsafe_allow_html=True,
                )


def section_header(title: str, subtitle: str = "") -> None:
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)


def prediction_result_card(sales: float, profit_class: int) -> None:
    high = profit_class == 1
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Predicted sales", indian_currency(sales, 2))
    with col2:
        st.metric("Profit outlook", "High profit" if high else "Low profit")


def ai_insight_panel(label: str, insight: str, kind: str = "info") -> None:
    renderer = {"info": st.info, "success": st.success, "warning": st.warning}.get(kind, st.info)
    renderer(f"**{label}**\n\n{insight}")
