from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# API Keys
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

# Paths
BASE_DIR  = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

DB_PATH = DATA_DIR / "stacknote.db"
CHROMA_PATH = DATA_DIR / "chroma"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

# Development
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

# Create directories
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

