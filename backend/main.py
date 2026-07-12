import os
import sys

from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from bedrock_agentcore.runtime import BedrockAgentCoreApp

from system_prompt import SYSTEM_PROMPT

# --- Configuration ---
MODEL_ID = os.environ.get("MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Gateway MCP URL (AgentCore Runtime에서 자동 주입됨)
# Local runs: export AGENTCORE_GATEWAY_VROOMDASHGATEWAY_URL=<gateway URL from `agentcore status`>
GATEWAY_URL = os.environ.get("AGENTCORE_GATEWAY_VROOMDASHGATEWAY_URL", "")


def load_model():
    return BedrockModel(
        model_id=MODEL_ID,
        region_name=AWS_REGION,
        temperature=0.7,
        max_tokens=2048,
    )


def create_mcp_transport():
    """Gateway MCP transport. Every request is SigV4-signed (Gateway authorizerType AWS_IAM)."""
    from mcp.client.streamable_http import streamablehttp_client

    from gateway_auth import GatewaySigV4Auth

    return streamablehttp_client(GATEWAY_URL, auth=GatewaySigV4Auth(AWS_REGION))


def create_agent_with_gateway_tools(**kwargs):
    """Gateway MCP에서 tools를 가져와 Agent 생성"""
    if not GATEWAY_URL:
        raise RuntimeError(
            "AGENTCORE_GATEWAY_VROOMDASHGATEWAY_URL is not set (AgentCore Runtime injects it; "
            "set it yourself for local runs)."
        )
    mcp_client = MCPClient(create_mcp_transport)

    with mcp_client:
        tools = mcp_client.list_tools_sync()
        return Agent(
            model=load_model(),
            system_prompt=SYSTEM_PROMPT,
            tools=tools,
            **kwargs,
        ), mcp_client


# --- AgentCore Runtime Entry Point ---
app = BedrockAgentCoreApp()
log = app.logger


@app.entrypoint
async def invoke(payload, context):
    log.info("Invoking Vroom&Dash Agent with Gateway tools...")

    session_id = getattr(context, 'session_id', None) or payload.get("session_id")
    user_id = payload.get("user_id") or payload.get("context", {}).get("user_id", "anonymous")
    prompt = payload.get("prompt") or payload.get("message", "")
    log.info(f"session_id={session_id}, user_id={user_id}")

    agent_kwargs = {}
    session_manager = None

    # AgentCore Memory 연동 (CDK 자동 주입 환경변수 사용)
    memory_id = os.environ.get("MEMORY_VROOMDASHMEMORY_ID") or os.environ.get("AGENTCORE_MEMORY_ID")
    if memory_id and session_id:
        try:
            from bedrock_agentcore.memory.integrations.strands.config import (
                AgentCoreMemoryConfig,
            )
            from bedrock_agentcore.memory.integrations.strands.session_manager import (
                AgentCoreMemorySessionManager,
            )

            memory_config = AgentCoreMemoryConfig(
                memory_id=memory_id,
                session_id=session_id,
                actor_id=user_id,
            )
            session_manager = AgentCoreMemorySessionManager(
                agentcore_memory_config=memory_config,
                region_name=AWS_REGION,
            )
            agent_kwargs["session_manager"] = session_manager
            log.info(f"Memory enabled: {memory_id}, session: {session_id}")
        except Exception as e:
            log.warning(f"Memory setup failed, running without memory: {e}")

    # Gateway MCP에서 tools 로드
    mcp_client = MCPClient(create_mcp_transport)

    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            log.info(f"Loaded {len(tools)} tools from Gateway")

            agent = Agent(
                model=load_model(),
                system_prompt=SYSTEM_PROMPT,
                tools=tools,
                **agent_kwargs,
            )

            stream = agent.stream_async(prompt)
            async for event in stream:
                if "data" in event and isinstance(event["data"], str):
                    yield event["data"]

            # Flush conversation to AgentCore Memory
            if session_manager:
                try:
                    session_manager.close()
                    log.info("Memory session closed — events flushed")
                except Exception as me:
                    log.warning(f"Memory flush failed: {me}")
    except Exception as e:
        log.error(f"Error during agent invocation: {e}")
        yield f"죄송합니다. 요청 처리 중 오류가 발생했습니다: {str(e)}"


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "local":
        # 로컬 CLI 모드 - Gateway tools 사용
        print("=== Vroom&Dash 고객 지원 에이전트 (Gateway 모드) ===")
        print(f"Gateway URL: {GATEWAY_URL}")
        print("종료하려면 'quit' 또는 'exit'를 입력하세요.\n")

        mcp_client = MCPClient(create_mcp_transport)

        try:
            with mcp_client:
                tools = mcp_client.list_tools_sync()
                print(f"로드된 도구: {len(tools)}개")
                for tool in tools:
                    desc = tool.tool_spec.get("description", "") or ""
                    print(f"  - {tool.tool_name}: {desc[:50]}...")
                print()

                agent = Agent(
                    model=load_model(),
                    system_prompt=SYSTEM_PROMPT,
                    tools=tools,
                )

                while True:
                    try:
                        user_input = input("고객: ").strip()
                        if not user_input:
                            continue
                        if user_input.lower() in ("quit", "exit", "종료"):
                            print("감사합니다! 좋은 하루 되세요!")
                            break
                        response = agent(user_input)
                        print(f"\nVroom&Dash: {response.message['content'][0]['text']}\n")
                    except KeyboardInterrupt:
                        print("\n감사합니다! 좋은 하루 되세요!")
                        break
        except Exception as e:
            print(f"Gateway 연결 실패: {e}")
            print("로컬 tools로 폴백합니다...")

            # 폴백: 로컬 tools 사용
            from tools import (
                lookup_order, track_delivery, request_return,
                search_products, get_product_detail, recommend_products,
                get_tech_guide,
            )

            TOOLS = [
                lookup_order, track_delivery, request_return,
                search_products, get_product_detail, recommend_products,
                get_tech_guide,
            ]

            agent = Agent(
                model=load_model(),
                system_prompt=SYSTEM_PROMPT,
                tools=TOOLS,
            )

            while True:
                try:
                    user_input = input("고객: ").strip()
                    if not user_input:
                        continue
                    if user_input.lower() in ("quit", "exit", "종료"):
                        print("감사합니다! 좋은 하루 되세요!")
                        break
                    response = agent(user_input)
                    print(f"\nVroom&Dash: {response.message['content'][0]['text']}\n")
                except KeyboardInterrupt:
                    print("\n감사합니다! 좋은 하루 되세요!")
                    break
    else:
        # AgentCore Runtime 모드
        app.run()
