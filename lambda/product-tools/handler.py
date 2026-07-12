"""
Lambda Handler: product-tools
Tools: search_products, get_product_detail, recommend_products
Data source: DynamoDB (vroom-dash-products)

AgentCore Gateway Lambda 호출 형식:
- event: inputSchema의 properties 값들 (예: {"query": "...", "category": "..."})
- context.client_context.custom['bedrockAgentCoreToolName']: "TargetName___tool_name"
"""
import json
import os
import logging
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
PRODUCTS_TABLE = os.environ.get("PRODUCTS_TABLE", "vroom-dash-products-dev")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
products_table = dynamodb.Table(PRODUCTS_TABLE)

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


def _decimal_to_num(obj):
    """Decimal → int/float 재귀 변환"""
    if isinstance(obj, Decimal):
        return int(obj) if obj == int(obj) else float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_num(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decimal_to_num(i) for i in obj]
    return obj


def _scan_all() -> list[dict]:
    """전체 상품 Scan (30개이므로 OK)"""
    resp = products_table.scan()
    return _decimal_to_num(resp.get("Items", []))


def search_products(params: dict) -> dict:
    query = params.get("query", "").lower()
    category = params.get("category", "")
    min_age = int(params.get("min_age", 0))
    max_price = int(params.get("max_price", 0))

    # 카테고리 GSI 사용 가능
    if category and not query:
        resp = products_table.query(
            IndexName="category-index",
            KeyConditionExpression=Key("category").eq(category),
        )
        items = _decimal_to_num(resp.get("Items", []))
    else:
        items = _scan_all()

    results = []
    for p in items:
        # 키워드 필터
        if query:
            searchable = f"{p.get('name','')} {p.get('category','')} {p.get('brand','')} {p.get('description','')}".lower()
            if query not in searchable:
                continue

        # 카테고리 필터 (scan 경우)
        if category and p.get("category") != category:
            continue

        # 연령 필터
        if min_age > 0:
            age_str = p.get("recommended_age", "0")
            age_num = int("".join(c for c in str(age_str) if c.isdigit()) or "0")
            if age_num > min_age:
                continue

        # 가격 필터
        price = int(p.get("price", 0))
        discount = int(p.get("discount_rate", 0))
        discounted = int(price * (1 - discount / 100))
        if max_price > 0 and discounted > max_price:
            continue

        results.append({
            "product_id": p["product_id"],
            "name": p["name"],
            "category": p.get("category", ""),
            "brand": p.get("brand", ""),
            "price": price,
            "discount_rate": discount,
            "discounted_price": discounted,
            "stock": int(p.get("stock", 0)),
            "recommended_age": p.get("recommended_age", ""),
            "image_url": p.get("image_url", ""),
        })

    return {"products": results, "total": len(results)}


def get_product_detail(params: dict) -> dict:
    product_id = params["product_id"]
    resp = products_table.get_item(Key={"product_id": product_id})
    p = resp.get("Item")
    if not p:
        return {"error": f"상품 ID '{product_id}'에 해당하는 상품을 찾을 수 없습니다."}

    p = _decimal_to_num(p)
    price = int(p.get("price", 0))
    discount = int(p.get("discount_rate", 0))

    return {
        "product_id": p["product_id"],
        "name": p["name"],
        "category": p.get("category", ""),
        "brand": p.get("brand", ""),
        "price": price,
        "discount_rate": discount,
        "discounted_price": int(price * (1 - discount / 100)),
        "stock": int(p.get("stock", 0)),
        "recommended_age": p.get("recommended_age", ""),
        "specs": p.get("specs", {}),
        "description": p.get("description", ""),
        "image_url": p.get("image_url", ""),
    }


def recommend_products(params: dict) -> dict:
    age = int(params.get("age", 0))
    budget = int(params.get("budget", 0))
    category = params.get("category", "")
    preference = params.get("preference", "").lower()

    items = _scan_all()
    candidates = []

    for p in items:
        score = 0
        price = int(p.get("price", 0))
        discount = int(p.get("discount_rate", 0))
        discounted = int(price * (1 - discount / 100))
        stock = int(p.get("stock", 0))
        age_str = p.get("recommended_age", "0")
        age_num = int("".join(c for c in str(age_str) if c.isdigit()) or "0")

        # 연령 적합성
        if age > 0:
            if age_num <= age:
                score += 3
            elif age_num <= age + 2:
                score += 1
            else:
                continue

        # 예산 적합성
        if budget > 0:
            if discounted <= budget:
                score += 2
            else:
                continue

        # 카테고리
        if category and p.get("category") == category:
            score += 2

        # 선호도
        if preference:
            desc = f"{p.get('name','')} {p.get('description','')}".lower()
            if "교육" in preference and ("조립" in desc or "stem" in desc or "태양" in desc):
                score += 3
            if "야외" in preference and ("오프로드" in desc or "수륙" in desc or "몬스터" in desc):
                score += 3
            if "초보" in preference and ("입문" in desc or "초급" in desc or "쉽" in desc):
                score += 3

        if stock > 10:
            score += 1
        if discount > 0:
            score += 1

        candidates.append((score, p, discounted))

    candidates.sort(key=lambda x: x[0], reverse=True)
    top = candidates[:5]

    recommendations = []
    for score, p, discounted in top:
        reasons = []
        if age > 0:
            reasons.append(f"권장 연령({p.get('recommended_age','')})이 적합합니다")
        if budget > 0 and discounted <= budget:
            reasons.append(f"예산 내 가격({discounted:,}원)입니다")
        dr = int(p.get("discount_rate", 0))
        if dr > 0:
            reasons.append(f"현재 {dr}% 할인 중입니다")

        recommendations.append({
            "product_id": p["product_id"],
            "name": p["name"],
            "category": p.get("category", ""),
            "price": int(p.get("price", 0)),
            "discount_rate": dr,
            "discounted_price": discounted,
            "recommended_age": p.get("recommended_age", ""),
            "image_url": p.get("image_url", ""),
            "reasoning": ". ".join(reasons) if reasons else "인기 상품입니다",
        })

    return {"recommendations": recommendations, "total": len(recommendations)}


TOOLS = {
    "search_products": search_products,
    "get_product_detail": get_product_detail,
    "recommend_products": recommend_products,
}


def lambda_handler(event, context):
    """
    Lambda 엔트리포인트 - AgentCore Gateway에서 호출됩니다.

    AgentCore Gateway 호출 형식:
    - event: inputSchema properties 값들 (예: {"query": "RC카", "category": "전동RC카"})
    - context.client_context.custom['bedrockAgentCoreToolName']: "ProductTools___search_products"
    """
    logger.info(f"Event: {json.dumps(event, ensure_ascii=False, default=str)}")

    # Context에서 tool name 추출 (AgentCore Gateway 형식)
    tool_name = _extract_tool_name(context)
    logger.info(f"Extracted tool_name: {tool_name}")

    # event 자체가 parameters (AgentCore Gateway는 inputSchema properties를 event로 전달)
    params = event

    if tool_name not in TOOLS:
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
