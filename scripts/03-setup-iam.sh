#!/bin/bash
# ============================================================
# IAM 역할 생성: VroomDashAgentRole, VroomDashLambdaRole
# ============================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "=========================================="
echo " IAM 역할 생성 (Account: ${ACCOUNT_ID})"
echo "=========================================="

# -------------------------------------------------------
# 1. Lambda 실행 역할 (VroomDashLambdaRole)
# -------------------------------------------------------
echo "[1/2] Creating Lambda role: ${LAMBDA_ROLE_NAME}"

LAMBDA_TRUST_POLICY=$(cat <<'POLICY'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}
POLICY
)

aws iam create-role \
  --role-name "${LAMBDA_ROLE_NAME}" \
  --assume-role-policy-document "${LAMBDA_TRUST_POLICY}" \
  --no-cli-pager 2>/dev/null \
  && echo "  -> Role created" \
  || echo "  -> Role already exists"

# Lambda 기본 실행 권한
aws iam attach-role-policy \
  --role-name "${LAMBDA_ROLE_NAME}" \
  --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" \
  --no-cli-pager

# DynamoDB 읽기 권한
LAMBDA_DYNAMO_POLICY=$(cat <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:${AWS_REGION}:${ACCOUNT_ID}:table/${PRODUCTS_TABLE}",
        "arn:aws:dynamodb:${AWS_REGION}:${ACCOUNT_ID}:table/${PRODUCTS_TABLE}/index/*",
        "arn:aws:dynamodb:${AWS_REGION}:${ACCOUNT_ID}:table/${ORDERS_TABLE}",
        "arn:aws:dynamodb:${AWS_REGION}:${ACCOUNT_ID}:table/${ORDERS_TABLE}/index/*",
        "arn:aws:dynamodb:${AWS_REGION}:${ACCOUNT_ID}:table/${CUSTOMERS_TABLE}"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:Retrieve"
      ],
      "Resource": "arn:aws:bedrock:${AWS_REGION}:${ACCOUNT_ID}:knowledge-base/*"
    }
  ]
}
POLICY
)

aws iam put-role-policy \
  --role-name "${LAMBDA_ROLE_NAME}" \
  --policy-name "VroomDashLambdaDataAccess" \
  --policy-document "${LAMBDA_DYNAMO_POLICY}" \
  --no-cli-pager
echo "  -> DynamoDB + KB policies attached"

# -------------------------------------------------------
# 2. AgentCore Agent 역할 (VroomDashAgentRole)
# -------------------------------------------------------
echo "[2/2] Creating Agent role: ${AGENT_ROLE_NAME}"

AGENT_TRUST_POLICY=$(cat <<'POLICY'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "bedrock.amazonaws.com",
          "bedrock-agentcore.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
POLICY
)

aws iam create-role \
  --role-name "${AGENT_ROLE_NAME}" \
  --assume-role-policy-document "${AGENT_TRUST_POLICY}" \
  --no-cli-pager 2>/dev/null \
  && echo "  -> Role created" \
  || echo "  -> Role already exists"

AGENT_PERMISSIONS=$(cat <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvokeModel",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:${AWS_REGION}::foundation-model/${MODEL_ID}"
    },
    {
      "Sid": "BedrockKB",
      "Effect": "Allow",
      "Action": "bedrock:Retrieve",
      "Resource": "arn:aws:bedrock:${AWS_REGION}:${ACCOUNT_ID}:knowledge-base/*"
    },
    {
      "Sid": "LambdaInvoke",
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:${AWS_REGION}:${ACCOUNT_ID}:function:${PROJECT_PREFIX}-*"
    },
    {
      "Sid": "AgentCoreMemory",
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:CreateMemory",
        "bedrock-agentcore:GetMemory",
        "bedrock-agentcore:DeleteMemory",
        "bedrock-agentcore:PutEvent",
        "bedrock-agentcore:GetEvent",
        "bedrock-agentcore:ListEvents",
        "bedrock-agentcore:ListSessions",
        "bedrock-agentcore:ListMemoryRecords",
        "bedrock-agentcore:RetrieveMemoryRecords"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AgentCoreGateway",
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeTool",
        "bedrock-agentcore:ListTools"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AgentCoreRuntime",
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeAgent",
        "bedrock-agentcore:InvokeAgentRuntime",
        "bedrock-agentcore:GetSession",
        "bedrock-agentcore:CreateSession",
        "bedrock-agentcore:DeleteSession"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Observability",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "cloudwatch:PutMetricData",
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords"
      ],
      "Resource": "*"
    }
  ]
}
POLICY
)

aws iam put-role-policy \
  --role-name "${AGENT_ROLE_NAME}" \
  --policy-name "VroomDashAgentPermissions" \
  --policy-document "${AGENT_PERMISSIONS}" \
  --no-cli-pager
echo "  -> Agent permissions attached"

echo ""
echo "IAM roles created:"
echo "  Lambda: arn:aws:iam::${ACCOUNT_ID}:role/${LAMBDA_ROLE_NAME}"
echo "  Agent:  arn:aws:iam::${ACCOUNT_ID}:role/${AGENT_ROLE_NAME}"
