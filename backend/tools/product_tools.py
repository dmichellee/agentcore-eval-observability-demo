import json
from strands import tool
from data.products import PRODUCTS


def _find_product(product_id: str) -> dict | None:
    for product in PRODUCTS:
        if product["product_id"] == product_id:
            return product
    return None


@tool
def search_products(query: str, category: str = "", min_age: int = 0, max_price: int = 0) -> str:
    """상품을 검색합니다. 키워드, 카테고리, 연령, 가격대 등으로 필터링할 수 있습니다.

    Args:
        query: 검색 키워드 (예: RC카, 조립, 미니카, 트랙 등)
        category: 카테고리 필터 (RC카, 미니카, 조립키트, 트랙세트 중 선택. 빈 문자열이면 전체 검색)
        min_age: 최소 권장 연령 필터 (숫자만 입력, 예: 5. 0이면 필터 없음)
        max_price: 최대 가격 필터 (원 단위, 예: 50000. 0이면 필터 없음)

    Returns:
        검색 조건에 맞는 상품 목록 (상품ID, 이름, 카테고리, 가격, 할인율, 재고, 권장연령)
    """
    results = []
    query_lower = query.lower()

    for product in PRODUCTS:
        # 키워드 매칭
        searchable = f"{product['name']} {product['category']} {product['brand']} {product['description']}".lower()
        if query_lower and query_lower not in searchable:
            continue

        # 카테고리 필터
        if category and product["category"] != category:
            continue

        # 연령 필터
        if min_age > 0:
            age_num = int("".join(c for c in product["recommended_age"] if c.isdigit()))
            if age_num > min_age:
                continue

        # 가격 필터 (할인 적용 가격)
        if max_price > 0:
            discounted = product["price"] * (1 - product["discount_rate"] / 100)
            if discounted > max_price:
                continue

        results.append(
            {
                "product_id": product["product_id"],
                "name": product["name"],
                "category": product["category"],
                "brand": product["brand"],
                "price": product["price"],
                "discount_rate": product["discount_rate"],
                "discounted_price": int(product["price"] * (1 - product["discount_rate"] / 100)),
                "stock": product["stock"],
                "recommended_age": product["recommended_age"],
                "image_url": product["image_url"],
            }
        )

    return json.dumps(
        {"products": results, "total": len(results)},
        ensure_ascii=False,
    )


@tool
def get_product_detail(product_id: str) -> str:
    """상품ID로 상품의 상세 정보를 조회합니다. 스펙, 가격, 재고, 설명 등 모든 정보를 확인할 수 있습니다.

    Args:
        product_id: 상품 ID (예: PRD-001)

    Returns:
        상품의 전체 상세 정보 (이름, 카테고리, 브랜드, 가격, 할인율, 재고, 권장연령, 스펙, 설명)
    """
    product = _find_product(product_id)
    if not product:
        return json.dumps(
            {"error": f"상품 ID '{product_id}'에 해당하는 상품을 찾을 수 없습니다."},
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "product_id": product["product_id"],
            "name": product["name"],
            "category": product["category"],
            "brand": product["brand"],
            "price": product["price"],
            "discount_rate": product["discount_rate"],
            "discounted_price": int(product["price"] * (1 - product["discount_rate"] / 100)),
            "stock": product["stock"],
            "recommended_age": product["recommended_age"],
            "specs": product["specs"],
            "description": product["description"],
            "image_url": product["image_url"],
        },
        ensure_ascii=False,
    )


@tool
def recommend_products(age: int = 0, budget: int = 0, category: str = "", preference: str = "") -> str:
    """고객의 취향과 조건에 맞는 상품을 추천합니다.

    Args:
        age: 아이의 나이 (예: 5. 0이면 연령 무관)
        budget: 예산 상한 (원 단위, 예: 50000. 0이면 예산 무관)
        category: 선호 카테고리 (RC카, 미니카, 조립키트, 트랙세트. 빈 문자열이면 전체)
        preference: 기타 선호 사항 (예: 교육용, 야외용, 선물용, 초보자용 등)

    Returns:
        추천 상품 목록과 추천 사유
    """
    candidates = []
    pref_lower = preference.lower()

    for product in PRODUCTS:
        score = 0

        # 연령 적합성
        if age > 0:
            age_num = int("".join(c for c in product["recommended_age"] if c.isdigit()))
            if age_num <= age:
                score += 3
            elif age_num <= age + 2:
                score += 1
            else:
                continue

        # 예산 적합성
        discounted = int(product["price"] * (1 - product["discount_rate"] / 100))
        if budget > 0:
            if discounted <= budget:
                score += 2
            else:
                continue

        # 카테고리 매칭
        if category and product["category"] == category:
            score += 2

        # 선호도 매칭
        if pref_lower:
            desc = f"{product['name']} {product['description']}".lower()
            if "교육" in pref_lower and ("조립" in desc or "stem" in desc or "태양" in desc):
                score += 3
            if "야외" in pref_lower and ("오프로드" in desc or "수륙" in desc or "몬스터" in desc):
                score += 3
            if "선물" in pref_lower and product["discount_rate"] > 0:
                score += 1
            if "초보" in pref_lower and ("입문" in desc or "초급" in desc or "쉽" in desc):
                score += 3

        # 재고 충분
        if product["stock"] > 10:
            score += 1

        # 할인 중
        if product["discount_rate"] > 0:
            score += 1

        candidates.append((score, product, discounted))

    # 점수순 정렬 후 상위 5개
    candidates.sort(key=lambda x: x[0], reverse=True)
    top = candidates[:5]

    recommendations = []
    for score, product, discounted in top:
        reasons = []
        if age > 0:
            reasons.append(f"권장 연령({product['recommended_age']})이 적합합니다")
        if budget > 0 and discounted <= budget:
            reasons.append(f"예산 내 가격({discounted:,}원)입니다")
        if product["discount_rate"] > 0:
            reasons.append(f"현재 {product['discount_rate']}% 할인 중입니다")
        if product["stock"] > 10:
            reasons.append("재고가 충분합니다")

        recommendations.append(
            {
                "product_id": product["product_id"],
                "name": product["name"],
                "category": product["category"],
                "price": product["price"],
                "discount_rate": product["discount_rate"],
                "discounted_price": discounted,
                "recommended_age": product["recommended_age"],
                "image_url": product["image_url"],
                "reasoning": ". ".join(reasons) if reasons else "인기 상품입니다",
            }
        )

    return json.dumps(
        {"recommendations": recommendations, "total": len(recommendations)},
        ensure_ascii=False,
    )
