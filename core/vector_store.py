"""벡터 스토어 관리"""
from langchain_chroma import Chroma
from langchain_upstage import UpstageEmbeddings
from config.settings import CHROMA_PATH, UPSTAGE_API_KEY
from utils import logger
from typing import List, Dict, Any, Optional

def init_vectorstore(collection_name="activities"):
    """chromadb 초기화"""
    logger.info("chromadb 초기화 시작")

    # 폴더 생성
    CHROMA_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 임베딩
    embeddings = UpstageEmbeddings(
        api_key=UPSTAGE_API_KEY,
        model="solar-embedding-1-large"
    )

    # 클라이언트 생성
    vectorstore = Chroma(
        persist_directory=str(CHROMA_PATH),
        embedding_function=embeddings,
        collection_name=collection_name
    )

    logger.info(f"벡터스토어 초기화 완료 : {CHROMA_PATH}")
    return vectorstore

def add_activity_to_vector(
    vectorstore: Chroma,
    activity_id : int,
    content: str,
    metadata: Dict[str, Any]
):
    """활동을 벡터 db에 추가"""

    try:
        # ID를 메타데이터에 포함
        metadata['activity_id'] = activity_id

        # content 토큰 제한 
        safe_content = content[:3800]

        # 추가, 자동 임베딩 -> add_documents는 하나의 문서리스트를 변환, 우리는 url 하나하나를 추가
        vectorstore.add_texts(
            texts=[content],
            metadatas=[metadata],
            ids=[f"activity_{activity_id}"]
        )

        logger.info(f"벡터 db 저장: activity_{activity_id}")
        return True
    
    except Exception as e:
        logger.error(f"벡터 DB 저장 실패: {e}")
        return False
    

def search_similar(
    vectorstore: Chroma,
    query: str,
    k: int = 5,
    filter_metadata: Optional[Dict] = None  
) -> List[Dict[str, Any]]:
    """유사 문서 검색"""
    try:
        # 유사도 검색
        if filter_metadata:
            results = vectorstore.similarity_search(
                query,
                k=k,
                filter=filter_metadata
            )
        else:
            results = vectorstore.similarity_search(query, k=k)

        # 결과 파싱 - add text를 썼기 때문에 텍스틀 리스트로! (Document 객체 안씀)
        documents = []
        for doc in results:
            documents.append({
                'content': doc.page_content,
                'metadata': doc.metadata
            })

        logger.info(f"벡터 검색 완료: '{query}' - {len(documents)}개 결과")
        return documents

    except Exception as e:
        logger.error(f"벡터 검색 에러: {e}")
        return []
    
def delete_activity_from_vector(vectorstore: Chroma, activity_id: int):
    """벡터 db에서 삭제"""
    try:
        vectorstore.delete(ids=[f"activity_{activity_id}"])
        logger.info(f"벡터 db에서 삭제: activity_{activity_id}")
    except Exception as e:
        logger.error(f"벡터 db 삭제 실패: {e}")
        return False
    
