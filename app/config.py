"""Centralised configuration — all magic strings live here."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent


def _get_groq_api_key() -> str:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if api_key:
        return api_key
    try:
        return str(st.secrets.get("GROQ_API_KEY", "")).strip()
    except FileNotFoundError:
        return ""


@dataclass(frozen=True)
class AppConfig:
    page_title: str = "AI Business Intelligence"
    page_icon: str = "📊"
    layout: str = "wide"

    groq_api_key: str = field(default_factory=_get_groq_api_key)
    groq_model: str = "llama-3.1-8b-instant"
    groq_temperature: float = 0.4

    model_dir: Path = ROOT_DIR / "model"
    reports_dir: Path = ROOT_DIR / "reports"

    required_columns: tuple[str, ...] = (
        "Sales", "Profit", "Category", "Region", "Quantity", "Discount"
    )

    @property
    def reg_model_path(self) -> Path:
        return self.model_dir / "sales_regression.pkl"

    @property
    def clf_model_path(self) -> Path:
        return self.model_dir / "profit_classifier.pkl"

    @property
    def scaler_path(self) -> Path:
        return self.model_dir / "scaler.pkl"


CONFIG = AppConfig()
CONFIG.reports_dir.mkdir(parents=True, exist_ok=True)