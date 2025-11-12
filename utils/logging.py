from pathlib import Path
import logging
from config.settings import LOG_LEVEL

def setup_logging():
    """로깅 설정"""

    # 로그 폴더 생성
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    level = getattr(logging, LOG_LEVEL.upper(), logging.DEBUG)

    # 로깅 설정
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'app.log'),
            logging.StreamHandler()   # 콘솔 출력
        ]
    )

    return logging.getLogger('stacknote')

logger = setup_logging()