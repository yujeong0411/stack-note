"""
AI 기반 콘텐츠 분류 및 요약
"""

from langchain_upstage import ChatUpstage
from config.settings import UPSTAGE_API_KEY, UPSTAGE_MODEL
from utils import logger
from typing import Dict, List, Any
import json

def classify_content(title: str, content:str) -> Dict[str, Any]:
    """
    콘텐츠를 분석하여 카테고리, 태그, 요약 생성
    
    Args:
        title, content

    Returns:
        {
            'category': str,      # 주 카테고리
            'tags': List[str],    # 태그 리스트
            'summary': str        # 3-4문장 요약
        }
    """
    logger.info(f"AI 분류 시작: {title}, {content}")

    try:
        llm = ChatUpstage(
            api_key=UPSTAGE_API_KEY,
            model=UPSTAGE_MODEL
        )

        # 토큰 제한
        content_preview = content[:2000]

        # 프롬프트
        prompt = f"""
제목: {title}
본문 : {content_preview}

<role>
너는 사용자가 읽은 웹페이지 콘텐츠를 자동으로 분류, 요약, 태그를 생성하는 전문 지식 관리 AI Agent야.
</role>

<instruction>
제공된 '제목'과 '본문'을 분석하여, 사용자가 나중에 쉽게 검색하고 이해할 수 있도록 구조화된 메타데이터를 생성해줘.

**규칙**:
1. category는 내용을 대표하는 단어 1개로, 15자 이내로 간결하게 작성해줘.
2. tags는 본문의 핵심 주제와 관련된 구체적인 키워드 3~5개를 생성해줘.
3. summary는 원본 내용을 왜 보았는지 기억할 수 있도록 핵심만 간결하게 3~4문장으로 요약해줘.
4. 절대로 output format 외의 다른 텍스트는 출력하지마.
</instruction>

<output format>
{{
    "category": "주요 카테고리 (내용을 대표하는 단어 1개, 예: LangChain, RAG, FastAPI, Python, AI, Web, Database 등)",
    "tags": ["태그1", "태그2", "태그3", "태그4"],
    "summary": "3-4문장으로 핵심 내용 요약"
}}
</output format>

다음 형식의 JSON으로만 응답하세요:
{{
    "category": "주요 카테고리 (예: LangChain, RAG, FastAPI, Python, AI, Web, Database 등)",
    "tags": ["태그1", "태그2", "태그3"],
    "summary": "3-4문장으로 핵심 내용 요약"
}}

규칙:
1. category는 내용을 대표하는 단어 1개
2. tags는 3-5개의 구체적인 키워드
3. summary는 핵심만 간결하게

JSON만 출력하세요. 다른 텍스트는 출력하지 마세요."""
        
        # API 호출
        response = llm.invoke(prompt)
        response_text = response.content.strip()

        # json 파싱
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        result = json.loads(response_text)

        logger.info(f"분류 완료: {result['category']}")
        logger.debug(f"태그: {', '.join(result['tags'])}")
        logger.debug(f"요약: {result['summary'][:50]}...")

        return result

    except json.JSONDecodeError as e:
        logger.error(f" JSON 파싱 실패: {e}")
        logger.error(f"응답: {response_text}")
        
        # 폴백
        return {
            'category': 'Uncategorized',
            'tags': ['tech'],
            'summary': title
        }
    
    except Exception as e:
        logger.error(f" AI 분류 실패 : {e}")

        # fullback
        return {
            'category': 'Uncategorized',
            'tags': ['tech'],
            'summary': title
        }

