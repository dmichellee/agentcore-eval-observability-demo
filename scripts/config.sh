#!/bin/bash
# ============================================================
# Vroom&Dash 프로젝트 공통 설정
# ============================================================

export AWS_REGION="us-east-1"
export PROJECT_PREFIX="vroom-dash"
export ENV="dev"  # dev | staging | prod

# --- DynamoDB ---
export PRODUCTS_TABLE="${PROJECT_PREFIX}-products-${ENV}"
export ORDERS_TABLE="${PROJECT_PREFIX}-orders-${ENV}"
export CUSTOMERS_TABLE="${PROJECT_PREFIX}-customers-${ENV}"

# --- S3 ---
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "unknown")
export TECH_GUIDES_BUCKET="${PROJECT_PREFIX}-tech-guides-${ENV}-${ACCOUNT_ID}"

# --- Lambda ---
export ORDER_TOOLS_LAMBDA="${PROJECT_PREFIX}-order-tools-${ENV}"
export PRODUCT_TOOLS_LAMBDA="${PROJECT_PREFIX}-product-tools-${ENV}"
export TECH_GUIDE_LAMBDA="${PROJECT_PREFIX}-tech-guide-${ENV}"
export LAMBDA_RUNTIME="python3.12"

# --- IAM ---
export AGENT_ROLE_NAME="VroomDashAgentRole-${ENV}"
export LAMBDA_ROLE_NAME="VroomDashLambdaRole-${ENV}"

# --- Cognito ---
export COGNITO_USER_POOL_NAME="${PROJECT_PREFIX}-users-${ENV}"

# --- AgentCore ---
export AGENTCORE_RUNTIME_ID="${PROJECT_PREFIX}-agent-${ENV}"
export AGENTCORE_MEMORY_ID="${PROJECT_PREFIX}-memory-${ENV}"
export AGENTCORE_GATEWAY_ID="${PROJECT_PREFIX}-gateway-${ENV}"
export AGENTCORE_EVAL_ID="${PROJECT_PREFIX}-eval-${ENV}"

# --- Bedrock ---
export MODEL_ID="anthropic.claude-haiku-4-5-20250514-v1:0"
export EMBEDDING_MODEL_ID="cohere.embed-multilingual-v3"
export KB_NAME="${PROJECT_PREFIX}-tech-kb-${ENV}"

echo "[config] Environment: ${ENV}, Region: ${AWS_REGION}, Prefix: ${PROJECT_PREFIX}"
