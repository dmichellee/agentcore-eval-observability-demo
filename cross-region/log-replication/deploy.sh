#!/bin/bash
set -euo pipefail

# ============================================================
# Cross-Region Log Replicator - Deploy
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="${1:-${SCRIPT_DIR}/config.sh}"
if [ ! -f "${CONFIG_FILE}" ]; then
  echo "ERROR: Config file not found: ${CONFIG_FILE}"
  echo "Usage: $0 [path/to/config.sh]"
  exit 1
fi
source "${CONFIG_FILE}"

echo "============================================================"
echo " Cross-Region Log Replicator - Deploy"
echo "============================================================"
echo " Account:     ${ACCOUNT_ID}"
echo " Source:      ${SOURCE_LOG_GROUP} (${SOURCE_REGION})"
echo " Destination: ${DEST_LOG_GROUP} (${DEST_REGION})"
echo "============================================================"
echo ""

# ----------------------------------------------------------
# 1. Create destination log group (if not exists)
# ----------------------------------------------------------
echo "[1/5] Creating destination log group..."
aws logs create-log-group \
  --log-group-name "${DEST_LOG_GROUP}" \
  --region "${DEST_REGION}" 2>/dev/null \
  && echo "  -> Created: ${DEST_LOG_GROUP}" \
  || echo "  -> Already exists: ${DEST_LOG_GROUP}"

# ----------------------------------------------------------
# 2. Create IAM role
# ----------------------------------------------------------
echo "[2/5] Creating IAM role: ${IAM_ROLE_NAME}..."

TRUST_POLICY=$(cat <<'POLICY'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
POLICY
)

aws iam create-role \
  --role-name "${IAM_ROLE_NAME}" \
  --assume-role-policy-document "${TRUST_POLICY}" \
  --no-cli-pager >/dev/null 2>&1 \
  && echo "  -> Created role" \
  || echo "  -> Role already exists"

INLINE_POLICY=$(cat <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": [
        "arn:aws:logs:${SOURCE_REGION}:${ACCOUNT_ID}:log-group:/aws/lambda/${LAMBDA_FUNCTION_NAME}:*",
        "arn:aws:logs:${DEST_REGION}:${ACCOUNT_ID}:log-group:${DEST_LOG_GROUP}:*"
      ]
    }
  ]
}
POLICY
)

aws iam put-role-policy \
  --role-name "${IAM_ROLE_NAME}" \
  --policy-name "log-replicator-policy" \
  --policy-document "${INLINE_POLICY}" \
  --no-cli-pager
echo "  -> Attached inline policy"

echo "  -> Waiting for IAM role propagation..."
sleep 10

# ----------------------------------------------------------
# 3. Package Lambda function
# ----------------------------------------------------------
echo "[3/5] Packaging Lambda function..."

WORK_DIR=$(mktemp -d)
cp "${SCRIPT_DIR}/lambda_function.py" "${WORK_DIR}/lambda_function.py"
(cd "${WORK_DIR}" && zip -q lambda.zip lambda_function.py)
echo "  -> Package created: ${WORK_DIR}/lambda.zip"

# ----------------------------------------------------------
# 4. Deploy Lambda function
# ----------------------------------------------------------
echo "[4/5] Deploying Lambda function: ${LAMBDA_FUNCTION_NAME}..."

LAMBDA_EXISTS=$(aws lambda get-function \
  --function-name "${LAMBDA_FUNCTION_NAME}" \
  --region "${SOURCE_REGION}" 2>/dev/null && echo "yes" || echo "no")

if [ "${LAMBDA_EXISTS}" = "no" ]; then
  aws lambda create-function \
    --function-name "${LAMBDA_FUNCTION_NAME}" \
    --runtime "${LAMBDA_RUNTIME}" \
    --role "${IAM_ROLE_ARN}" \
    --handler "lambda_function.handler" \
    --zip-file "fileb://${WORK_DIR}/lambda.zip" \
    --timeout "${LAMBDA_TIMEOUT}" \
    --memory-size "${LAMBDA_MEMORY}" \
    --environment "Variables={DEST_REGION=${DEST_REGION},DEST_LOG_GROUP=${DEST_LOG_GROUP},DEST_LOG_STREAM=${DEST_LOG_STREAM},ALLOWED_SOURCE_STREAMS=${ALLOWED_SOURCE_STREAMS:-}}" \
    --region "${SOURCE_REGION}" \
    --no-cli-pager >/dev/null
  echo "  -> Created Lambda function"
