#!/bin/bash
# ============================================================
# Cognito Identity Pool 생성
# 프론트엔드에서 SigV4 서명용 임시 AWS 자격 증명 획득
# ============================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "=========================================="
echo " Cognito Identity Pool 설정"
echo "=========================================="

# -------------------------------------------------------
# 0. 기존 Cognito User Pool / App Client 조회
# -------------------------------------------------------
USER_POOL_ID=$(aws cognito-idp list-user-pools --max-results 50 --region "${AWS_REGION}" --no-cli-pager \
  | python3 -c "
import sys, json
pools = json.load(sys.stdin)['UserPools']
for p in pools:
    if p['Name'] == '${COGNITO_USER_POOL_NAME}':
        print(p['Id'])
        break
" 2>/dev/null || echo "NOT_FOUND")

if [ "${USER_POOL_ID}" = "NOT_FOUND" ] || [ -z "${USER_POOL_ID}" ]; then
  echo "ERROR: User Pool '${COGNITO_USER_POOL_NAME}' not found. Run 06-setup-cognito.sh first."
  exit 1
fi
echo "  User Pool ID: ${USER_POOL_ID}"

APP_CLIENT_ID=$(aws cognito-idp list-user-pool-clients \
  --user-pool-id "${USER_POOL_ID}" \
  --max-results 10 \
  --region "${AWS_REGION}" \
  --no-cli-pager \
  | python3 -c "
import sys, json
clients = json.load(sys.stdin)['UserPoolClients']
for c in clients:
    print(c['ClientId'])
    break
" 2>/dev/null || echo "NOT_FOUND")

if [ -z "${APP_CLIENT_ID}" ] || [ "${APP_CLIENT_ID}" = "NOT_FOUND" ]; then
  echo "ERROR: App Client not found for pool ${USER_POOL_ID}. Run 06-setup-cognito.sh first."
  exit 1
fi
echo "  App Client ID: ${APP_CLIENT_ID}"

# -------------------------------------------------------
# 1. Identity Pool 생성
# -------------------------------------------------------
IDENTITY_POOL_NAME="${PROJECT_PREFIX}-identity-${ENV}"
echo ""
echo "[1/3] Creating Identity Pool: ${IDENTITY_POOL_NAME}"

PROVIDER_NAME="cognito-idp.${AWS_REGION}.amazonaws.com/${USER_POOL_ID}"

IP_RESULT=$(aws cognito-identity create-identity-pool \
  --identity-pool-name "${IDENTITY_POOL_NAME}" \
  --no-allow-unauthenticated-identities \
  --cognito-identity-providers \
    ProviderName="${PROVIDER_NAME}",ClientId="${APP_CLIENT_ID}",ServerSideTokenCheck=false \
  --region "${AWS_REGION}" \
  --no-cli-pager 2>&1) || true

IDENTITY_POOL_ID=$(echo "${IP_RESULT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['IdentityPoolId'])" 2>/dev/null || echo "")

if [ -z "${IDENTITY_POOL_ID}" ]; then
  # 이미 존재하는 경우 조회
  IDENTITY_POOL_ID=$(aws cognito-identity list-identity-pools --max-results 20 --region "${AWS_REGION}" --no-cli-pager \
    | python3 -c "
import sys, json
pools = json.load(sys.stdin)['IdentityPools']
for p in pools:
    if p['IdentityPoolName'] == '${IDENTITY_POOL_NAME}':
        print(p['IdentityPoolId'])
        break
" 2>/dev/null || echo "NOT_FOUND")
  echo "  -> Existing Identity Pool: ${IDENTITY_POOL_ID}"
else
  echo "  -> Identity Pool created: ${IDENTITY_POOL_ID}"
fi

if [ -z "${IDENTITY_POOL_ID}" ] || [ "${IDENTITY_POOL_ID}" = "NOT_FOUND" ]; then
  echo "ERROR: Identity Pool 생성/조회 실패."
  exit 1
fi

# -------------------------------------------------------
# 2. IAM Role for authenticated users
# -------------------------------------------------------
AUTH_ROLE_NAME="${PROJECT_PREFIX}-cognito-auth-role-${ENV}"
echo ""
echo "[2/3] Creating authenticated role: ${AUTH_ROLE_NAME}"

AUTH_TRUST_POLICY=$(cat <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "cognito-identity.amazonaws.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "cognito-identity.amazonaws.com:aud": "${IDENTITY_POOL_ID}"
        },
        "ForAnyValue:StringLike": {
          "cognito-identity.amazonaws.com:amr": "authenticated"
        }
      }
    }
  ]
}
POLICY
)

if aws iam create-role \
  --role-name "${AUTH_ROLE_NAME}" \
  --assume-role-policy-document "${AUTH_TRUST_POLICY}" \
  --no-cli-pager 2>/dev/null; then
  echo "  -> Role created"
else
  echo "  -> Role already exists, updating trust policy..."
  aws iam update-assume-role-policy \
    --role-name "${AUTH_ROLE_NAME}" \
    --policy-document "${AUTH_TRUST_POLICY}" \
    --no-cli-pager
fi

# AgentCore InvokeAgent 권한
AUTH_PERMISSIONS=$(cat <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AgentCoreInvoke",
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeAgent",
        "bedrock-agentcore:InvokeAgentRuntime"
      ],
      "Resource": "arn:aws:bedrock-agentcore:${AWS_REGION}:${ACCOUNT_ID}:runtime/*"
    }
  ]
}
POLICY
)

aws iam put-role-policy \
  --role-name "${AUTH_ROLE_NAME}" \
  --policy-name "AgentCoreInvokeAccess" \
  --policy-document "${AUTH_PERMISSIONS}" \
  --no-cli-pager
echo "  -> AgentCore InvokeAgent permission attached"

AUTH_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${AUTH_ROLE_NAME}"

# -------------------------------------------------------
# 3. Identity Pool에 역할 매핑
# -------------------------------------------------------
echo ""
echo "[3/3] Setting role mapping..."

aws cognito-identity set-identity-pool-roles \
  --identity-pool-id "${IDENTITY_POOL_ID}" \
  --roles authenticated="${AUTH_ROLE_ARN}" \
  --region "${AWS_REGION}" \
  --no-cli-pager
echo "  -> Role mapping set"

# -------------------------------------------------------
# 출력
# -------------------------------------------------------
echo ""
echo "=========================================="
echo " Identity Pool 설정 완료!"
echo "=========================================="
echo ""
echo "  Identity Pool ID:  ${IDENTITY_POOL_ID}"
echo "  Auth Role ARN:     ${AUTH_ROLE_ARN}"
echo "  User Pool ID:      ${USER_POOL_ID}"
echo "  App Client ID:     ${APP_CLIENT_ID}"
echo ""
echo "프론트엔드 .env에 추가:"
echo "  REACT_APP_USER_POOL_ID=${USER_POOL_ID}"
echo "  REACT_APP_APP_CLIENT_ID=${APP_CLIENT_ID}"
echo "  REACT_APP_IDENTITY_POOL_ID=${IDENTITY_POOL_ID}"
echo "  REACT_APP_REGION=${AWS_REGION}"
