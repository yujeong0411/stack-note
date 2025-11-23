"""
웹 콘텐츠 추출 모듈
Trafilatura를 사용하여 URL에서 본문과 메타데이터 추출
"""

from trafilatura import extract, extract_metadata
from urllib.parse import urlparse
from utils.logging import logger
from typing import Optional, Dict, Any
import requests

def extract_content(url: str) -> Optional[Dict[str, Any]]:
    """
    URL에서 콘텐츠와 메타데이터 추출

    Args:
        url: 추출할 웹페이지 URL

    Return:
        Dict with:
        - url : URL
        - domain: 도메인
        - title : 제목
        - content: 본문
        
        실패 시 None
    """
    logger.info(f"콘텐츠 추출 시작: {url}")

    try:
        # 기본 추출
        # Cloudflare 보호를 trafilatura으로 해결하기 어려워서 requests 병용
        # html = fetch_url(url)
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=40)
        if response.status_code != 200:
            return None

        html = response.text

        # 본문 추출
        content = extract(
            html,
            include_comments=False,   # 댓글 제외
            include_tables=True,      # 표 포함
            no_fallback=False         # 풀백 허용 (추출 정확도 향상)
        )

        # 메타데이터 추출
        metadata = extract_metadata(html)

        # 도메인 추출
        domain = detect_source_type(url)

        # 결과 구성
        result = {
            "url": url,
            "domain": domain,
            "title": metadata.title if metadata else None,
            "content": content,
        }

        logger.info(f"추출 완료: {result['title']}")
        logger.debug(f"도메인: {domain}")

        return result
    
    except Exception as e:
        logger.error(f"[ERROR]추출 실패: {e}")
        logger.exception(e)
        return None
    

def detect_source_type(url: str) -> str:
    """
    URL 기반으로 콘텐츠 소스 유형(blog, docs, news, forum, youtube, article 등)을 감지합니다.
    단순 패턴 매칭 + 도메인 기반으로 분류.
    
    Args:
        url: 웹페이지 URL

    Returns:
        source_type: 'youtube', 'blog', 'docs', 'article', 'unknown'
    """
    url_lower = url.lower()
    domain = urlparse(url).netloc.lower()

    # --- YouTube / 영상 ---
    VIDEO_DOMAINS = [
        "youtube.com", "youtu.be", "vimeo.com", "navertv.", "dailymotion.com",
        "twitch.tv", "kakao.tv", "afreecatv.com", "ted.com/talks",
        "bilibili.com", "inflearn.com", "fastcampus.co"
    ]
    if any(d in domain for d in VIDEO_DOMAINS) or "/video/" in url_lower:
        return "video"

    # --- 블로그 ---
    BLOG_DOMAINS = [
        "tistory.com", "velog.io", "medium.com", "brunch.co.kr", "naver.com",
        "notion.site", "substack.com", "hashnode.dev", "ghost.io",
        "wordpress.com", "blogspot.com", "dev.to", "teletype.in",
        "post.naver.com", "mirror.xyz"
    ]
    if any(d in domain for d in BLOG_DOMAINS) or "/blog/" in url_lower:
        return "blog"

    # --- 문서 / 기술 문서 ---
    DOC_DOMAINS = [
        "readthedocs.io", "github.io", "docsify", "developer.", "api.",
        "python.langchain.com", "docs.", "devdocs.io", "notion.com",
        "learn.microsoft.com", "developer.mozilla.org", "pkg.go.dev",
        "pytorch.org", "tensorflow.org", "react.dev", "vuejs.org"
    ]
    if any(d in domain for d in DOC_DOMAINS) or "/docs/" in url_lower or "/guide/" in url_lower:
        return "docs"

    # --- 뉴스 / 미디어 ---
    NEWS_DOMAINS = [
        "news.naver.com", "bbc.com", "nytimes.com", "cnn.com",
        "reuters.com", "bloomberg.com", "theguardian.com",
        "ytn.co.kr", "mbc.co.kr", "sbs.co.kr", "kbs.co.kr",
        "hani.co.kr", "chosun.com", "joongang.co.kr", "donga.com"
    ]
    if any(d in domain for d in NEWS_DOMAINS) or "/news/" in url_lower:
        return "news"

    # --- 커뮤니티 / Q&A ---
    FORUM_DOMAINS = [
        "reddit.com", "stackoverflow.com", "okky.kr", "ruliweb.com",
        "clien.net", "slack.com", "discord.com", "github.com/issues",
        "medium.com/@", "cafe.naver.com"
    ]
    if any(d in domain for d in FORUM_DOMAINS) or "/questions/" in url_lower:
        return "forum"

    # --- 기본값: 일반 기사 또는 기타 콘텐츠 ---
    return "article"
