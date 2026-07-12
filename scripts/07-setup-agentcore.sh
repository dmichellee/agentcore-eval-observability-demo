#!/bin/bash
# ============================================================
# AgentCore 리소스 설정
# Memory, Gateway 설정 + Runtime 배포 (agentcore CLI)
# ============================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================="
echo " AgentCore 리소스 설정"
echo " Region: ${AWS_REGION}, Env: ${ENV}"
echo "=========================================="

# -------------------------------------------------------
# 0. agentcore CLI 설치 확인
# -------------------------------------------------------
if ! command -v agentcore &> /dev/null; then
  echo "Installing agentcore CLI..."
  npm install -g @aws/agentcore
fi
echo "  agentcore CLI: $(agentcore --version)"

# -------------------------------------------------------
# 1. agentcore 프로젝트 디렉토리로 이동
# -------------------------------------------------------
cd "${PROJECT_ROOT}"
echo "[1/4] Working directory: ${PROJECT_ROOT}"

# 배포 대상(계정/리전)은 저장소에 두지 않고 현재 AWS 자격 증명으로 만든다
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
mkdir -p agentcore
cat > agentcore/aws-targets.json <<EOF
[
  {
    "name": "dev",
    "account": "${ACCOUNT_ID}",
    "region": "${AWS_REGION}"
  }
]
EOF
echo "  -> agentcore/aws-targets.json: ${ACCOUNT_ID} / ${AWS_REGION}"

# agentcore.json은 템플릿에서 계정/리전/환경 값을 채워 만든다 (생성 파일은 git에 올리지 않음)
python3 - "${ACCOUNT_ID}" "${AWS_REGION}" "${ENV}" <<'PY'
import sys
account, region, env = sys.argv[1:4]
src = open("agentcore/agentcore.template.json", encoding="utf-8").read()
out = src.replace("{{AWS_ACCOUNT_ID}}", account).replace("{{AWS_REGION}}", region).replace("{{ENV}}", env)
assert "{{" not in out, "unfilled placeholder in agentcore.template.json"
open("agentcore/agentcore.json", "w", encoding="utf-8").write(out)
PY
echo "  -> agentcore/agentcore.json generated from agentcore.template.json"

# CDK 앱 의존성 (처음 받은 저장소에는 node_modules가 없음)
if [ ! -d agentcore/cdk/node_modules ]; then
  echo "  -> Installing agentcore/cdk dependencies (npm ci)..."
  (cd agentcore/cdk && npm ci --no-audit --no-fund)
fi

# -------------------------------------------------------
# 2. 배포 (non-interactive 모드: -y 플래그)
# -------------------------------------------------------
echo "[2/4] Deploying AgentCore resources (Runtime + Memory + Gateway)..."
echo "  This runs CDK under the hood. May take a few minutes..."
agentcore deploy --target dev -y -v 2>&1

echo "  -> Deployment complete"

# -------------------------------------------------------
# 3. 상태 확인
# -------------------------------------------------------
echo "[3/4] Checking AgentCore status..."
agentcore status --json 2>/dev/null || agentcore status 2>&1 || true

# -------------------------------------------------------
# 4. 배포 후 테스트 안내
# -------------------------------------------------------
echo ""
echo "[4/4] Deployment finished!"
echo ""
echo "=========================================="
echo " AgentCore 설정 완료!"
echo "=========================================="
echo ""
echo "테스트:"
echo "  cd agentcore"
echo "  agentcore invoke '주문번호 ORD-001 조회해줘' --stream"
echo ""
echo "로컬 개발:"
echo "  agentcore dev"
echo ""
echo "로그:"
echo "  agentcore logs"
echo ""
echo "트레이스:"
echo "  agentcore traces list --limit 10"
