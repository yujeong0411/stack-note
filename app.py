# uv run streamlit run app.py

import streamlit as st
from utils.logging import logger
from config.settings import UPSTAGE_API_KEY, DEV_MODE, DB_PATH, CHROMA_PATH

st.title("Stacknote")
st.subheader("AI-powered Personal Knowledge Base")

# API KEY 확인
if UPSTAGE_API_KEY:
    st.success("loaded API KEY")
else:
    st.error("API KEY not found")

if DEV_MODE:
    with st.expander("개발 정보"):
        st.write(f"**DEV_MODE:** {DEV_MODE}")
        st.write(f"**DB Path:** {DB_PATH}")
        st.write(f"**ChromaDB:** {CHROMA_PATH}")

# 로그 테스트
logger.info("앱 시작")
logger.debug("더비깅 메세지")
logger.error("에러 발생!")
logger.warning("주의!")

st.divider()
st.subheader("URL 입력 테스트")
url = st.text_input("URL을 입력하세요.", placeholder="https://example.com")

if url:
    st.info(f"입력된 URL: {url}")
    logger.info(f"User input URL: {url}")

st.divider()
st.success("테스트 완료")