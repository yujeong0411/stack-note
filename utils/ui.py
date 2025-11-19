import streamlit as st
from pathlib import Path
from urllib.parse import urlparse

def load_css(file_path: str="style.css"):
    """
    외부 CSS 파일 로드
    
    Args:
        file_path: CSS 파일 경로 (프로젝트 루트 기준)
    """
    css_file = Path(__file__).parent.parent / file_path
    
    if css_file.exists():
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"CSS 파일을 찾을 수 없습니다: {css_file}")

def render_card(title: str, url: str, summary: str, tags: list):
    """
    활동 카드 렌더링
    
    Args:
        title: 제목
        url: URL
        summary: 요약
        tags: 태그 리스트
    """
    # 도메인 추출
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace('www.', '')  # www. 제거
    
    # 도메인 아이콘 설정 (파비콘 사용)
    favicon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=32"

    # 태그 HTML 생성
    tags_html = " ".join([f"<span class='tag'>#{t}</span>" for t in tags[:5]])
    
    # 카드 전체를 링크로 만들기
    st.markdown(f"""
    <a href="{url}" target="_blank" style="text-decoration: none; color: inherit;">
        <div class='card'>
            <div style='display: flex; align-items: start; gap: 0.75rem;'>
                <img src="{favicon_url}" 
                     style='width: 24px; height: 24px; margin-top: 0.25rem; border-radius: 4px;'
                     onerror="this.style.display='none'">
                <div style='flex: 1; min-width: 0;'>
                    <b style='display: block; margin-bottom: 0.25rem;'>{title}</b>
                    <span style='color: var(--text-tertiary); font-size: 0.75rem; display: flex; align-items: center; gap: 0.25rem;'>
                        🔗 {domain}
                    </span>
                </div>
            </div>
            <p style='margin-top: 0.75rem; line-height: 1.6;'>{summary}</p>
            <div style='margin-top: 0.75rem; display: flex; flex-wrap: wrap; gap: 0.25rem;'>
                {tags_html}
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)

def render_briefing_block(content: str):
    """
    브리핑 블록 렌더링
    
    Args:
        title: 블록 제목
        content: 내용
    """
    st.markdown(
        content, 
        unsafe_allow_html=False # content는 순수 마크다운으로 처리
    )
    






