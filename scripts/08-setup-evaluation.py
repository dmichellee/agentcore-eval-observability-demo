#!/usr/bin/env python3
"""
Vroom&Dash AgentCore Evaluation 설정 스크립트

커스텀 evaluator 생성 + 온라인 평가 설정을 수행합니다.
boto3 bedrock-agentcore-control API를 사용합니다.

사전 조건:
  pip install boto3

사용법:
  python scripts/08-setup-evaluation.py
"""

import json
import os
import sys
import time
from pathlib import Path

import boto3

# ─── 설정 ───────────────────────────────────────────────────
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
ACCOUNT_ID = boto3.client("sts").get_caller_identity()["Account"]

from agentcore_ids import resolve_runtime_id, runtime_name  # noqa: E402

AGENT_RUNTIME_ID = resolve_runtime_id(AWS_REGION)
AGENT_RUNTIME_NAME = runtime_name()
QUALIFIER = "DEFAULT"

# CloudWatch 로그 설정 (AgentCore 런타임 기본 패턴)
LOG_GROUP_NAME = f"/aws/bedrock-agentcore/runtimes/{AGENT_RUNTIME_ID}-{QUALIFIER}"
SERVICE_NAME = f"{AGENT_RUNTIME_NAME}.{QUALIFIER}"

# 프로젝트 루트 기준 경로
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
EVAL_DIR = PROJECT_ROOT / "agentcore" / "eval"

ACCURACY_METRIC_PATH = EVAL_DIR / "accuracy-metric.json"
HELPFULNESS_METRIC_PATH = EVAL_DIR / "helpfulness-metric.json"

# 내장 evaluator 목록
BUILTIN_EVALUATORS = [
    "Builtin.GoalSuccessRate",
    "Builtin.Correctness",
    "Builtin.ToolSelectionAccuracy",
    "Builtin.ToolParameterAccuracy",
]

# 온라인 평가 설정
ONLINE_EVAL_CONFIG_NAME = "VroomDash_online_eval"
ONLINE_EVAL_DESCRIPTION = "VroomDash agent online evaluation with builtin and custom metrics"
SAMPLING_RATE = 100.0  # dev 환경: 100% 샘플링
SESSION_TIMEOUT_MINUTES = 60


