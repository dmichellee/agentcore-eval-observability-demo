"""
Lambda Handler: order-tools
Tools: lookup_order, track_delivery, request_return
Data source: DynamoDB (vroom-dash-orders)

AgentCore Gateway Lambda 호출 형식:
- event: inputSchema의 properties 값들 (예: {"order_id": "..."})
- context.client_context.custom['bedrockAgentCoreToolName']: "TargetName___tool_name"
"""
import json
import os
import uuid
import logging

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
ORDERS_TABLE = os.environ.get("ORDERS_TABLE", "vroom-dash-orders-dev")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
orders_table = dynamodb.Table(ORDERS_TABLE)

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


def _get_order(order_id: str) -> dict | None:
    resp = orders_table.get_item(Key={"order_id": order_id})
    item = resp.get("Item")
    if item:
        # Decimal -> int/float 변환
        return json.loads(json.dumps(item, default=str))
    return None


def lookup_order(params: dict) -> dict:
    order_id = params["order_id"]
    order = _get_order(order_id)
    if not order:
        return {"error": f"주문번호 '{order_id}'에 해당하는 주문을 찾을 수 없습니다."}

    return {
        "order_id": order["order_id"],
        "customer_name": order["customer_name"],
        "items": order["items"],
        "total_amount": order["total_amount"],
        "order_date": order["order_date"],
        "order_status": order["order_status"],
        "shipping": {
            "carrier": order["shipping"].get("carrier", ""),
            "tracking_number": order["shipping"].get("tracking_number", ""),
            "status": order["shipping"].get("status", ""),
            "eta": order["shipping"].get("eta", ""),
        },
    }


def track_delivery(params: dict) -> dict:
    order_id = params["order_id"]
    order = _get_order(order_id)
    if not order:
        return {"error": f"주문번호 '{order_id}'에 해당하는 주문을 찾을 수 없습니다."}

    shipping = order["shipping"]
    result = {
        "order_id": order["order_id"],
        "order_status": order["order_status"],
        "shipping_status": shipping.get("status", ""),
        "location": shipping.get("location") or "아직 배송 정보가 없습니다",
        "carrier": shipping.get("carrier") or "택배사 미배정",
        "tracking_number": shipping.get("tracking_number") or "운송장 미발급",
        "eta": shipping.get("eta", ""),
    }
    if "delivered_date" in shipping:
        result["delivered_date"] = shipping["delivered_date"]
    return result


def request_return(params: dict) -> dict:
    order_id = params["order_id"]
    reason = params["reason"]

    order = _get_order(order_id)
    if not order:
        return {"error": f"주문번호 '{order_id}'에 해당하는 주문을 찾을 수 없습니다."}

    if order["order_status"] not in ("배송완료", "배송중"):
        return {
            "error": f"현재 주문 상태가 '{order['order_status']}'이므로 반품/교환 요청이 불가합니다."
        }

    return_id = f"RET-{uuid.uuid4().hex[:8].upper()}"
    return {
        "return_id": return_id,
        "order_id": order_id,
        "status": "반품 접수 완료",
        "reason": reason,
        "instructions": [
            f"반품 접수번호: {return_id}",
            "반품 접수가 완료되었습니다.",
            "택배 기사가 2~3일 내 방문하여 상품을 수거합니다.",
            "상품은 원래 포장 상태로 준비해주세요.",
            "반품 상품 확인 후 3~5일 내 환불 처리됩니다.",
            "환불은 원래 결제 수단으로 진행됩니다.",
            "문의사항은 고객센터 1588-VROOM으로 연락해주세요.",
        ],
    }


# Tool dispatcher
TOOLS = {
    "lookup_order": lookup_order,
    "track_delivery": track_delivery,
    "request_return": request_return,
}


def lambda_handler(event, context):
    """
    Lambda 엔트리포인트 - AgentCore Gateway에서 호출됩니다.

    AgentCore Gateway 호출 형식:
    - event: inputSchema properties 값들 (예: {"order_id": "ORD-001"})
    - context.client_context.custom['bedrockAgentCoreToolName']: "OrderTools___lookup_order"
    """
    logger.info(f"Event: {json.dumps(event, ensure_ascii=False)}")

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
