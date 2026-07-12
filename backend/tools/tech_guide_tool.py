import json
import os
import logging
from strands import tool

logger = logging.getLogger(__name__)

KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")


def _query_knowledge_base(query: str, top_k: int = 3) -> list[dict]:
    """Bedrock Knowledge Base에 벡터 검색 쿼리를 실행합니다."""
    import boto3

    client = boto3.client(
        "bedrock-agent-runtime",
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
    )

    response = client.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={
            "vectorSearchConfiguration": {"numberOfResults": top_k}
        },
    )

    results = []
    for item in response.get("retrievalResults", []):
        results.append(
            {
                "content": item["content"]["text"],
                "source": item.get("location", {})
                .get("s3Location", {})
                .get("uri", ""),
                "confidence": item.get("score", 0),
            }
        )
    return results


def _local_text_search(query: str, top_k: int = 3) -> list[dict]:
    """로컬 기술 가이드 마크다운 파일에서 텍스트 유사도 검색 (KB 미설정 시 폴백)."""
    import pathlib

    tech_guides_dir = pathlib.Path(__file__).parent.parent / "tech_guides"
    if not tech_guides_dir.exists():
        return []

    query_terms = set(query.lower().split())
    scored = []

    for md_file in tech_guides_dir.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        content_lower = content.lower()

        score = sum(1 for term in query_terms if term in content_lower)
        if score > 0:
            scored.append(
                {
                    "content": content,
                    "source": str(md_file.relative_to(tech_guides_dir)),
                    "confidence": round(score / max(len(query_terms), 1), 2),
                }
            )

    scored.sort(key=lambda x: x["confidence"], reverse=True)
    return scored[:top_k]


@tool
def get_tech_guide(query: str) -> str:
    """장난감 자동차 기술 지원 가이드를 자연어로 검색합니다.
    Bedrock Knowledge Base에서 벡터 유사도 검색(RAG)을 수행하여
    조립 방법, 고장 해결, 배터리 교체/충전, 리모컨 페어링 등의 가이드를 찾아줍니다.

    Args:
        query: 자연어 검색 질문 (예: "RC카 리모컨이 연결이 안 돼요", "스피드 레이서 배터리 충전 방법", "조립키트 모터가 안 돌아요")

    Returns:
        검색된 기술 가이드 내용, 출처, 신뢰도 점수
    """
    try:
        if KNOWLEDGE_BASE_ID:
            logger.info(f"KB search: kb={KNOWLEDGE_BASE_ID}, query='{query}'")
            results = _query_knowledge_base(query, top_k=3)
        else:
            logger.info(f"Local text search fallback: query='{query}'")
            results = _local_text_search(query, top_k=3)
    except Exception as e:
        logger.error(f"Tech guide search failed: {e}")
        return json.dumps(
            {
                "error": f"기술 가이드 검색 중 오류가 발생했습니다: {str(e)}",
                "suggestion": "고객센터 1588-VROOM으로 연락해주세요.",
            },
            ensure_ascii=False,
        )

    if not results:
        return json.dumps(
            {
                "error": f"'{query}' 관련 기술 가이드를 찾을 수 없습니다.",
                "suggestion": "다른 키워드로 다시 검색해보세요. 그래도 해결이 안 되면 고객센터 1588-VROOM으로 연락해주세요.",
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "query": query,
            "results": results,
            "total": len(results),
        },
        ensure_ascii=False,
    )