else
  aws lambda update-function-code \
    --function-name "${LAMBDA_FUNCTION_NAME}" \
    --zip-file "fileb://${WORK_DIR}/lambda.zip" \
    --region "${SOURCE_REGION}" \
    --no-cli-pager >/dev/null

  # Wait for update to complete before updating config
  aws lambda wait function-updated \
    --function-name "${LAMBDA_FUNCTION_NAME}" \
    --region "${SOURCE_REGION}"

  aws lambda update-function-configuration \
    --function-name "${LAMBDA_FUNCTION_NAME}" \
    --runtime "${LAMBDA_RUNTIME}" \
    --role "${IAM_ROLE_ARN}" \
    --handler "lambda_function.handler" \
    --timeout "${LAMBDA_TIMEOUT}" \
    --memory-size "${LAMBDA_MEMORY}" \
    --environment "Variables={DEST_REGION=${DEST_REGION},DEST_LOG_GROUP=${DEST_LOG_GROUP},DEST_LOG_STREAM=${DEST_LOG_STREAM},ALLOWED_SOURCE_STREAMS=${ALLOWED_SOURCE_STREAMS:-}}" \
    --region "${SOURCE_REGION}" \
    --no-cli-pager >/dev/null
  echo "  -> Updated existing Lambda function"
fi

# Wait for Lambda to become Active
aws lambda wait function-active-v2 \
  --function-name "${LAMBDA_FUNCTION_NAME}" \
  --region "${SOURCE_REGION}"

# Grant CloudWatch Logs permission to invoke Lambda
LAMBDA_ARN=$(aws lambda get-function \
  --function-name "${LAMBDA_FUNCTION_NAME}" \
  --region "${SOURCE_REGION}" \
  --query 'Configuration.FunctionArn' --output text)

aws lambda add-permission \
  --function-name "${LAMBDA_FUNCTION_NAME}" \
  --statement-id "AllowCloudWatchLogs" \
  --principal "logs.${SOURCE_REGION}.amazonaws.com" \
  --action "lambda:InvokeFunction" \
  --source-arn "arn:aws:logs:${SOURCE_REGION}:${ACCOUNT_ID}:log-group:${SOURCE_LOG_GROUP}:*" \
  --region "${SOURCE_REGION}" \
  --no-cli-pager >/dev/null 2>&1 \
  && echo "  -> Added CloudWatch Logs invoke permission" \
  || echo "  -> Invoke permission already exists"

# ----------------------------------------------------------
# 5. Create subscription filter
# ----------------------------------------------------------
echo "[5/5] Creating subscription filter: ${SUBSCRIPTION_FILTER_NAME}..."

aws logs put-subscription-filter \
  --log-group-name "${SOURCE_LOG_GROUP}" \
  --filter-name "${SUBSCRIPTION_FILTER_NAME}" \
  --filter-pattern "" \
  --destination-arn "${LAMBDA_ARN}" \
  --region "${SOURCE_REGION}" \
  --no-cli-pager
echo "  -> Subscription filter created"

# ----------------------------------------------------------
# Cleanup temp files
# ----------------------------------------------------------
rm -rf "${WORK_DIR}"

echo ""
echo "============================================================"
echo " Deploy complete!"
echo "============================================================"
echo " Lambda:      ${LAMBDA_ARN}"
echo " Filter:      ${SUBSCRIPTION_FILTER_NAME}"
echo ""
echo " Logs from:"
echo "   ${SOURCE_LOG_GROUP} (${SOURCE_REGION})"
echo " will be forwarded to:"
echo "   ${DEST_LOG_GROUP}:${DEST_LOG_STREAM} (${DEST_REGION})"
echo "============================================================"
