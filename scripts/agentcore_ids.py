"""Look up IDs of the deployed AgentCore runtime instead of hardcoding them.

Order: AGENT_RUNTIME_ID env var, then the runtime whose name is AGENT_RUNTIME_NAME
(default VroomDash_VroomDash, the name `agentcore deploy` gives this project).
"""

import os

import boto3

DEFAULT_RUNTIME_NAME = "VroomDash_VroomDash"


def runtime_name() -> str:
    return os.environ.get("AGENT_RUNTIME_NAME", DEFAULT_RUNTIME_NAME)


def resolve_runtime_id(region: str) -> str:
    if os.environ.get("AGENT_RUNTIME_ID"):
        return os.environ["AGENT_RUNTIME_ID"]
    name = runtime_name()
    client = boto3.client("bedrock-agentcore-control", region_name=region)
    token = None
    while True:
        resp = client.list_agent_runtimes(**({"nextToken": token} if token else {}))
        for rt in resp.get("agentRuntimes", []):
            if rt.get("agentRuntimeName") == name:
                return rt["agentRuntimeId"]
        token = resp.get("nextToken")
        if not token:
            break
    raise SystemExit(
        f"AgentCore runtime '{name}' not found in {region}. Deploy first "
        "(scripts/07-setup-agentcore.sh) or set AGENT_RUNTIME_ID."
    )
