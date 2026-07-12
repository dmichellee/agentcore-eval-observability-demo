#!/bin/bash
# ============================================================
# Cross-Region Log Replicator - Configuration (aws/spans)
# ============================================================

# --- Source (where logs originate) ---
SOURCE_REGION="us-east-1"
SOURCE_LOG_GROUP="aws/spans"
SOURCE_LOG_STREAM_PREFIX="default"

# --- Destination (where logs are replicated to) ---
DEST_REGION="ap-northeast-1"
DEST_LOG_GROUP="aws/spans"
DEST_LOG_STREAM="default"

# --- Resource naming ---
LAMBDA_FUNCTION_NAME="log-replicator-spans"
IAM_ROLE_NAME="log-replicator-spans-role"
SUBSCRIPTION_FILTER_NAME="spans-replicator"

# --- Lambda settings ---
LAMBDA_RUNTIME="python3.12"
LAMBDA_TIMEOUT=60
LAMBDA_MEMORY=128

# --- Derived values (do not edit) ---
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
IAM_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${IAM_ROLE_NAME}"
