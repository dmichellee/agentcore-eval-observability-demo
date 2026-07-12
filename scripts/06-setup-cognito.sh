#!/bin/bash
# ============================================================
# Cognito User Pool + App Client 생성
# AgentCore Identity의 OAuth 인증 소스
# ============================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

echo "=========================================="
echo " Cognito User Pool 설정"
echo "=========================================="

# -------------------------------------------------------
# 1. User Pool 생성
# -------------------------------------------------------
echo "[1/3] Creating User Pool: ${COGNITO_USER_POOL_NAME}"

UP_RESULT=$(aws cognito-idp create-user-pool \
  --pool-name "${COGNITO_USER_POOL_NAME}" \
  --auto-verified-attributes email \
  --username-attributes email \
  --policies '{
    "PasswordPolicy": {
      "MinimumLength": 8,
      "RequireUppercase": true,
      "RequireLowercase": true,
      "RequireNumbers": true,
      "RequireSymbols": false
    }
  }' \
  --schema '[
    {"Name": "email", "Required": true, "Mutable": true},
    {"Name": "name",  "Required": true, "Mutable": true}
  ]' \
  --region "${AWS_REGION}" \
  --no-cli-pager 2>&1) || true

USER_POOL_ID=$(echo "${UP_RESULT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['UserPool']['Id'])" 2>/dev/null || echo "")

if [ -z "${USER_POOL_ID}" ]; then
  # 이미 존재하는 경우 조회
  USER_POOL_ID=$(aws cognito-idp list-user-pools --max-results 50 --region "${AWS_REGION}" --no-cli-pager \
    | python3 -c "
import sys, json
pools = json.load(sys.stdin)['UserPools']
for p in pools:
    if p['Name'] == '${COGNITO_USER_POOL_NAME}':
        print(p['Id'])
        break
" 2>/dev/null || echo "NOT_FOUND")
  echo "  -> Existing pool: ${USER_POOL_ID}"
else
  echo "  -> Pool created: ${USER_POOL_ID}"
fi

# -------------------------------------------------------
# 2. App Client 생성 (프론트엔드용)
# -------------------------------------------------------
echo "[2/3] Creating App Client..."

CLIENT_RESULT=$(aws cognito-idp create-user-pool-client \
  --user-pool-id "${USER_POOL_ID}" \
  --client-name "${PROJECT_PREFIX}-web-client-${ENV}" \
  --no-generate-secret \
  --explicit-auth-flows "ALLOW_USER_SRP_AUTH" "ALLOW_REFRESH_TOKEN_AUTH" \
  --supported-identity-providers "COGNITO" \
  --allowed-o-auth-flows "code" "implicit" \
  --allowed-o-auth-scopes "openid" "email" "profile" \
  --allowed-o-auth-flows-user-pool-client true \
  --callback-urls '["http://localhost:3000/callback","https://vroomdash.example.com/callback"]' \
  --logout-urls '["http://localhost:3000","https://vroomdash.example.com"]' \
  --region "${AWS_REGION}" \
  --no-cli-pager 2>&1) || true

CLIENT_ID=$(echo "${CLIENT_RESULT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['UserPoolClient']['ClientId'])" 2>/dev/null || echo "EXISTING")
echo "  -> App Client ID: ${CLIENT_ID}"

# -------------------------------------------------------
# 3. 도메인 설정 (Hosted UI용)
# -------------------------------------------------------
echo "[3/3] Setting up domain..."
DOMAIN_PREFIX="${PROJECT_PREFIX}-${ENV}"
aws cognito-idp create-user-pool-domain \
  --domain "${DOMAIN_PREFIX}" \
  --user-pool-id "${USER_POOL_ID}" \
  --region "${AWS_REGION}" \
  --no-cli-pager 2>/dev/null \
  && echo "  -> Domain created: ${DOMAIN_PREFIX}" \
  || echo "  -> Domain already exists"

# -------------------------------------------------------
# 4. 데모용 테스트 사용자 (비밀번호는 랜덤 생성 후 Secrets Manager에 보관)
# -------------------------------------------------------
echo ""
echo "Creating demo test user..."
DEMO_USERNAME="demo@vroomdash.example.com"
DEMO_SECRET_NAME="${PROJECT_PREFIX}/demo-user-${ENV}"

# 기존 secret이 있으면 그 비밀번호를 재사용 (재실행해도 비밀번호가 바뀌지 않음)
DEMO_PASSWORD=$(aws secretsmanager get-secret-value --secret-id "${DEMO_SECRET_NAME}" \
  --query SecretString --output text --region "${AWS_REGION}" --no-cli-pager 2>/dev/null \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['password'])" 2>/dev/null || echo "")

if [ -z "${DEMO_PASSWORD}" ]; then
  # User Pool 정책(대문자, 소문자, 숫자, 8자 이상)을 만족하는 20자 랜덤 값
  DEMO_PASSWORD=$(aws secretsmanager get-random-password --password-length 20 \
    --exclude-punctuation --require-each-included-type \
    --query RandomPassword --output text --region "${AWS_REGION}" --no-cli-pager)
  SECRET_JSON=$(python3 -c "import json,sys; print(json.dumps({'username': sys.argv[1], 'password': sys.argv[2]}))" \
    "${DEMO_USERNAME}" "${DEMO_PASSWORD}")
  aws secretsmanager create-secret --name "${DEMO_SECRET_NAME}" \
    --description "Vroom&Dash demo user (${ENV})" --secret-string "${SECRET_JSON}" \
    --region "${AWS_REGION}" --no-cli-pager >/dev/null
  echo "  -> Demo password generated and stored in Secrets Manager: ${DEMO_SECRET_NAME}"
else
  echo "  -> Reusing demo password from Secrets Manager: ${DEMO_SECRET_NAME}"
fi

aws cognito-idp admin-create-user \
  --user-pool-id "${USER_POOL_ID}" \
  --username "${DEMO_USERNAME}" \
  --user-attributes \
    Name=email,Value="${DEMO_USERNAME}" \
    Name=name,Value="데모 사용자" \
    Name=email_verified,Value=true \
  --message-action SUPPRESS \
  --region "${AWS_REGION}" \
  --no-cli-pager >/dev/null 2>&1 \
  && echo "  -> Demo user created: ${DEMO_USERNAME}" \
  || echo "  -> Demo user already exists: ${DEMO_USERNAME}"

# 영구 비밀번호로 설정 (첫 로그인 비밀번호 변경 단계 없음). 재실행 시 secret 값으로 다시 맞춤
aws cognito-idp admin-set-user-password \
  --user-pool-id "${USER_POOL_ID}" \
  --username "${DEMO_USERNAME}" \
  --password "${DEMO_PASSWORD}" \
  --permanent \
  --region "${AWS_REGION}" \
  --no-cli-pager
echo "  -> Password: aws secretsmanager get-secret-value --secret-id ${DEMO_SECRET_NAME} --query SecretString --output text"

echo ""
echo "Cognito setup complete!"
echo "  User Pool ID:   ${USER_POOL_ID}"
echo "  App Client ID:  ${CLIENT_ID}"
echo "  Domain:         ${DOMAIN_PREFIX}"
echo ""
echo "Set these in config:"
echo "  COGNITO_USER_POOL_ID=${USER_POOL_ID}"
echo "  COGNITO_APP_CLIENT_ID=${CLIENT_ID}"
