#!/bin/bash
set -euo pipefail

# ============================================================
# Cross-Region Log Replicator - Cleanup
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
echo " Cross-Region Log Replicator - Cleanup"
echo "============================================================"
echo " Account:  ${ACCOUNT_ID}"
echo " Region:   ${SOURCE_REGION}"
echo "============================================================"
echo ""

# ----------------------------------------------------------
# 1. Remove subscription filter
# ----------------------------------------------------------
echo "[1/3] Removing subscription filter: ${SUBSCRIPTION_FILTER_NAME}..."
aws logs delete-subscription-filter \
  --log-group-name "${SOURCE_LOG_GROUP}" \
  --filter-name "${SUBSCRIPTION_FILTER_NAME}" \
  --region "${SOURCE_REGION}" 2>/dev/null \
  && echo "  -> Deleted" \
  || echo "  -> Not found, skipping"

# ----------------------------------------------------------
# 2. Delete Lambda function
# ----------------------------------------------------------
echo "[2/3] Deleting Lambda function: ${LAMBDA_FUNCTION_NAME}..."
aws lambda delete-function \
  --function-name "${LAMBDA_FUNCTION_NAME}" \
  --region "${SOURCE_REGION}" 2>/dev/null \
  && echo "  -> Deleted" \
  || echo "  -> Not found, skipping"

# ----------------------------------------------------------
# 3. Delete IAM role (must remove inline policies first)
# ----------------------------------------------------------
echo "[3/3] Deleting IAM role: ${IAM_ROLE_NAME}..."

# List and delete all inline policies
POLICIES=$(aws iam list-role-policies \
  --role-name "${IAM_ROLE_NAME}" \
  --query 'PolicyNames[]' --output text 2>/dev/null || echo "")

if [ -n "${POLICIES}" ]; then
  for POLICY in ${POLICIES}; do
    aws iam delete-role-policy \
      --role-name "${IAM_ROLE_NAME}" \
      --policy-name "${POLICY}"
    echo "  -> Detached inline policy: ${POLICY}"
  done
fi

aws iam delete-role \
  --role-name "${IAM_ROLE_NAME}" 2>/dev/null \
  && echo "  -> Deleted role" \
  || echo "  -> Role not found, skipping"

echo ""
echo "============================================================"
echo " Cleanup complete!"
echo "============================================================"
echo ""
echo " NOTE: Destination log group was NOT deleted:"
echo "   ${DEST_LOG_GROUP} (${DEST_REGION})"
echo " Delete manually if no longer needed:"
echo "   aws logs delete-log-group --log-group-name '${DEST_LOG_GROUP}' --region ${DEST_REGION}"
echo "============================================================"
