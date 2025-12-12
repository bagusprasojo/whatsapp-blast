"""
Configuration constants for the WhatsApp Blast application.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "wa_blast.db"

DEFAULT_DELAY_SECONDS = 2
MAX_RECOMMENDED_MESSAGES_PER_DAY = 300
LOG_FILE = DATA_DIR / "blast.log"

# Selenium configuration
SELENIUM_DRIVER_PATH = DATA_DIR / "drivers"
DEFAULT_BROWSER = "chrome"

# APScheduler configuration
SCHEDULER_JOBSTORE = DATA_DIR / "jobs.sqlite"

# Authentication
AUTH_ENDPOINT = (
    "https://script.google.com/macros/s/"
    "AKfycbww0PkO5E3wQ8w62_UvU3IABbvwW4PqDP4BNIXMY-H5dYAmB7a81b6OuOE0RB0RMIgFjw/exec"
)

DATA_DIR.mkdir(exist_ok=True)
SELENIUM_DRIVER_PATH.mkdir(parents=True, exist_ok=True)
