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

# Color Palette Tokens (StitchMCP / LOGIC_OS 2.0)
COLOR_BG_DARK = "#0a0a0c"
COLOR_BG_SURFACE = "rgba(17, 17, 20, 0.75)"
COLOR_BG_CARD = "rgba(20, 20, 24, 0.85)"
COLOR_CYAN_PRIMARY = "#4cd7f6"
COLOR_PURPLE_SECONDARY = "#d0bcff"
COLOR_PURPLE_ACCENT = "#571bc1"
COLOR_BORDER = "#1e293b"
COLOR_TEXT_PRIMARY = "#e5e1e4"
COLOR_TEXT_SECONDARY = "#94a3b8"
COLOR_TEXT_MUTED = "#869397"
COLOR_SUCCESS = "#10b981"
COLOR_WARNING = "#fbbf24"
COLOR_DANGER = "#f43f5e"

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
    "COLOR_DANGER",
    "COLOR_PURPLE_ACCENT",
    "COLOR_PURPLE_SECONDARY",
    "COLOR_SUCCESS",
    "COLOR_TEXT_MUTED",
    "COLOR_TEXT_PRIMARY",
    "COLOR_TEXT_SECONDARY",
    "COLOR_WARNING",
    "EXAMPLE_QUESTIONS",
    "SAMPLE_DATA_DIR",
    "SAMPLE_DATASETS",
    "STYLES_PATH",
]
