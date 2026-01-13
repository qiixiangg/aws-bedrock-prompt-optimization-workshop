"""
V4 Routing Agent - Model routing based on query complexity.
- Simple queries -> Haiku (cheaper)
- Complex queries -> Sonnet (better quality)
"""

import base64
import os
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel
from strands.telemetry import StrandsTelemetry
from strands.types.content import SystemContentBlock

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.tools import get_return_policy, get_product_info, web_search, get_technical_support

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

MODEL_HAIKU = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
MODEL_SONNET = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

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
def invoke(payload):
    user_input = payload.get("prompt", "")
    print(f"V4 ROUTING: User input: {user_input}")

    strands_telemetry = StrandsTelemetry()
    strands_telemetry.setup_otlp_exporter()

    # Route to appropriate model based on query complexity
    complexity = classify_query_complexity(user_input)
    model_id = MODEL_HAIKU if complexity == "simple" else MODEL_SONNET
    print(f"V4 ROUTING: Query complexity: {complexity}, using model: {model_id}")

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
        name="customer-support-v4-routing",
        trace_attributes={
            "version": "v4-routing",
            "query_complexity": complexity,
            "model_used": model_id,
            "langfuse.tags": ["routing", complexity],
        },
    )

    response = agent(user_input)
    response_text = response.message["content"][0]["text"]
    print(f"V4 ROUTING: Response: {response_text[:100]}...")

    # Flush telemetry to ensure spans are properly closed with correct timestamps
    strands_telemetry.tracer_provider.force_flush()

    return {"response": response_text, "model_used": model_id, "complexity": complexity}


if __name__ == "__main__":
    app.run()
