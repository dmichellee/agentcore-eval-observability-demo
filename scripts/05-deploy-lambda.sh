#!/bin/bash
# ============================================================
# Lambda 함수 배포 (3개: order-tools, product-tools, tech-guide)
# ============================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
LAMBDA_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${LAMBDA_ROLE_NAME}"
TEMP_DIR=$(mktemp -d)

echo "=========================================="
echo " Lambda 함수 배포"
echo "=========================================="

deploy_lambda() {
  local FUNC_NAME=$1
  local SOURCE_DIR=$2
  local ENV_VARS=$3
  local ZIP_FILE="${TEMP_DIR}/${FUNC_NAME}.zip"

  echo "[*] Deploying: ${FUNC_NAME}"

  # 패키징
  cd "${SOURCE_DIR}"
  zip -j "${ZIP_FILE}" handler.py > /dev/null
  cd "${PROJECT_ROOT}"

  # 함수 존재 여부 확인
  if aws lambda get-function --function-name "${FUNC_NAME}" --region "${AWS_REGION}" --no-cli-pager 2>/dev/null; then
    # 업데이트
    echo "  -> Updating existing function..."
    aws lambda update-function-code \
      --function-name "${FUNC_NAME}" \
      --zip-file "fileb://${ZIP_FILE}" \
      --region "${AWS_REGION}" \
      --no-cli-pager > /dev/null

    # 코드 업데이트 완료 대기
    aws lambda wait function-updated --function-name "${FUNC_NAME}" --region "${AWS_REGION}"

    aws lambda update-function-configuration \
      --function-name "${FUNC_NAME}" \
      --environment "${ENV_VARS}" \
      --region "${AWS_REGION}" \
      --no-cli-pager > /dev/null
  else
    # 신규 생성
    echo "  -> Creating new function..."
    aws lambda create-function \
      --function-name "${FUNC_NAME}" \
      --runtime "${LAMBDA_RUNTIME}" \
      --role "${LAMBDA_ROLE_ARN}" \
      --handler "handler.lambda_handler" \
      --zip-file "fileb://${ZIP_FILE}" \
      --timeout 30 \
      --memory-size 256 \
      --environment "${ENV_VARS}" \
      --region "${AWS_REGION}" \
      --no-cli-pager > /dev/null
  fi

  echo "  -> ${FUNC_NAME} deployed"
}

# NOTE: AWS_REGION is a Lambda reserved env var (auto-set by Lambda runtime).
# Do NOT pass it explicitly. Use ORDERS_TABLE, PRODUCTS_TABLE, KNOWLEDGE_BASE_ID only.

# --- 1. order-tools ---
deploy_lambda \
  "${ORDER_TOOLS_LAMBDA}" \
  "${PROJECT_ROOT}/lambda/order-tools" \
  '{"Variables":{"ORDERS_TABLE":"'"${ORDERS_TABLE}"'"}}'

# --- 2. product-tools ---
deploy_lambda \
  "${PRODUCT_TOOLS_LAMBDA}" \
  "${PROJECT_ROOT}/lambda/product-tools" \
  '{"Variables":{"PRODUCTS_TABLE":"'"${PRODUCTS_TABLE}"'"}}'

# --- 3. tech-guide ---
KB_ID="${KNOWLEDGE_BASE_ID:-REPLACE_WITH_KB_ID}"
deploy_lambda \
  "${TECH_GUIDE_LAMBDA}" \
  "${PROJECT_ROOT}/lambda/tech-guide" \
  '{"Variables":{"KNOWLEDGE_BASE_ID":"'"${KB_ID}"'"}}'

# 정리
rm -rf "${TEMP_DIR}"

echo ""
echo "Lambda functions deployed:"
echo "  ${ORDER_TOOLS_LAMBDA}"
echo "  ${PRODUCT_TOOLS_LAMBDA}"
echo "  ${TECH_GUIDE_LAMBDA}"
echo ""
echo "NOTE: If KNOWLEDGE_BASE_ID was 'REPLACE_WITH_KB_ID',"
echo "update tech-guide Lambda env var after KB is created."
