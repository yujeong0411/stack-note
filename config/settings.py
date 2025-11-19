from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# API Keys
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
UPSTAGE_MODEL = os.getenv("UPSTAGE_MODEL")

# Paths
BASE_DIR  = Path(__file__).parent.parent
# DATA_DIR = BASE_DIR / "data"
# LOG_DIR = BASE_DIR / "logs"
HOME_DIR = Path.home()
APP_DATA_DIR = HOME_DIR / ".stacknote"
DATA_DIR = APP_DATA_DIR / "data"
LOG_DIR = APP_DATA_DIR / "logs" # 로그도 데이터와 함께 옮깁니다.

DB_PATH = DATA_DIR / "stacknote.db"
CHROMA_PATH = DATA_DIR / "chroma"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

# Development
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

# Create directories
APP_DATA_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

