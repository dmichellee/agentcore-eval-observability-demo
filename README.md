# Amazon Bedrock AgentCore Evaluations and Observability Demo: Vroom&Dash Support Agent

This repository shows how to evaluate an AI agent with **Amazon Bedrock AgentCore Evaluations**.
The agent under test is Vroom&Dash, a Korean-language customer support agent for a fictional toy car
shop. It runs on AgentCore Runtime with Memory and Gateway, and every conversation is scored by
built-in and custom (LLM-as-a-Judge) evaluators, online and on demand.

All shop data (customers, orders, products, guides) is fictional mock data.

---

## What the demo covers

| Topic | What you will see |
|---|---|
| Built-in evaluators | Goal success, correctness, tool selection and tool parameter accuracy |
| Custom evaluators | Two LLM-as-a-Judge metrics (accuracy, helpfulness) on a 1 to 5 scale |
| Evaluation levels | SESSION, TRACE and TOOL_CALL scoring of the same conversation |
| Online evaluation | 100% sampling of live sessions on the deployed runtime |
| On-demand evaluation | Re-scoring a session, a time window or the golden test scenarios |
| Golden test set | 18 scenarios across order lookup, recommendations, tech support, returns and edge cases |
| Cross-region evaluation | Replicating runtime logs and spans to another Region and evaluating there |
| Reading results | CloudWatch GenAI Observability dashboard and evaluation history |

---

## Architecture

```
Frontend (React chat) --Cognito--> AgentCore Runtime (Strands Agent, Claude Haiku 4.5)
                                       |-- AgentCore Memory (semantic, user preference, summary)
                                       |-- AgentCore Gateway --> Lambda tools
                                       |        |-- OrderTools     -> DynamoDB
                                       |        |-- ProductTools   -> DynamoDB
                                       |        `-- TechGuideTools -> Bedrock Knowledge Base (S3 Vectors)
                                       `-- Traces --> CloudWatch (GenAI Observability)
                                                         |
                                       AgentCore Evaluations (online + on demand)
                                         built-in evaluators + custom LLM-as-a-Judge
```

---

## Project layout for evaluation

| Path | What it is |
|---|---|
| `agentcore/agentcore.template.json` | AgentCore project spec: Runtime, Memory, Gateway (3 Lambda targets), the two custom evaluators and the online evaluation config |
| `agentcore/eval/golden-test-set.json` | Golden test set (18 scenarios with expected tool trajectory and assertions) |
| `agentcore/eval/accuracy-metric.json`, `helpfulness-metric.json` | Custom LLM-as-a-Judge evaluator definitions |
| `agentcore/tool-schemas/` | Gateway tool schemas |
| `agentcore/cdk/` | CDK app used by `agentcore deploy` |
| `scripts/08-*`, `scripts/09-*` | Evaluation setup and on-demand runs |

## Evaluators

| Evaluator | Level | Type | What it checks |
|---|---|---|---|
| `Builtin.GoalSuccessRate` | SESSION | Built-in | Did the conversation achieve the customer's goal |
| `Builtin.Correctness` | TRACE | Built-in | Is the answer factually correct |
| `Builtin.ToolSelectionAccuracy` | TOOL_CALL | Built-in | Did the agent call the right tool |
| `Builtin.ToolParameterAccuracy` | TOOL_CALL | Built-in | Were the tool arguments right |
| `VroomDash_Accuracy` | TRACE | Custom (LLM-as-a-Judge) | Consistency with tool results: hallucination, wrong numbers, Korean accuracy |
| `VroomDash_Helpfulness` | TRACE | Custom (LLM-as-a-Judge) | Did it resolve the request: completeness, next steps, reasons for recommendations, tone |

Custom evaluators use `us.anthropic.claude-haiku-4-5-20251001-v1:0` as the judge and score on an
integer 1 to 5 scale, which AgentCore normalizes to 0.0 to 1.0. The evaluator name `Accuracy` in the
project config becomes `VroomDash_Accuracy` after deployment (the project name is added as a prefix).

### Golden test set (18 scenarios)

| Category | Scenarios | Main tools |
|---|:---:|---|
| Order lookup | 4 | `lookup_order`, `track_delivery` |
| Product recommendation | 4 | `search_products`, `recommend_products`, `get_product_detail` |
| Tech support | 3 | `get_tech_guide` |
| Returns and exchanges | 3 | `request_return`, `lookup_order` |
| Multi-turn | 1 | `recommend_products` then `get_product_detail` |
| Edge cases | 3 | Invalid order number, out-of-scope question, informal Korean |

---

## Quick start

### Prerequisites

- An AWS account with access to Amazon Bedrock (Claude Haiku 4.5, Cohere Embed Multilingual v3) and
  AgentCore in `us-east-1`
- AWS CLI v2 configured for that account, Python 3.12+, Node.js 20+
- AgentCore CLI: `npm install -g @aws/agentcore`

### 1. Deploy

```bash
bash scripts/deploy-all.sh
```

This creates IAM roles, DynamoDB tables with mock data, the S3 Vectors knowledge base, Lambda tools,
Cognito (user pool, identity pool and a demo user), and the AgentCore Runtime, Memory, Gateway and
evaluation resources. The individual steps are in `scripts/01-*` to `scripts/10-*`.

`scripts/07-setup-agentcore.sh` generates the account-specific files from your current AWS credentials,
so nothing account-specific is stored in the repository:

