"""UI Configuration and Application Constants."""

from __future__ import annotations

from pathlib import Path

# Paths
APP_DIR = Path(__file__).parent
ASSETS_DIR = APP_DIR / "assets"
SAMPLE_DATA_DIR = APP_DIR / "sample_data"
STYLES_PATH = ASSETS_DIR / "styles.css"

# App Metadata
APP_TITLE = "LOGIC_OS_2.0"
APP_SUBTITLE = "Tabular Analytics Agent"
APP_VERSION = "v2.0.0-production"
APP_ICON = "🤖"

# Color Palette Tokens
COLOR_BG_DARK = "#111111"
COLOR_BG_SURFACE = "#18181b"
COLOR_BG_CARD = "#1e1e24"
COLOR_CYAN_PRIMARY = "#00f0ff"
COLOR_PURPLE_SECONDARY = "#a855f7"
COLOR_BORDER = "#27272a"
COLOR_TEXT_PRIMARY = "#f8fafc"
COLOR_TEXT_SECONDARY = "#94a3b8"

# Default Sample Datasets
SAMPLE_DATASETS = [
    {"name": "sales_data.csv", "label": "📊 Sales Data", "icon": "📊"},
    {"name": "customer_churn.csv", "label": "👥 Customer Churn", "icon": "👥"},
    {"name": "survey_responses.csv", "label": "💬 Survey Responses", "icon": "💬"},
]

# Quick Follow-Up Example Questions
EXAMPLE_QUESTIONS = [
    "Average salary",
    "Highest revenue",
    "Show revenue trend",
    "Top 10 customers",
]

__all__ = [
    "APP_DIR",
    "APP_ICON",
    "APP_SUBTITLE",
    "APP_TITLE",
    "APP_VERSION",
    "ASSETS_DIR",
    "COLOR_BG_CARD",
    "COLOR_BG_DARK",
    "COLOR_BG_SURFACE",
    "COLOR_BORDER",
    "COLOR_CYAN_PRIMARY",
    "COLOR_PURPLE_SECONDARY",
    "COLOR_TEXT_PRIMARY",
    "COLOR_TEXT_SECONDARY",
    "EXAMPLE_QUESTIONS",
    "SAMPLE_DATA_DIR",
    "SAMPLE_DATASETS",
    "STYLES_PATH",
]
