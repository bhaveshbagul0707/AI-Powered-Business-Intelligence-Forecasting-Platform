"""Matplotlib chart builders shared by the dashboard and data explorer."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from matplotlib import font_manager
import pandas as pd
from matplotlib.figure import Figure

from formatting import indian_currency
from translations import chart_text, month_names

PALETTE = ["#625bd8", "#149675", "#e98a35", "#d65379", "#3788d8", "#b38b16"]
_STYLE = {
    "figure.facecolor": "#ffffff",
    "axes.facecolor": "#ffffff",
    "axes.edgecolor": "#dce3ed",
    "axes.grid": True,
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "text.color": "#182230",
    "axes.labelcolor": "#526174",
    "xtick.color": "#526174",
    "ytick.color": "#526174",
    "font.size": 10,
}
_FONT_REGISTERED = False


def _prepare() -> None:
    global _FONT_REGISTERED
    if not _FONT_REGISTERED:
        candidates = (
            Path("C:/Windows/Fonts/Nirmala.ttc"),
            Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        )
        for font_path in candidates:
            if font_path.is_file():
                font_manager.fontManager.addfont(str(font_path))
                family = font_manager.FontProperties(fname=str(font_path)).get_name()
                _STYLE["font.family"] = [family, "DejaVu Sans"]
                break
        _FONT_REGISTERED = True
    plt.rcParams.update(_STYLE)


def _currency(axis, orientation: str = "y") -> None:
    formatter = mticker.FuncFormatter(lambda value, _: indian_currency(value))
    (axis.yaxis if orientation == "y" else axis.xaxis).set_major_formatter(formatter)


def _month_year(value: float, months: list[str]) -> str:
    date = mdates.num2date(value)
    return f"{months[date.month - 1]} {date.year}"


def sales_trend(df: pd.DataFrame, language: str = "English") -> Figure | None:
    if "Order Date" not in df or "Sales" not in df:
        return None
    _prepare()
    dates = pd.to_datetime(df["Order Date"], errors="coerce")
    monthly = df.assign(_date=dates).dropna(subset=["_date"]).set_index("_date")["Sales"].resample("ME").sum()
    if monthly.empty:
        return None
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(monthly.index, monthly.values, color=PALETTE[0], linewidth=2.6, marker="o", markersize=3.5)
    ax.fill_between(monthly.index, monthly.values, color=PALETTE[0], alpha=0.13)
    ax.set_title(chart_text(language, "chart_trend"), loc="left", fontsize=13, fontweight="bold", pad=14, color="#182230")
    ax.set_ylabel(chart_text(language, "chart_sales"))
    locator = mdates.AutoDateLocator(minticks=3, maxticks=8)
    ax.xaxis.set_major_locator(locator)
    translated_months = month_names(language)
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda value, _: _month_year(value, translated_months))
    )
    _currency(ax)
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


def sales_by_category(df: pd.DataFrame, language: str = "English") -> Figure | None:
    if not {"Category", "Sales"}.issubset(df.columns):
        return None
    _prepare()
    data = df.groupby("Category", observed=True)["Sales"].sum().sort_values()
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(data.index.astype(str), data.values, color=PALETTE[:len(data)], height=.54)
    ax.bar_label(bars, labels=[indian_currency(value) for value in data.values], padding=5, fontsize=9, color="#344256")
    ax.set_title(chart_text(language, "chart_category"), loc="left", fontsize=13, fontweight="bold", pad=14, color="#182230")
    _currency(ax, "x")
    ax.set_xlabel(chart_text(language, "chart_sales"))
    fig.tight_layout()
    return fig


def profit_by_region(df: pd.DataFrame, language: str = "English") -> Figure | None:
    if not {"Region", "Profit"}.issubset(df.columns):
        return None
    _prepare()
    data = df.groupby("Region", observed=True)["Profit"].sum().sort_values()
    colors = ["#d65379" if value < 0 else PALETTE[1] for value in data.values]
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(data.index.astype(str), data.values, color=colors, height=.54)
    ax.bar_label(bars, labels=[indian_currency(value) for value in data.values], padding=5, fontsize=9, color="#344256")
    ax.axvline(0, color="#cbd5e1", linewidth=.8)
    ax.set_title(chart_text(language, "chart_region"), loc="left", fontsize=13, fontweight="bold", pad=14, color="#182230")
    _currency(ax, "x")
    ax.set_xlabel(chart_text(language, "chart_profit"))
    fig.tight_layout()
    return fig


def segment_pie(df: pd.DataFrame, language: str = "English") -> Figure | None:
    if not {"Segment", "Sales"}.issubset(df.columns):
        return None
    _prepare()
    data = df.groupby("Segment", observed=True)["Sales"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.pie(data, labels=data.index.astype(str), autopct="%1.0f%%", startangle=90,
           colors=PALETTE[:len(data)], wedgeprops={"width": .38, "edgecolor": "#ffffff"})
    ax.text(0, 0, chart_text(language, "chart_sales"), ha="center", va="center", color="#526174", fontsize=10, fontweight="bold")
    ax.set_title(chart_text(language, "chart_customer"), loc="left", fontsize=13, fontweight="bold", pad=14, color="#182230")
    fig.tight_layout()
    return fig


def ship_mode_bar(df: pd.DataFrame, language: str = "English") -> Figure | None:
    if not {"Ship Mode", "Sales"}.issubset(df.columns):
        return None
    _prepare()
    data = df.groupby("Ship Mode", observed=True)["Sales"].sum().sort_values()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(data.index.astype(str), data.values, color=PALETTE[:len(data)], height=.54)
    ax.set_title(chart_text(language, "chart_shipping"), loc="left", fontsize=13, fontweight="bold", pad=14, color="#182230")
    _currency(ax, "x")
    fig.tight_layout()
    return fig


def discount_profitability(df: pd.DataFrame, language: str = "English") -> Figure | None:
    if not {"Discount", "Profit", "Sales"}.issubset(df.columns):
        return None
    _prepare()
    tmp = df.assign(_discount=pd.to_numeric(df["Discount"], errors="coerce").round(2))
    data = tmp.groupby("_discount", observed=True).agg(Profit=("Profit", "sum"), Sales=("Sales", "sum")).dropna()
    if data.empty:
        return None
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(data.index.astype(str), data["Profit"], color=[PALETTE[1] if v >= 0 else "#d65379" for v in data["Profit"]])
    ax.axhline(0, color="#cbd5e1", linewidth=.8)
    ax.set_title(chart_text(language, "chart_discount_profit"), loc="left", fontsize=13, fontweight="bold", pad=14, color="#182230")
    ax.set_xlabel(chart_text(language, "chart_discount"))
    _currency(ax)
    fig.tight_layout()
    return fig
