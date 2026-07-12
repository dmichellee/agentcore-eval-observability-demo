#!/bin/bash
# ============================================================
# Cross-Region Log Replicator - Configuration
# ============================================================

# --- Source (where logs originate) ---
SOURCE_REGION="us-east-1"
# Runtime ID: set AGENT_RUNTIME_ID, or it is looked up by name (VroomDash_VroomDash)
AGENT_RUNTIME_ID="${AGENT_RUNTIME_ID:-$(aws bedrock-agentcore-control list-agent-runtimes --region "${SOURCE_REGION}" \
  --query "agentRuntimes[?agentRuntimeName=='${AGENT_RUNTIME_NAME:-VroomDash_VroomDash}'].agentRuntimeId | [0]" --output text 2>/dev/null)}"
SOURCE_LOG_GROUP="/aws/bedrock-agentcore/runtimes/${AGENT_RUNTIME_ID}-DEFAULT"
SOURCE_LOG_STREAM_PREFIX="otel-rt-logs"

# --- Destination (where logs are replicated to) ---
DEST_REGION="ap-northeast-1"
DEST_LOG_GROUP="/test/agentcore-runtime/otel/vroomdash"
DEST_LOG_STREAM="otel-rt-logs"

# --- Resource naming ---
LAMBDA_FUNCTION_NAME="log-replicator-vroomdash-otel"
IAM_ROLE_NAME="log-replicator-vroomdash-otel-role"
SUBSCRIPTION_FILTER_NAME="otel-rt-logs-replicator"

# --- Source stream filter (comma-separated, empty = allow all) ---
ALLOWED_SOURCE_STREAMS="otel-rt-logs"

# --- Lambda settings ---
LAMBDA_RUNTIME="python3.12"
LAMBDA_TIMEOUT=60
LAMBDA_MEMORY=128

# --- Derived values (do not edit) ---
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
IAM_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${IAM_ROLE_NAME}"