- `agentcore/aws-targets.json`: target account and Region
- `agentcore/agentcore.json`: rendered from `agentcore/agentcore.template.json` (account, Region and
  environment filled into the Gateway's Lambda target ARNs)

### 2. Create some conversations

```bash
agentcore invoke '주문번호 ORD-001 조회해줘' --stream     # "Look up order ORD-001"
```

or use the chat UI:

```bash
cd frontend && npm install && npm start                  # http://localhost:3000
```

Try a few questions from different categories (order status, a product recommendation, a pairing
problem, a return request) so every evaluator has something to score.

### 3. Set up and run evaluations

```bash
python scripts/08-setup-evaluation.py                     # custom evaluators + online evaluation
bash scripts/08-run-evaluation.sh                         # on demand: all sessions from the last day
bash scripts/08-run-evaluation.sh -s <SESSION_ID>         # one session
bash scripts/08-run-evaluation.sh --days 7                # last 7 days
bash scripts/08-run-evaluation.sh --scenarios             # list the golden test scenarios
bash scripts/08-run-evaluation.sh --history               # past evaluation runs
python scripts/09-run-evaluation.py --session-id <SESSION_ID>   # SDK version, pick evaluators
```

The scripts find the runtime by name (`VroomDash_VroomDash`). Set `AGENT_RUNTIME_ID` to point them at
a specific runtime.

### 4. Read the results

- **CloudWatch console, GenAI Observability**: per-session traces with evaluator scores
- **`--history`**: past on-demand runs and their scores

Example baseline from the first run:

| Category | Correctness | GoalSuccess | ToolSelection | Accuracy | Helpfulness |
|---|:---:|:---:|:---:|:---:|:---:|
| Order lookup | 1.0 | 1.0 | 1.0 | 1.0 | 0.75 |
| Product recommendation | 1.0 | 1.0 | 1.0 | 1.0 | 0.75 |
| Tech support | 0.0 | 1.0 | 1.0 | 0.5 | 0.25 |
| Returns | 1.0 | 1.0 | 1.0 | 1.0 | 0.75 |

How to read it: tool selection is perfect everywhere, so the agent picks the right tool. Tech support
still fails correctness and helpfulness, which points at the answer step rather than retrieval: the
agent does not use the knowledge base results enough in its reply. The next iteration is a system
prompt change, followed by the same evaluation to confirm the improvement.

---

## Cross-region evaluation

`cross-region/` shows how to evaluate an agent from a different Region than the one it runs in:

- `log-replication/`: a Lambda subscription that copies runtime logs (`config.sh`) and spans
  (`config-spans.sh`) from the source Region to the destination Region (`deploy.sh`, `cleanup.sh`)
- `on-demand.py`: reads a session's spans and logs and calls an evaluator in the evaluation Region

Set `SOURCE_REGION`, `DEST_REGION` and, if needed, `AGENT_RUNTIME_ID` in the config files first.

---

## The sample agent

| Area | Details |
|---|---|
| Agent | Strands Agents SDK, Claude Haiku 4.5 on Amazon Bedrock (`backend/main.py`, `backend/system_prompt.py`) |
| Tools (via Gateway) | `lookup_order`, `track_delivery`, `request_return`, `search_products`, `get_product_detail`, `recommend_products`, `get_tech_guide` (`lambda/`) |
| Memory | Semantic facts, user preferences, session summaries |
| Data | 30 products, 15 orders for 3 customers, 12 tech guides (`backend/data/`, `backend/tech_guides/`) |
| Frontend | React chat UI with Cognito sign-in (`frontend/`) |
| Gateway auth | `AWS_IAM`: the runtime signs every MCP request with SigV4 (`backend/gateway_auth.py`); the deployment grants the runtime role `bedrock-agentcore:InvokeGateway` |

`REQUIREMENTS.md` (Korean) is the full design document.

---

## Demo user and secrets

- `scripts/06-setup-cognito.sh` creates the demo user `demo@vroomdash.example.com` with a **random
  password** and stores it in AWS Secrets Manager as `vroom-dash/demo-user-dev`. Re-running the
  script keeps the same password. Read it with:

  ```bash
  aws secretsmanager get-secret-value --secret-id vroom-dash/demo-user-dev --query SecretString --output text
  ```

- `scripts/10-write-frontend-env.sh` writes the Cognito IDs, the runtime ARN and the demo credentials
  to `frontend/.env.local` (git-ignored; see `frontend/.env.example`). The React dev server embeds
  these values in the page, so use the UI for local demos only and do not host the built bundle.

---

## Cleanup

Delete the CloudFormation stack created by `agentcore deploy` (`AgentCore-VroomDash-dev`), then the resources created by the scripts: Lambda functions, DynamoDB tables,
the S3 buckets and knowledge base, the Cognito user pool and identity pool, the IAM roles and the
`vroom-dash/demo-user-dev` secret. Online evaluation scores every session, so stop it when you are done.

---

## References

- [AgentCore CLI: evaluations](https://github.com/aws/agentcore-cli/blob/main/docs/evals.md)
- [Amazon Bedrock AgentCore documentation](https://docs.aws.amazon.com/bedrock-agentcore/)

---

## License

This project is licensed under the MIT No Attribution (MIT-0) License. See [LICENSE](./LICENSE).
