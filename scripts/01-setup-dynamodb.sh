#!/bin/bash
# ============================================================
# DynamoDB 테이블 생성
# 테이블 3개: products, orders, customers (+ GSI)
# ============================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

echo "=========================================="
echo " DynamoDB 테이블 생성"
echo "=========================================="

# --- 1. Products 테이블 ---
echo "[1/3] Creating table: ${PRODUCTS_TABLE}"
aws dynamodb create-table \
  --table-name "${PRODUCTS_TABLE}" \
  --attribute-definitions \
    AttributeName=product_id,AttributeType=S \
    AttributeName=category,AttributeType=S \
  --key-schema \
    AttributeName=product_id,KeyType=HASH \
  --global-secondary-indexes '[
    {
      "IndexName": "category-index",
      "KeySchema": [{"AttributeName": "category", "KeyType": "HASH"}],
      "Projection": {"ProjectionType": "ALL"},
      "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
    }
  ]' \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region "${AWS_REGION}" \
  --no-cli-pager \
  && echo "  -> ${PRODUCTS_TABLE} created" \
  || echo "  -> ${PRODUCTS_TABLE} already exists or error"

# --- 2. Orders 테이블 ---
echo "[2/3] Creating table: ${ORDERS_TABLE}"
aws dynamodb create-table \
  --table-name "${ORDERS_TABLE}" \
  --attribute-definitions \
    AttributeName=order_id,AttributeType=S \
    AttributeName=customer_id,AttributeType=S \
  --key-schema \
    AttributeName=order_id,KeyType=HASH \
  --global-secondary-indexes '[
    {
      "IndexName": "customer_id-index",
      "KeySchema": [{"AttributeName": "customer_id", "KeyType": "HASH"}],
      "Projection": {"ProjectionType": "ALL"},
      "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
    }
  ]' \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region "${AWS_REGION}" \
  --no-cli-pager \
  && echo "  -> ${ORDERS_TABLE} created" \
  || echo "  -> ${ORDERS_TABLE} already exists or error"

# --- 3. Customers 테이블 ---
echo "[3/3] Creating table: ${CUSTOMERS_TABLE}"
aws dynamodb create-table \
  --table-name "${CUSTOMERS_TABLE}" \
  --attribute-definitions \
    AttributeName=customer_id,AttributeType=S \
  --key-schema \
    AttributeName=customer_id,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region "${AWS_REGION}" \
  --no-cli-pager \
  && echo "  -> ${CUSTOMERS_TABLE} created" \
  || echo "  -> ${CUSTOMERS_TABLE} already exists or error"

# --- 테이블 활성화 대기 ---
echo ""
echo "Waiting for tables to become ACTIVE..."
for TABLE in "${PRODUCTS_TABLE}" "${ORDERS_TABLE}" "${CUSTOMERS_TABLE}"; do
  aws dynamodb wait table-exists --table-name "${TABLE}" --region "${AWS_REGION}"
  echo "  -> ${TABLE} is ACTIVE"
done

echo ""
echo "DynamoDB tables created successfully!"
echo "Next: Run 02-seed-data.py to load mock data."
