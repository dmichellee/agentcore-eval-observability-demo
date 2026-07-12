"""
Lambda Handler: tech-guide
Tool: get_tech_guide
Data source: Bedrock Knowledge Base (RAG 벡터 검색)

AgentCore Gateway Lambda 호출 형식:
- event: inputSchema의 properties 값들 (예: {"query": "..."})
- context.client_context.custom['bedrockAgentCoreToolName']: "TargetName___tool_name"
"""
import json
import os
import logging

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")

bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)

# Tool name prefix delimiter used by AgentCore Gateway
TOOL_NAME_DELIMITER = "___"


def _extract_tool_name(context) -> str:
    """AgentCore Gateway context에서 tool name 추출 (prefix 제거)"""
    try:
        if hasattr(context, 'client_context') and context.client_context:
            custom = getattr(context.client_context, 'custom', None)
            if custom and 'bedrockAgentCoreToolName' in custom:
                full_name = custom['bedrockAgentCoreToolName']
                if TOOL_NAME_DELIMITER in full_name:
                    return full_name.split(TOOL_NAME_DELIMITER, 1)[1]
                return full_name
    except Exception as e:
        logger.warning(f"Failed to extract tool name from context: {e}")
    return ""


def get_tech_guide(params: dict) -> dict:
    query = params.get("query", "")

    if not query:
        return {"error": "검색 질문(query)을 입력해주세요."}

    if not KNOWLEDGE_BASE_ID:
        return {
            "error": "Knowledge Base가 설정되지 않았습니다.",
            "suggestion": "KNOWLEDGE_BASE_ID 환경변수를 설정해주세요.",
        }

    logger.info(f"KB retrieve: kb={KNOWLEDGE_BASE_ID}, query='{query}'")

    response = bedrock_agent_runtime.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={
            "vectorSearchConfiguration": {"numberOfResults": 3}
        },
    )

    results = []
    for item in response.get("retrievalResults", []):
        results.append({
            "content": item["content"]["text"],
            "source": item.get("location", {}).get("s3Location", {}).get("uri", ""),
            "confidence": item.get("score", 0),
        })

    if not results:
        return {
            "error": f"'{query}' 관련 기술 가이드를 찾을 수 없습니다.",
            "suggestion": "다른 키워드로 다시 검색해보세요. 고객센터 1588-VROOM으로 연락해주세요.",
        }

    return {
        "query": query,
        "results": results,
        "total": len(results),
    }


TOOLS = {
    "get_tech_guide": get_tech_guide,
}


def lambda_handler(event, context):
    """
    Lambda 엔트리포인트 - AgentCore Gateway에서 호출됩니다.

    AgentCore Gateway 호출 형식:
    - event: inputSchema properties 값들 (예: {"query": "리모컨 문제"})
    - context.client_context.custom['bedrockAgentCoreToolName']: "TechGuideTools___get_tech_guide"
    """
    logger.info(f"Event: {json.dumps(event, ensure_ascii=False)}")

    # Context에서 tool name 추출 (AgentCore Gateway 형식)
    tool_name = _extract_tool_name(context)
    logger.info(f"Extracted tool_name: {tool_name}")

    # event 자체가 parameters (AgentCore Gateway는 inputSchema properties를 event로 전달)
    params = event

    if tool_name not in TOOLS:
        # Fallback: 단일 tool인 경우 tool_name 없이도 기본 tool 실행
        if len(TOOLS) == 1:
            tool_name = list(TOOLS.keys())[0]
            logger.info(f"Fallback to single tool: {tool_name}")
        else:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"error": f"Unknown tool: {tool_name}. Available: {list(TOOLS.keys())}"},
                    ensure_ascii=False,
                ),
            }

    result = TOOLS[tool_name](params)
    return {
        "statusCode": 200,
        "body": json.dumps(result, ensure_ascii=False, default=str),
    }
