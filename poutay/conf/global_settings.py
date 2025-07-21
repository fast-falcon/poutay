"""Default configuration values for Poutay framework."""

from pathlib import Path

# General settings
DEBUG = True
INSTALLED_APPS = []
BASE_DIR = Path(__file__).resolve().parent.parent

# SVG color generation
SVG_COLORS = {
    "primary": "#0d6efd",
    "secondary": "#6c757d",
}
SVG_COLORS_DIR = BASE_DIR / "build" / "svg_colors"

# Resource compilation
QRC_FILE = str(BASE_DIR / "assets.qrc")
QRC_FILE_FULL = str(BASE_DIR / "build" / "assets_full.qrc")
COMPILED_QRC_PY = str(BASE_DIR / "build" / "assets_rc.py")
PYSIDE6_RCC_PATH = "pyside6-rcc"

# UI themes
FONT_PATH = str(BASE_DIR / "assets" / "font.ttf")
QSS_PATH = str(BASE_DIR / "assets" / "style.qss")

# Entry point
START = None  # e.g., "module:main"
