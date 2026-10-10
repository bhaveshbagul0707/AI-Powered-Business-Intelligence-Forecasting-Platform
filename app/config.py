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
    return _get_setting("GROQ_API_KEY")


def _get_setting(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, "")
        if not value:
            group_name, _, setting_name = name.partition("_")
            secret_group = st.secrets.get(group_name.lower(), {})
            if hasattr(secret_group, "get"):
                value = secret_group.get(
                    name,
                    secret_group.get(
                        setting_name.lower(),
                        secret_group.get(setting_name.upper(), ""),
                    ),
                )
    except FileNotFoundError:
        value = ""
    if value:
        return str(value).strip()
    return os.getenv(name, "").strip() or default


@dataclass(frozen=True)
class AppConfig:
    page_title: str = "Dukaan Dost | Shop Dashboard"
    page_icon: str = "📊"
    layout: str = "wide"

    groq_api_key: str = field(default_factory=_get_groq_api_key)
    groq_model: str = "openai/gpt-oss-20b"
    groq_temperature: float = 0.4

    mongodb_uri: str = field(default_factory=lambda: _get_setting("MONGODB_URI"))
    mongodb_database: str = field(
        default_factory=lambda: _get_setting("MONGODB_DATABASE", "dukaan_dost")
    )

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