#!/bin/bash
# ============================================================
# Vroom&Dash 전체 인프라 배포 (마스터 스크립트)
#
# 배포 체크리스트 (REQUIREMENTS.md 7.11.4) 순서대로 실행:
#  1. IAM 역할 생성
#  2. DynamoDB 테이블 생성
#  3. DynamoDB 목업 데이터 적재
#  4. S3 버킷 + 기술 가이드 업로드 + Knowledge Base 생성
#  5. Lambda 함수 배포
#  6. Cognito User Pool 설정
#  7. AgentCore 리소스 설정 (Memory, Gateway, Runtime, Eval)
#
# 사용법:
#   chmod +x scripts/deploy-all.sh
#   ./scripts/deploy-all.sh
# ============================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "╔══════════════════════════════════════════╗"
echo "║  Vroom&Dash 전체 인프라 배포             ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Step 1: IAM
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Step 1/7: IAM 역할 생성"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bash "${SCRIPT_DIR}/03-setup-iam.sh"
echo ""

# Step 2: DynamoDB 테이블
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Step 2/7: DynamoDB 테이블 생성"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bash "${SCRIPT_DIR}/01-setup-dynamodb.sh"
echo ""

# Step 3: 데이터 시딩
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Step 3/7: DynamoDB 목업 데이터 적재"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 "${SCRIPT_DIR}/02-seed-data.py"
echo ""

# Step 4: S3 + Knowledge Base
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Step 4/7: S3 + Bedrock Knowledge Base"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bash "${SCRIPT_DIR}/04-setup-s3-kb.sh"
echo ""

# Step 5: Lambda
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Step 5/7: Lambda 함수 배포"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bash "${SCRIPT_DIR}/05-deploy-lambda.sh"
echo ""

# Step 6: Cognito
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Step 6/7: Cognito User Pool"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bash "${SCRIPT_DIR}/06-setup-cognito.sh"
echo ""

# Step 7: AgentCore
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Step 7/7: AgentCore 리소스 (Memory, Gateway, Runtime, Eval)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bash "${SCRIPT_DIR}/07-setup-agentcore.sh"
echo ""

# Frontend settings (frontend/.env.local, not committed)
bash "${SCRIPT_DIR}/06b-setup-identity-pool.sh"
bash "${SCRIPT_DIR}/10-write-frontend-env.sh"
echo ""

echo "╔══════════════════════════════════════════╗"
echo "║  전체 배포 완료!                         ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "테스트:"
echo "  agentcore invoke '주문번호 ORD-001 조회해줘' --stream"
echo ""
echo "프론트엔드:"
echo "  cd frontend && npm start"
