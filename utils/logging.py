from pathlib import Path
import logging
import sys
import io
from config.settings import LOG_LEVEL

# 전역 플래그: stdout/stderr가 이미 래핑되었는지 확인
_IO_WRAPPED = False

def setup_logging():
    """로깅 설정"""
    global _IO_WRAPPED # 전역 플래그 사용 선언

    # 로그 폴더 생성
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    level = getattr(logging, LOG_LEVEL.upper(), logging.DEBUG)

    try:
        if sys.platform == 'win32' and not _IO_WRAPPED:
            # sys.stdout이 이미 닫혀 있는지 확인하는 안전 장치 추가
            # (단, Streamlit 환경에서는 Streamlit 자체가 stdout을 관리하므로 
            # 이 재정의를 완전히 피하는 것이 가장 안전할 수 있습니다.)
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding='utf-8',
                errors='replace',  # 디코딩 불가능한 문자는 ? 로 치환
                line_buffering=True
            )
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer,
                encoding='utf-8',
                errors='replace',
                line_buffering=True
            )
            _IO_WRAPPED = True # 성공적으로 래핑했음을 표시

    except ValueError:
        # 만약 이미 닫혔다면, 오류를 무시하고 래핑 플래그만 설정하지 않음
        pass

    # 기존 핸들러가 있다면 제거 (Streamlit 재실행 시 핸들러 중복 등록 방지)
    root_logger = logging.getLogger()
    if root_logger.handlers:
        # 기존 핸들러 제거 (Streamlit 환경에서 중요)
        root_logger.handlers = []

    # 로깅 설정
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'app.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)   # 콘솔 출력
        ]
    )

    return logging.getLogger('stacknote')

logger = setup_logging()