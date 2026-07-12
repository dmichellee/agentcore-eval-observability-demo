#!/bin/bash
# ============================================================
# S3 버킷 + 기술 가이드 업로드
# S3 Vectors (벡터 저장소) 생성
# Bedrock Knowledge Base 생성 (S3_VECTORS 스토리지)
# ============================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

VECTOR_BUCKET_NAME="${PROJECT_PREFIX}-vectors-${ENV}"
VECTOR_INDEX_NAME="${PROJECT_PREFIX}-tech-index-${ENV}"
# Cohere embed-multilingual-v3 dimension = 1024
VECTOR_DIMENSION=1024

echo "=========================================="
echo " S3 + S3 Vectors + Knowledge Base 설정"
echo "=========================================="

# -------------------------------------------------------
# 1. S3 버킷 생성 (기술 가이드 원본 문서)
# -------------------------------------------------------
echo "[1/5] Creating S3 bucket: ${TECH_GUIDES_BUCKET}"
if aws s3api head-bucket --bucket "${TECH_GUIDES_BUCKET}" 2>/dev/null; then
  echo "  -> Bucket already exists"
else
  if [ "${AWS_REGION}" = "us-east-1" ]; then
    aws s3api create-bucket \
      --bucket "${TECH_GUIDES_BUCKET}" \
      --region "${AWS_REGION}" \
      --no-cli-pager
  else
    aws s3api create-bucket \
      --bucket "${TECH_GUIDES_BUCKET}" \
      --region "${AWS_REGION}" \
      --create-bucket-configuration LocationConstraint="${AWS_REGION}" \
      --no-cli-pager
  fi
  echo "  -> Bucket created"
fi

# -------------------------------------------------------
# 2. 기술 가이드 마크다운 문서 업로드
# -------------------------------------------------------
echo "[2/5] Uploading tech guide documents..."
TECH_DIR="${PROJECT_ROOT}/backend/tech_guides"
aws s3 sync "${TECH_DIR}" "s3://${TECH_GUIDES_BUCKET}/tech-guides/" \
  --delete \
  --no-cli-pager
echo "  -> Documents uploaded to s3://${TECH_GUIDES_BUCKET}/tech-guides/"

UPLOADED=$(aws s3 ls "s3://${TECH_GUIDES_BUCKET}/tech-guides/" --recursive | wc -l | tr -d ' ')
echo "  -> ${UPLOADED} files uploaded"

# -------------------------------------------------------
# 3. S3 Vectors: Vector Bucket + Vector Index 생성
# -------------------------------------------------------
echo "[3/5] Creating S3 Vector Bucket: ${VECTOR_BUCKET_NAME}"

VBUCKET_RESULT=$(aws s3vectors create-vector-bucket \
  --vector-bucket-name "${VECTOR_BUCKET_NAME}" \
  --region "${AWS_REGION}" \
  --no-cli-pager 2>&1) || true

if echo "${VBUCKET_RESULT}" | grep -q "already exists\|BucketAlreadyExists\|ConflictException"; then
  echo "  -> Vector Bucket already exists"
else
  echo "  -> Vector Bucket created"
fi

# Vector Bucket ARN 조회
VECTOR_BUCKET_ARN=$(aws s3vectors list-vector-buckets \
  --region "${AWS_REGION}" \
  --no-cli-pager \
  | python3 -c "
import sys, json
buckets = json.load(sys.stdin).get('vectorBuckets', [])
for b in buckets:
    if b['vectorBucketName'] == '${VECTOR_BUCKET_NAME}':
        print(b['vectorBucketArn'])
        break
" 2>/dev/null || echo "")

echo "  -> Vector Bucket ARN: ${VECTOR_BUCKET_ARN}"

echo "  Creating Vector Index: ${VECTOR_INDEX_NAME}"
INDEX_RESULT=$(aws s3vectors create-index \
  --vector-bucket-name "${VECTOR_BUCKET_NAME}" \
  --index-name "${VECTOR_INDEX_NAME}" \
  --data-type "float32" \
  --dimension "${VECTOR_DIMENSION}" \
  --distance-metric "cosine" \
  --metadata-configuration '{"nonFilterableMetadataKeys":["AMAZON_BEDROCK_TEXT","AMAZON_BEDROCK_METADATA"]}' \
  --region "${AWS_REGION}" \
  --no-cli-pager 2>&1) || true

if echo "${INDEX_RESULT}" | grep -q "already exists\|ConflictException"; then
  echo "  -> Vector Index already exists"
else
  echo "  -> Vector Index created"
fi

# Vector Index ARN 조회 (create 응답에서 먼저 시도, 없으면 get으로)
VECTOR_INDEX_ARN=$(echo "${INDEX_RESULT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['indexArn'])" 2>/dev/null || echo "")
if [ -z "${VECTOR_INDEX_ARN}" ]; then
  VECTOR_INDEX_ARN=$(aws s3vectors get-index \
    --vector-bucket-name "${VECTOR_BUCKET_NAME}" \
    --index-name "${VECTOR_INDEX_NAME}" \
    --region "${AWS_REGION}" \
    --no-cli-pager 2>/dev/null \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['index']['indexArn'])" 2>/dev/null || echo "")
fi

echo "  -> Vector Index ARN: ${VECTOR_INDEX_ARN}"

# -------------------------------------------------------
# 4. KB IAM 역할 + Knowledge Base 생성
# -------------------------------------------------------
echo "[4/5] Creating Bedrock Knowledge Base: ${KB_NAME}"

KB_ROLE_NAME="VroomDashKBRole-${ENV}"
KB_TRUST=$(cat <<'POLICY'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "bedrock.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}
POLICY
)

aws iam create-role \
  --role-name "${KB_ROLE_NAME}" \
  --assume-role-policy-document "${KB_TRUST}" \
  --no-cli-pager 2>/dev/null || true

KB_POLICY=$(cat <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::${TECH_GUIDES_BUCKET}",
        "arn:aws:s3:::${TECH_GUIDES_BUCKET}/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": "arn:aws:bedrock:${AWS_REGION}::foundation-model/${EMBEDDING_MODEL_ID}"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3vectors:QueryVectors",
        "s3vectors:PutVectors",
        "s3vectors:GetVectors",
        "s3vectors:DeleteVectors",
        "s3vectors:ListVectors"
      ],
      "Resource": "${VECTOR_INDEX_ARN:-*}"
    }
  ]
}
POLICY
)

