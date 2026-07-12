#!/usr/bin/env python3
"""
Vroom&Dash On-demand 평가 스크립트

골든 테스트 셋 시나리오 확인 또는 특정 세션에 대해 evaluator를 실행합니다.
bedrock_agentcore.evaluation.EvaluationClient를 사용합니다.

사전 조건:
  pip install bedrock-agentcore

사용법:
  # 특정 세션 평가 (세션 ID 직접 지정)
  python scripts/08-run-evaluation.py --session-id <SESSION_ID>

  # 골든 테스트 셋 시나리오 목록 보기
  python scripts/08-run-evaluation.py --list-scenarios

  # 특정 evaluator만 실행
  python scripts/08-run-evaluation.py --session-id <SESSION_ID> --evaluators Builtin.Correctness Builtin.Helpfulness

  # 커스텀 evaluator 포함 실행
  python scripts/08-run-evaluation.py --session-id <SESSION_ID> --custom-evaluator-ids <ID1> <ID2>
"""

import argparse
import json
import os
import sys
from datetime import timedelta
from pathlib import Path

# ─── 설정 ───────────────────────────────────────────────────
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from agentcore_ids import resolve_runtime_id  # noqa: E402

AGENT_RUNTIME_ID = resolve_runtime_id(AWS_REGION)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
GOLDEN_TEST_SET_PATH = PROJECT_ROOT / "agentcore" / "eval" / "golden-test-set.json"

# 기본 evaluator 목록
DEFAULT_EVALUATORS = [
    "Builtin.GoalSuccessRate",
    "Builtin.Correctness",
    "Builtin.ToolSelectionAccuracy",
    "Builtin.ToolParameterAccuracy",
]


def load_golden_test_set() -> dict:
    """골든 테스트 셋을 로드합니다."""
    with open(GOLDEN_TEST_SET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def list_scenarios():
    """골든 테스트 셋의 시나리오 목록을 출력합니다."""
    test_set = load_golden_test_set()
    print(f"골든 테스트 셋: {len(test_set['scenarios'])}개 시나리오")
    print(f"버전: {test_set['version']}")
    print()

    categories = {}
    for scenario in test_set["scenarios"]:
        cat = scenario["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(scenario)

    for cat, scenarios in categories.items():
        print(f"[{cat}] ({len(scenarios)}개)")
        for s in scenarios:
            tools = ", ".join(s["expected_trajectory"]) if s["expected_trajectory"] else "(없음)"
            turns = len(s["turns"])
            print(f"  {s['scenario_id']}: {s['turns'][0]['input'][:50]}...")
            print(f"    예상 도구: {tools} | 턴 수: {turns}")
        print()


def run_session_evaluation(eval_client, session_id: str, evaluator_ids: list):
    """특정 세션에 대해 평가를 실행합니다."""
    print(f"\n[eval] 세션 평가 실행: {session_id}")
    print(f"[eval] Agent Runtime ID: {AGENT_RUNTIME_ID}")
    print(f"[eval] Evaluators ({len(evaluator_ids)}개):")
    for eid in evaluator_ids:
        print(f"  - {eid}")
    print()

    results = eval_client.run(
        evaluator_ids=evaluator_ids,
        session_id=session_id,
        agent_id=AGENT_RUNTIME_ID,
        look_back_time=timedelta(hours=24),
    )

    print("=" * 60)
    print("  평가 결과")
    print("=" * 60)

    if not results:
        print("  (결과 없음 — 세션에 해당하는 트레이스를 찾을 수 없습니다)")
        return results

    for result in results:
        evaluator_name = result.get("evaluatorName", result.get("evaluatorId", "N/A"))
        value = result.get("value", "N/A")
        label = result.get("label", "N/A")
        explanation = result.get("explanation", "N/A")

        print(f"\n  Metric     : {evaluator_name}")
        print(f"  Score      : {label} ({value})")
        if explanation and len(str(explanation)) > 200:
            print(f"  Explanation: {str(explanation)[:200]}...")
        else:
            print(f"  Explanation: {explanation}")
        print("  " + "-" * 56)

    print()
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Vroom&Dash On-demand 평가 실행"
    )
    parser.add_argument(
        "--session-id",
        help="평가할 세션 ID",
    )
    parser.add_argument(
        "--evaluators",
        nargs="+",
        default=None,
        help="실행할 evaluator ID 목록 (미지정 시 기본 목록 사용)",
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="골든 테스트 셋 시나리오 목록 출력",
    )
    parser.add_argument(
        "--custom-evaluator-ids",
        nargs="+",
        default=[],
        help="커스텀 evaluator ID (08-setup-evaluation.py에서 생성된 ID)",
    )

    args = parser.parse_args()

    # 시나리오 목록 모드
    if args.list_scenarios:
        list_scenarios()
        return

    # 세션 평가 모드
    if not args.session_id:
        print("ERROR: --session-id 또는 --list-scenarios 옵션이 필요합니다.")
        parser.print_help()
        sys.exit(1)

    # SDK 임포트
    try:
        from bedrock_agentcore.evaluation import EvaluationClient
    except ImportError:
        print("ERROR: bedrock-agentcore 패키지가 필요합니다.")
        print("  pip install bedrock-agentcore")
        sys.exit(1)

    print(f"[eval] Region: {AWS_REGION}")
    print(f"[eval] Agent Runtime ID: {AGENT_RUNTIME_ID}")

    eval_client = EvaluationClient(region_name=AWS_REGION)

    evaluator_ids = args.evaluators or DEFAULT_EVALUATORS
    evaluator_ids = evaluator_ids + args.custom_evaluator_ids

    run_session_evaluation(eval_client, args.session_id, evaluator_ids)


if __name__ == "__main__":
    main()
