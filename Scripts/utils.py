from pathlib import Path


# ==========================================================
# Project Paths
# ==========================================================

PROJECT_ROOT = Path(__file__).parent.parent


# ==========================================================
# Working Folders
# ==========================================================

BLP_FOLDER = PROJECT_ROOT / "BLP"
PNG_FOLDER = PROJECT_ROOT / "PNG"
RESIZED_FOLDER = PROJECT_ROOT / "PNG_128x128_Resized"
ICONS_FOLDER = PROJECT_ROOT / "ICONS"

TEMPLATES_FOLDER = PROJECT_ROOT / "Templates"
LOGS_FOLDER = PROJECT_ROOT / "Logs"


# ==========================================================
# Create Required Folders
# ==========================================================

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