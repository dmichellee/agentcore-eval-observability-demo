#!/bin/bash
# ============================================================
# Vroom&Dash On-demand 평가 실행
# agentcore CLI 기반
#
# 사용법:
#   bash scripts/08-run-evaluation.sh                      # 최근 1일 전체 평가
#   bash scripts/08-run-evaluation.sh -s <SESSION_ID>      # 특정 세션 평가
#   bash scripts/08-run-evaluation.sh --scenarios           # 골든 테스트 시나리오 목록
#   bash scripts/08-run-evaluation.sh --days 7             # 최근 7일 평가
#   bash scripts/08-run-evaluation.sh --history            # 평가 이력 확인
# ============================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
GOLDEN_TEST_SET="${PROJECT_ROOT}/agentcore/eval/golden-test-set.json"

# --- 설정 ---
RUNTIME_NAME="VroomDash"
DEFAULT_DAYS=1
DEFAULT_EVALUATORS=(
  "Builtin.GoalSuccessRate"
  "Builtin.Correctness"
  "Builtin.ToolSelectionAccuracy"
  "Builtin.ToolParameterAccuracy"
  "Accuracy"
  "Helpfulness"
)

# -------------------------------------------------------
# 인자 파싱
# -------------------------------------------------------
SESSION_ID=""
DAYS="${DEFAULT_DAYS}"
SHOW_SCENARIOS=false
SHOW_HISTORY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    -s|--session-id)  SESSION_ID="$2"; shift 2 ;;
    --days)           DAYS="$2"; shift 2 ;;
    --scenarios)      SHOW_SCENARIOS=true; shift ;;
    --history)        SHOW_HISTORY=true; shift ;;
    -h|--help)
      echo "사용법:"
      echo "  bash scripts/08-run-evaluation.sh                    # 최근 ${DEFAULT_DAYS}일 전체 평가"
      echo "  bash scripts/08-run-evaluation.sh -s <SESSION_ID>    # 특정 세션 평가"
      echo "  bash scripts/08-run-evaluation.sh --days 7           # lookback 기간 변경"
      echo "  bash scripts/08-run-evaluation.sh --scenarios        # 골든 테스트 시나리오 목록"
      echo "  bash scripts/08-run-evaluation.sh --history          # 평가 이력 확인"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

cd "${PROJECT_ROOT}"

# -------------------------------------------------------
# 골든 테스트 시나리오 목록
# -------------------------------------------------------
if $SHOW_SCENARIOS; then
  python3 -c "
import json
with open('${GOLDEN_TEST_SET}') as f:
    data = json.load(f)
print(f\"골든 테스트 셋: {len(data['scenarios'])}개 시나리오 (v{data['version']})\")
print()
cats = {}
for s in data['scenarios']:
    cats.setdefault(s['category'], []).append(s)
for cat, scenarios in cats.items():
    print(f'[{cat}] ({len(scenarios)}개)')
    for s in scenarios:
        tools = ', '.join(s['expected_trajectory']) or '(없음)'
        print(f\"  {s['scenario_id']}: {s['turns'][0]['input'][:50]}...\")
        print(f'    예상 도구: {tools} | 턴 수: {len(s[\"turns\"])}')
    print()
"
  exit 0
fi

# -------------------------------------------------------
# 평가 이력 확인
# -------------------------------------------------------
if $SHOW_HISTORY; then
  agentcore evals history --agent "${RUNTIME_NAME}"
  exit 0
fi

# -------------------------------------------------------
# 온디맨드 평가 실행
# -------------------------------------------------------
echo "=========================================="
echo " Vroom&Dash On-demand 평가"
echo " Runtime: ${RUNTIME_NAME}, Days: ${DAYS}"
echo "=========================================="

EVAL_ARGS=(
  --runtime "${RUNTIME_NAME}"
  --evaluator "${DEFAULT_EVALUATORS[@]}"
  --days "${DAYS}"
)

if [[ -n "${SESSION_ID}" ]]; then
  echo " Session: ${SESSION_ID}"
  EVAL_ARGS+=(--session-id "${SESSION_ID}")
  echo "=========================================="
fi

echo ""

agentcore run eval "${EVAL_ARGS[@]}"
