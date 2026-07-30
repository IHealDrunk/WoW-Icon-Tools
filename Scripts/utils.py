from pathlib import Path


# Project Root
PROJECT_ROOT = Path(__file__).parent.parent


# Main folders
BLP_FOLDER = PROJECT_ROOT / "BLP"
PNG_FOLDER = PROJECT_ROOT / "PNG"
RESIZED_FOLDER = PROJECT_ROOT / "PNG_128x128_Resized"
ICONS_FOLDER = PROJECT_ROOT / "ICONS"


# Templates
TEMPLATES_FOLDER = PROJECT_ROOT / "Templates"


# Logs and reports
LOGS_FOLDER = PROJECT_ROOT / "Logs"


# Create required folders if missing
REQUIRED_FOLDERS = [
    BLP_FOLDER,
    PNG_FOLDER,
    RESIZED_FOLDER,
    ICONS_FOLDER,
    TEMPLATES_FOLDER,
    LOGS_FOLDER,
]


for folder in REQUIRED_FOLDERS:
    folder.mkdir(parents=True, exist_ok=True)