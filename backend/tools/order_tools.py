import json
import uuid
from strands import tool
from data.orders import ORDERS


def _find_order(order_id: str) -> dict | None:
    for order in ORDERS:
        if order["order_id"] == order_id:
            return order
    return None


@tool
def lookup_order(order_id: str) -> str:
    """주문번호로 주문 상태를 조회합니다. 주문 상태, 상품명, 결제금액, 배송 정보를 확인할 수 있습니다.

    Args:
        order_id: 주문번호 (예: ORD-001)

    Returns:
        주문 상태, 상품명, 결제금액, 배송 정보를 포함한 주문 정보
    """
    order = _find_order(order_id)
    if not order:
        return json.dumps(
            {"error": f"주문번호 '{order_id}'에 해당하는 주문을 찾을 수 없습니다."},
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "order_id": order["order_id"],
            "customer_name": order["customer_name"],
            "items": order["items"],
            "total_amount": order["total_amount"],
            "order_date": order["order_date"],
            "order_status": order["order_status"],
            "shipping": {
                "carrier": order["shipping"]["carrier"],
                "tracking_number": order["shipping"]["tracking_number"],
                "status": order["shipping"]["status"],
                "eta": order["shipping"]["eta"],
            },
        },
        ensure_ascii=False,
    )


@tool
def track_delivery(order_id: str) -> str:
    """주문번호로 배송 추적 정보를 조회합니다. 배송 상태, 현재 위치, 택배사, 예상 도착일을 확인합니다.

    Args:
        order_id: 주문번호 (예: ORD-001)

    Returns:
        배송 상태, 현재 위치, 택배사, 운송장번호, 예상 도착일 정보
    """
    order = _find_order(order_id)
    if not order:
        return json.dumps(
            {"error": f"주문번호 '{order_id}'에 해당하는 주문을 찾을 수 없습니다."},
            ensure_ascii=False,
        )

    shipping = order["shipping"]
    result = {
        "order_id": order["order_id"],
        "order_status": order["order_status"],
        "shipping_status": shipping["status"],
        "location": shipping["location"] or "아직 배송 정보가 없습니다",
        "carrier": shipping["carrier"] or "택배사 미배정",
        "tracking_number": shipping["tracking_number"] or "운송장 미발급",
        "eta": shipping["eta"],
    }
    if "delivered_date" in shipping:
        result["delivered_date"] = shipping["delivered_date"]

    return json.dumps(result, ensure_ascii=False)


@tool
def request_return(order_id: str, reason: str) -> str:
    """반품 또는 교환을 요청합니다. 주문번호와 반품 사유가 필요합니다.

    Args:
        order_id: 반품/교환할 주문번호 (예: ORD-001)
        reason: 반품/교환 사유 (예: 상품 불량, 단순 변심, 오배송 등)

    Returns:
        반품 접수 확인 및 반품 절차 안내
    """
    order = _find_order(order_id)
    if not order:
        return json.dumps(
            {"error": f"주문번호 '{order_id}'에 해당하는 주문을 찾을 수 없습니다."},
            ensure_ascii=False,
        )

    if order["order_status"] not in ("배송완료", "배송중"):
        return json.dumps(
            {
                "error": f"현재 주문 상태가 '{order['order_status']}'이므로 반품/교환 요청이 불가합니다. 배송완료 또는 배송중 상태에서만 가능합니다."
            },
            ensure_ascii=False,
        )

    return_id = f"RET-{uuid.uuid4().hex[:8].upper()}"

    return json.dumps(
        {
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
        },
        ensure_ascii=False,
    )
