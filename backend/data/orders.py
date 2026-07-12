ORDERS = [
    # === 김민준 (CUST-001) - 5건 ===
    {
        "order_id": "ORD-001",
        "customer_id": "CUST-001",
        "customer_name": "김민준",
        "items": [
            {"product_id": "PRD-001", "product_name": "스피드 레이서 RC카", "quantity": 1, "price": 45000}
        ],
        "total_amount": 40500,
        "order_date": "2025-03-28T10:30:00",
        "order_status": "배송완료",
        "shipping": {
            "carrier": "CJ대한통운",
            "tracking_number": "6023456789012",
            "status": "배달완료",
            "location": "서울 강남구",
            "eta": "2025-03-31",
            "delivered_date": "2025-03-31",
        },
    },
    {
        "order_id": "ORD-002",
        "customer_id": "CUST-001",
        "customer_name": "김민준",
        "items": [
            {"product_id": "PRD-011", "product_name": "클래식 스포츠카 미니카 5종 세트", "quantity": 1, "price": 25000},
            {"product_id": "PRD-013", "product_name": "풀백 레이싱카 미니카", "quantity": 2, "price": 8000},
        ],
        "total_amount": 41000,
        "order_date": "2025-04-01T14:20:00",
        "order_status": "배송중",
        "shipping": {
            "carrier": "한진택배",
            "tracking_number": "4567890123456",
            "status": "배송중",
            "location": "서울 송파 허브터미널",
            "eta": "2025-04-05",
        },
    },
    {
        "order_id": "ORD-003",
        "customer_id": "CUST-001",
        "customer_name": "김민준",
        "items": [
            {"product_id": "PRD-025", "product_name": "스피드 루프 트랙세트", "quantity": 1, "price": 55000}
        ],
        "total_amount": 49500,
        "order_date": "2025-04-03T09:15:00",
        "order_status": "배송준비",
        "shipping": {
            "carrier": "CJ대한통운",
            "tracking_number": "",
            "status": "상품 포장중",
            "location": "Vroom&Dash 물류센터",
            "eta": "2025-04-07",
        },
    },
    {
        "order_id": "ORD-004",
        "customer_id": "CUST-001",
        "customer_name": "김민준",
        "items": [
            {"product_id": "PRD-020", "product_name": "모터 자동차 조립키트 (초급)", "quantity": 1, "price": 15000}
        ],
        "total_amount": 13500,
        "order_date": "2025-04-04T16:45:00",
        "order_status": "결제완료",
        "shipping": {
            "carrier": "",
            "tracking_number": "",
            "status": "결제 확인됨",
            "location": "",
            "eta": "2025-04-08",
        },
    },
    {
        "order_id": "ORD-005",
        "customer_id": "CUST-001",
        "customer_name": "김민준",
        "items": [
            {"product_id": "PRD-008", "product_name": "변신 로봇 RC카", "quantity": 1, "price": 62000}
        ],
        "total_amount": 62000,
        "order_date": "2025-04-05T08:00:00",
        "order_status": "주문접수",
        "shipping": {
            "carrier": "",
            "tracking_number": "",
            "status": "주문 접수 대기",
            "location": "",
            "eta": "2025-04-09",
        },
    },
    # === 이서연 (CUST-002) - 5건 ===
    {
        "order_id": "ORD-006",
        "customer_id": "CUST-002",
        "customer_name": "이서연",
        "items": [
            {"product_id": "PRD-004", "product_name": "미니 레이싱 RC카 세트", "quantity": 1, "price": 35000}
        ],
        "total_amount": 28000,
        "order_date": "2025-03-25T11:00:00",
        "order_status": "배송완료",
        "shipping": {
            "carrier": "롯데택배",
            "tracking_number": "7890123456789",
            "status": "배달완료",
            "location": "경기 성남시 분당구",
            "eta": "2025-03-28",
            "delivered_date": "2025-03-27",
        },
    },
    {
        "order_id": "ORD-007",
        "customer_id": "CUST-002",
        "customer_name": "이서연",
        "items": [
            {"product_id": "PRD-007", "product_name": "공룡 RC카", "quantity": 1, "price": 52000},
            {"product_id": "PRD-023", "product_name": "고무동력 자동차 조립키트", "quantity": 2, "price": 12000},
        ],
        "total_amount": 70800,
        "order_date": "2025-04-01T17:30:00",
        "order_status": "배송중",
        "shipping": {
            "carrier": "CJ대한통운",
            "tracking_number": "6098765432101",
            "status": "배송중",
            "location": "경기 용인 허브",
            "eta": "2025-04-05",
        },
    },
    {
        "order_id": "ORD-008",
        "customer_id": "CUST-002",
        "customer_name": "이서연",
        "items": [
            {"product_id": "PRD-027", "product_name": "도시 드라이브 플레이 트랙세트", "quantity": 1, "price": 42000}
        ],
        "total_amount": 42000,
        "order_date": "2025-04-03T13:00:00",
        "order_status": "배송준비",
        "shipping": {
            "carrier": "한진택배",
            "tracking_number": "",
            "status": "상품 포장중",
            "location": "Vroom&Dash 물류센터",
            "eta": "2025-04-07",
        },
    },
    {
        "order_id": "ORD-009",
        "customer_id": "CUST-002",
        "customer_name": "이서연",
        "items": [
            {"product_id": "PRD-017", "product_name": "색칠 미니카 DIY 세트", "quantity": 3, "price": 19000}
        ],
        "total_amount": 54150,
        "order_date": "2025-04-04T10:20:00",
        "order_status": "결제완료",
        "shipping": {
            "carrier": "",
            "tracking_number": "",
            "status": "결제 확인됨",
            "location": "",
            "eta": "2025-04-08",
        },
    },
    {
        "order_id": "ORD-010",
        "customer_id": "CUST-002",
        "customer_name": "이서연",
        "items": [
            {"product_id": "PRD-010", "product_name": "앱 연동 스마트 RC카", "quantity": 1, "price": 95000}
        ],
        "total_amount": 85500,
        "order_date": "2025-04-05T09:30:00",
        "order_status": "주문접수",
        "shipping": {
            "carrier": "",
            "tracking_number": "",
            "status": "주문 접수 대기",
            "location": "",
            "eta": "2025-04-09",
        },
    },
    # === 박지호 (CUST-003) - 5건 ===
    {
        "order_id": "ORD-011",
        "customer_id": "CUST-003",
        "customer_name": "박지호",
        "items": [
            {"product_id": "PRD-003", "product_name": "몬스터 트럭 4WD RC카", "quantity": 1, "price": 89000}
        ],
        "total_amount": 89000,
        "order_date": "2025-03-20T15:00:00",
        "order_status": "배송완료",
        "shipping": {
            "carrier": "CJ대한통운",
            "tracking_number": "6011223344556",
            "status": "배달완료",
            "location": "부산 해운대구",
            "eta": "2025-03-24",
            "delivered_date": "2025-03-23",
        },
    },
    {
        "order_id": "ORD-012",
        "customer_id": "CUST-003",
        "customer_name": "박지호",
        "items": [
            {"product_id": "PRD-006", "product_name": "프로 레이서 RC카", "quantity": 1, "price": 120000},
            {"product_id": "PRD-022", "product_name": "RC카 조립키트 (상급)", "quantity": 1, "price": 65000},
        ],
        "total_amount": 185000,
        "order_date": "2025-04-02T12:10:00",
        "order_status": "배송중",
        "shipping": {
            "carrier": "CJ대한통운",
            "tracking_number": "6055667788990",
            "status": "배송중",
            "location": "대전 물류터미널",
            "eta": "2025-04-06",
        },
    },
    {
        "order_id": "ORD-013",
        "customer_id": "CUST-003",
        "customer_name": "박지호",
        "items": [
            {"product_id": "PRD-030", "product_name": "디럭스 멀티 트랙세트", "quantity": 1, "price": 115000}
        ],
        "total_amount": 103500,
        "order_date": "2025-04-03T18:00:00",
        "order_status": "배송준비",
        "shipping": {
            "carrier": "롯데택배",
            "tracking_number": "",
            "status": "상품 포장중",
            "location": "Vroom&Dash 물류센터",
            "eta": "2025-04-08",
        },
    },
    {
        "order_id": "ORD-014",
        "customer_id": "CUST-003",
        "customer_name": "박지호",
        "items": [
            {"product_id": "PRD-015", "product_name": "F1 레이싱카 미니카 컬렉션", "quantity": 2, "price": 32000},
            {"product_id": "PRD-029", "product_name": "자석 조립 트랙세트", "quantity": 1, "price": 62000},
        ],
        "total_amount": 126000,
        "order_date": "2025-04-04T20:00:00",
        "order_status": "결제완료",
        "shipping": {
            "carrier": "",
            "tracking_number": "",
            "status": "결제 확인됨",
            "location": "",
            "eta": "2025-04-09",
        },
    },
    {
        "order_id": "ORD-015",
        "customer_id": "CUST-003",
        "customer_name": "박지호",
        "items": [
            {"product_id": "PRD-009", "product_name": "수륙양용 RC카", "quantity": 1, "price": 58000}
        ],
        "total_amount": 55100,
        "order_date": "2025-04-05T07:45:00",
        "order_status": "주문접수",
        "shipping": {
            "carrier": "",
            "tracking_number": "",
            "status": "주문 접수 대기",
            "location": "",
            "eta": "2025-04-10",
        },
    },
]
