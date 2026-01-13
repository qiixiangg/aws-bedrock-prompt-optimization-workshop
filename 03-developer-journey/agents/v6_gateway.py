"""
V6 Gateway Agent - AgentCore Gateway with semantic tool search.
- Load only relevant tools per query
- Reduce context size and token usage
"""

import base64
import os
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models import BedrockModel
from strands.telemetry import StrandsTelemetry
from strands.tools.mcp import MCPClient
from strands.types.content import SystemContentBlock

load_dotenv()

# Langfuse configuration
langfuse_public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
langfuse_secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
langfuse_host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")
LANGFUSE_AUTH = base64.b64encode(f"{langfuse_public_key}:{langfuse_secret_key}".encode()).decode()

os.environ["LANGFUSE_PROJECT_NAME"] = "my-llm-project"
os.environ["DISABLE_ADOT_OBSERVABILITY"] = "true"
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{langfuse_host}/api/public/otel"
os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"

for k in [
    "OTEL_EXPORTER_OTLP_LOGS_HEADERS",
    "AGENT_OBSERVABILITY_ENABLED",
    "OTEL_PYTHON_DISTRO",
    "OTEL_RESOURCE_ATTRIBUTES",
    "OTEL_PYTHON_CONFIGURATOR",
    "OTEL_PYTHON_EXCLUDED_URLS",
]:
    os.environ.pop(k, None)

app = BedrockAgentCoreApp()

GATEWAY_URL = os.environ.get("GATEWAY_URL")
GUARDRAIL_ID = os.environ.get("GUARDRAIL_ID")

SYSTEM_PROMPT_TEXT = """You are a customer support assistant for TechMart Electronics.

Available tools:
- get_return_policy: Return/refund policy by product category
- get_product_info: Product specs and features
- web_search: Current information from the web
- get_technical_support: Technical troubleshooting from knowledge base

Be concise and accurate. Use tools to get information before answering."""

SYSTEM_PROMPT = [
    SystemContentBlock(text=SYSTEM_PROMPT_TEXT),
    SystemContentBlock(cachePoint={"type": "default"})
]


def classify_query_complexity(query: str) -> str:
    """Classify query as 'simple' or 'complex'."""
    simple_patterns = [
        "return policy", "warranty", "price", "hours", "shipping",
        "what is", "how much", "when does", "do you have", "can i return"
    ]
    query_lower = query.lower()
    for pattern in simple_patterns:
        if pattern in query_lower:
            return "simple"
    return "complex"


@app.entrypoint
async def invoke(payload, context=None):
    user_input = payload.get("prompt", "")
    print(f"V6 GATEWAY: User input: {user_input}")

    strands_telemetry = StrandsTelemetry()
    strands_telemetry.setup_otlp_exporter()

    complexity = classify_query_complexity(user_input)
    model_id = "us.anthropic.claude-haiku-4-5-20251001-v1:0" if complexity == "simple" else "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

    # If Gateway is configured, use semantic tool search
    if GATEWAY_URL and context:
        auth_header = context.request_headers.get("Authorization", "")

        mcp_client = MCPClient(
            lambda: streamablehttp_client(url=GATEWAY_URL, headers={"Authorization": auth_header})
        )

        with mcp_client:
            # Semantic search for relevant tools
            search_result = mcp_client.call_tool_sync(
                "x_amz_bedrock_agentcore_search",
                {"query": user_input}
            )
            relevant_tools = search_result.content
            tools_loaded = len(relevant_tools)
            print(f"V6 GATEWAY: Loaded {tools_loaded} relevant tools via semantic search")

            model_kwargs = {
                "model_id": model_id,
                "temperature": 0.3,
                "max_tokens": 500,
                "stop_sequences": ["###", "END_RESPONSE"],
                "cache_tools": "default",
                "region_name": os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            }

            if GUARDRAIL_ID:
                model_kwargs["guardrail_id"] = GUARDRAIL_ID
                model_kwargs["guardrail_version"] = "DRAFT"

            model = BedrockModel(**model_kwargs)

            agent = Agent(
                model=model,
                tools=relevant_tools,
                system_prompt=SYSTEM_PROMPT,
                name="customer-support-v6-gateway",
                trace_attributes={
                    "version": "v6-gateway",
                    "tools_loaded": tools_loaded,
                    "query_complexity": complexity,
                    "langfuse.tags": ["gateway", "semantic-search"],
                },
            )

            response = agent(user_input)
            response_text = response.message["content"][0]["text"]
            print(f"V6 GATEWAY: Response: {response_text[:100]}...")

            # Flush telemetry to ensure spans are properly closed with correct timestamps
            strands_telemetry.tracer_provider.force_flush()

            return {"response": response_text, "tools_loaded": tools_loaded}

    # Fallback: load all tools locally
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.tools import get_return_policy, get_product_info, web_search, get_technical_support

    model = BedrockModel(
        model_id=model_id,
        temperature=0.3,
        max_tokens=500,
        stop_sequences=["###", "END_RESPONSE"],
        cache_tools="default",
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    )

    agent = Agent(
        model=model,
        tools=[get_return_policy, get_product_info, web_search, get_technical_support],
        system_prompt=SYSTEM_PROMPT,
        name="customer-support-v6-gateway",
        trace_attributes={
            "version": "v6-gateway-fallback",
            "tools_loaded": 4,
            "query_complexity": complexity,
            "langfuse.tags": ["gateway-fallback"],
        },
    )

    response = agent(user_input)
    response_text = response.message["content"][0]["text"]
    print(f"V6 GATEWAY (fallback): Response: {response_text[:100]}...")

    # Flush telemetry to ensure spans are properly closed with correct timestamps
    strands_telemetry.tracer_provider.force_flush()

    return {"response": response_text, "tools_loaded": 4}


if __name__ == "__main__":
    app.run()