def load_metric(path: Path) -> dict:
    """메트릭 JSON 파일을 로드합니다."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_existing_eval_role(iam_client) -> str | None:
    """기존 AgentCore 평가 역할을 찾습니다."""
    try:
        paginator = iam_client.get_paginator("list_roles")
        for page in paginator.paginate(PathPrefix="/service-role/"):
            for role in page["Roles"]:
                if role["RoleName"].startswith("AgentCoreEvalRole-"):
                    # 연결된 정책이 있는지 확인 (전파 완료된 역할)
                    attached = iam_client.list_attached_role_policies(RoleName=role["RoleName"])
                    if attached["AttachedPolicies"]:
                        return role["Arn"]
    except Exception:
        pass
    return None


def create_eval_execution_role(iam_client, config_name: str) -> str:
    """온라인 평가용 IAM 실행 역할을 생성합니다."""
    role_name = f"AgentCoreEvalRole-{config_name}"

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "TrustPolicyStatement",
                "Effect": "Allow",
                "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "aws:ResourceAccount": ACCOUNT_ID,
                        "aws:SourceAccount": ACCOUNT_ID,
                    },
                    "ArnLike": {
                        "aws:SourceArn": [
                            f"arn:aws:bedrock-agentcore:{AWS_REGION}:{ACCOUNT_ID}:evaluator/*",
                            f"arn:aws:bedrock-agentcore:{AWS_REGION}:{ACCOUNT_ID}:online-evaluation-config/*",
                        ]
                    },
                },
            }
        ],
    }

    # 역할이 이미 있으면 재사용
    try:
        resp = iam_client.get_role(RoleName=role_name)
        role_arn = resp["Role"]["Arn"]
        print(f"  기존 IAM 역할 재사용: {role_arn}")
        return role_arn
    except iam_client.exceptions.NoSuchEntityException:
        pass

    resp = iam_client.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description="AgentCore online evaluation execution role for VroomDash",
        Path="/service-role/",
    )
    role_arn = resp["Role"]["Arn"]

    # 평가 역할에 필요한 권한 (기존 AgentCore 평가 역할 패턴 준수)
    policy_name = f"{role_name}-policy"
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "CloudWatchLogReadStatement",
                "Effect": "Allow",
                "Action": [
                    "logs:DescribeLogGroups",
                    "logs:GetQueryResults",
                    "logs:StartQuery",
                ],
                "Resource": ["*"],
            },
            {
                "Sid": "CloudWatchLogWriteStatement",
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                "Resource": [
                    f"arn:aws:logs:{AWS_REGION}:{ACCOUNT_ID}:log-group:/aws/bedrock-agentcore/evaluations/*"
                ],
            },
            {
                "Sid": "CloudWatchIndexPolicyStatement",
                "Effect": "Allow",
                "Action": [
                    "logs:DescribeIndexPolicies",
                    "logs:PutIndexPolicy",
                ],
                "Resource": [
                    f"arn:aws:logs:{AWS_REGION}:{ACCOUNT_ID}:log-group:aws/spans",
                    f"arn:aws:logs:{AWS_REGION}:{ACCOUNT_ID}:log-group:aws/spans:*",
                ],
            },
            {
                "Sid": "BedrockInvokeStatement",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                "Resource": [
                    "arn:aws:bedrock:*::foundation-model/*",
                    f"arn:aws:bedrock:*:{ACCOUNT_ID}:inference-profile/*",
                ],
            },
        ],
    }

    # 관리형 정책으로 생성 (기존 패턴과 동일)
    try:
        policy_resp = iam_client.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy),
            Path="/service-role/",
            Description="AgentCore evaluation execution policy",
        )
        policy_arn = policy_resp["Policy"]["Arn"]
    except iam_client.exceptions.EntityAlreadyExistsException:
        policy_arn = f"arn:aws:iam::{ACCOUNT_ID}:policy/service-role/{policy_name}"

    iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)

    print(f"  IAM 역할 생성: {role_arn}")
    print("  IAM 역할 전파 대기 중 (15초)...")
    time.sleep(15)
    return role_arn


def main():
    print(f"[eval] Region: {AWS_REGION}")
    print(f"[eval] Account: {ACCOUNT_ID}")
    print(f"[eval] Agent Runtime ID: {AGENT_RUNTIME_ID}")
    print(f"[eval] Log Group: {LOG_GROUP_NAME}")
    print(f"[eval] Service Name: {SERVICE_NAME}")
    print()

    cp_client = boto3.client("bedrock-agentcore-control", region_name=AWS_REGION)
    iam_client = boto3.client("iam", region_name=AWS_REGION)

    # ─── 1. 내장 evaluator 확인 ─────────────────────────────
    print("[eval] 사용할 내장 evaluator 확인:")
    for ev_id in BUILTIN_EVALUATORS:
        try:
            cp_client.get_evaluator(evaluatorId=ev_id)
            print(f"  ✓ {ev_id}")
        except Exception as e:
            print(f"  ✗ {ev_id} — {e}")

    # ─── 2. 커스텀 evaluator 생성 ───────────────────────────
    print("\n[eval] 커스텀 evaluator 생성 중...")

    def find_existing_evaluator(name: str) -> str | None:
        """이름으로 기존 evaluator를 찾습니다."""
        resp = cp_client.list_evaluators()
        for e in resp.get("evaluators", []):
            if e.get("evaluatorName") == name:
                return e["evaluatorId"]
        return None

    # Accuracy evaluator
    accuracy_id = find_existing_evaluator("VroomDash_Accuracy")
    if accuracy_id:
        print(f"  ✓ Accuracy evaluator (기존): {accuracy_id}")
    else:
        accuracy_config = load_metric(ACCURACY_METRIC_PATH)
        accuracy_resp = cp_client.create_evaluator(
            evaluatorName="VroomDash_Accuracy",
            description="VroomDash domain accuracy evaluator",
            evaluatorConfig=accuracy_config,
            level="TRACE",
        )
        accuracy_id = accuracy_resp["evaluatorId"]
        print(f"  ✓ Accuracy evaluator (신규): {accuracy_id}")

    # Helpfulness evaluator
    helpfulness_id = find_existing_evaluator("VroomDash_Helpfulness")
    if helpfulness_id:
        print(f"  ✓ Helpfulness evaluator (기존): {helpfulness_id}")
    else:
        helpfulness_config = load_metric(HELPFULNESS_METRIC_PATH)
        helpfulness_resp = cp_client.create_evaluator(
            evaluatorName="VroomDash_Helpfulness",
            description="VroomDash domain helpfulness evaluator",
            evaluatorConfig=helpfulness_config,
            level="TRACE",
        )
        helpfulness_id = helpfulness_resp["evaluatorId"]
        print(f"  ✓ Helpfulness evaluator (신규): {helpfulness_id}")

    # ─── 3. IAM 실행 역할 생성/재사용 ──────────────────────────
    print("\n[eval] 평가 실행 IAM 역할 설정 중...")
    eval_role_arn = create_eval_execution_role(iam_client, ONLINE_EVAL_CONFIG_NAME)
    print(f"  Role ARN: {eval_role_arn}")

    # ─── 4. 온라인 평가 설정 생성 ───────────────────────────
    print("\n[eval] 온라인 평가 설정 생성 중...")

    all_evaluator_ids = BUILTIN_EVALUATORS + [accuracy_id, helpfulness_id]
    evaluator_list = [{"evaluatorId": eid} for eid in all_evaluator_ids]

    print(f"  Evaluator 목록 ({len(all_evaluator_ids)}개):")
    for eid in all_evaluator_ids:
        print(f"    - {eid}")

    online_resp = cp_client.create_online_evaluation_config(
        onlineEvaluationConfigName=ONLINE_EVAL_CONFIG_NAME,
        description=ONLINE_EVAL_DESCRIPTION,
        rule={
            "samplingConfig": {"samplingPercentage": SAMPLING_RATE},
            "sessionConfig": {"sessionTimeoutMinutes": SESSION_TIMEOUT_MINUTES},
        },
        dataSourceConfig={
            "cloudWatchLogs": {
                "logGroupNames": [LOG_GROUP_NAME],
                "serviceNames": [SERVICE_NAME],
            }
        },
        evaluators=evaluator_list,
        evaluationExecutionRoleArn=eval_role_arn,
        enableOnCreate=True,
    )

    config_id = online_resp["onlineEvaluationConfigId"]
    print(f"  ✓ 온라인 평가 설정 생성: {config_id}")

    # ─── 5. 결과 요약 ───────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Vroom&Dash AgentCore Evaluation 설정 완료")
    print("=" * 60)
    print(f"  Agent Runtime ID         : {AGENT_RUNTIME_ID}")
    print(f"  Accuracy Evaluator ID    : {accuracy_id}")
    print(f"  Helpfulness Evaluator ID : {helpfulness_id}")
    print(f"  Online Eval Config ID    : {config_id}")
    print(f"  Eval Execution Role      : {eval_role_arn}")
    print(f"  Sampling Rate            : {SAMPLING_RATE}%")
    print(f"  Total Evaluators         : {len(all_evaluator_ids)}")
    print("=" * 60)
    print()
    print("[eval] 다음 단계:")
    print("  1. 프론트엔드에서 에이전트와 대화하여 평가 데이터 생성")
    print("  2. CloudWatch GenAI Observability 대시보드에서 평가 스코어 확인")
    print("  3. python scripts/08-run-evaluation.py 로 온디맨드 평가 실행")


if __name__ == "__main__":
    main()