aws iam put-role-policy \
  --role-name "${KB_ROLE_NAME}" \
  --policy-name "VroomDashKBAccess" \
  --policy-document "${KB_POLICY}" \
  --no-cli-pager

KB_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${KB_ROLE_NAME}"
echo "  -> KB role: ${KB_ROLE_ARN}"

echo "  -> Waiting for IAM role propagation (10s)..."
sleep 10

# Knowledge Base 생성 with S3_VECTORS storage
KB_RESULT=$(aws bedrock-agent create-knowledge-base \
  --name "${KB_NAME}" \
  --role-arn "${KB_ROLE_ARN}" \
  --knowledge-base-configuration '{
    "type": "VECTOR",
    "vectorKnowledgeBaseConfiguration": {
      "embeddingModelArn": "arn:aws:bedrock:'"${AWS_REGION}"'::foundation-model/'"${EMBEDDING_MODEL_ID}"'"
    }
  }' \
  --storage-configuration '{
    "type": "S3_VECTORS",
    "s3VectorsConfiguration": {
      "vectorBucketArn": "'"${VECTOR_BUCKET_ARN}"'",
      "indexArn": "'"${VECTOR_INDEX_ARN}"'"
    }
  }' \
  --region "${AWS_REGION}" \
  --no-cli-pager 2>&1) || true

KB_ID=$(echo "${KB_RESULT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['knowledgeBase']['knowledgeBaseId'])" 2>/dev/null || echo "")

if [ -z "${KB_ID}" ]; then
  echo "  -> KB creation error:"
  echo "${KB_RESULT}" | head -5
  echo ""
  echo "  KB_ID is empty. Check errors above."
  KB_ID="PENDING"
else
  echo "  -> Knowledge Base created: ${KB_ID}"
fi

# -------------------------------------------------------
# 5. Data Source 추가 + Ingestion
# -------------------------------------------------------
echo "[5/5] Adding data source & starting ingestion..."

if [ "${KB_ID}" != "PENDING" ]; then
  aws bedrock-agent create-data-source \
    --knowledge-base-id "${KB_ID}" \
    --name "${PROJECT_PREFIX}-tech-guides-source" \
    --data-source-configuration '{
      "type": "S3",
      "s3Configuration": {
        "bucketArn": "arn:aws:s3:::'"${TECH_GUIDES_BUCKET}"'",
        "inclusionPrefixes": ["tech-guides/"]
      }
    }' \
    --vector-ingestion-configuration '{
      "chunkingConfiguration": {
        "chunkingStrategy": "FIXED_SIZE",
        "fixedSizeChunkingConfiguration": {
          "maxTokens": 512,
          "overlapPercentage": 10
        }
      }
    }' \
    --region "${AWS_REGION}" \
    --no-cli-pager || true

  echo "  -> Data source added"

  # Ingestion 시작
  DS_ID=$(aws bedrock-agent list-data-sources \
    --knowledge-base-id "${KB_ID}" \
    --region "${AWS_REGION}" \
    --no-cli-pager \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['dataSourceSummaries'][0]['dataSourceId'])" 2>/dev/null || echo "")

  if [ -n "${DS_ID}" ]; then
    aws bedrock-agent start-ingestion-job \
      --knowledge-base-id "${KB_ID}" \
      --data-source-id "${DS_ID}" \
      --region "${AWS_REGION}" \
      --no-cli-pager || true
    echo "  -> Ingestion job started"
  fi
else
  echo "  -> Skipping (KB not created yet)"
fi

echo ""
echo "=========================================="
echo " S3 + S3 Vectors + KB 설정 완료!"
echo "=========================================="
echo "  S3 Data Bucket:   ${TECH_GUIDES_BUCKET}"
echo "  S3 Vector Bucket: ${VECTOR_BUCKET_NAME}"
echo "  Vector Index:     ${VECTOR_INDEX_NAME}"
echo "  KB Name:          ${KB_NAME}"
echo "  KB ID:            ${KB_ID}"
echo ""
echo "Set: KNOWLEDGE_BASE_ID=${KB_ID}"
