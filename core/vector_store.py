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
    

if __name__ == "__main__":
    print("🧪 LangChain ChromaDB 테스트\n")
    print("=" * 70)

    vectorstore = init_vectorstore()

    # 2. 문서 추가
    print("\n2️⃣ 문서 추가...")
    test_docs = [
        {
            'id': 1,
            'content': 'LangGraph는 상태 기반 워크플로우를 만드는 프레임워크입니다. StateGraph를 사용하여 복잡한 Agent를 구현할 수 있습니다.',
            'metadata': {
                'title': 'LangGraph 튜토리얼',
                'category': 'LangGraph',
                'source_type': 'blog'
            }
        },
        {
            'id': 2,
            'content': 'RAG는 Retrieval Augmented Generation의 약자입니다. 벡터 데이터베이스를 사용하여 관련 문서를 검색하고 LLM과 결합합니다.',
            'metadata': {
                'title': 'RAG 가이드',
                'category': 'RAG',
                'source_type': 'docs'
            }
        },
        {
            'id': 3,
            'content': 'FastAPI는 Python 웹 프레임워크입니다. async/await를 사용한 비동기 처리를 지원합니다.',
            'metadata': {
                'title': 'FastAPI 가이드',
                'category': 'FastAPI',
                'source_type': 'blog'
            }
        }
    ]
    
    for doc in test_docs:
        success = add_activity_to_vector(
            vectorstore,
            doc['id'],
            doc['content'],
            doc['metadata']
        )
        if success:
            print(f"   ✅ 추가: {doc['metadata']['title']}")
    
    # 3. 검색 테스트
    print("\n3️⃣ 검색 테스트...")
    
    queries = [
        "Agent 워크플로우",
        "벡터 데이터베이스",
        "비동기 처리"
    ]
    
    for query in queries:
        print(f"\n   검색어: '{query}'")
        results = search_similar(vectorstore, query, k=2)
        
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result['metadata']['title']}")
            print(f"      내용: {result['content'][:50]}...")
    
    # 4. 필터 검색
    print("\n4️⃣ 필터 검색 (category=RAG)...")
    results = search_similar(
        vectorstore,
        "데이터베이스",
        k=5,
        filter_metadata={"category": "RAG"}
    )
    
    print(f"   결과: {len(results)}개")
    for result in results:
        print(f"   - {result['metadata']['title']}")
    
    # 5. 삭제 테스트
    print("\n5️⃣ 삭제 테스트...")
    delete_activity_from_vector(vectorstore, 3)
    print(f"   삭제 완료")
    
    print("\n" + "=" * 70)
    print("✅ ChromaDB 테스트 완료!")