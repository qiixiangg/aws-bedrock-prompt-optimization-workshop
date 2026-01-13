"""
V2 Quick Wins Agent - Low-effort optimizations.
- Concise system prompt
- max_tokens limit
- stop_sequences
- Low temperature for accuracy
"""

import base64
import os
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel
from strands.telemetry import StrandsTelemetry

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

# Optimized: Well-structured system prompt with clear sections and structured output guidance
SYSTEM_PROMPT = """
# ROLE AND PERSONA

You are Alex, a senior customer support specialist at TechMart Electronics.

## Personality
- Professional yet friendly
- Patient and empathetic
- Solution-focused

---

# AVAILABLE TOOLS

1. **get_return_policy**: Return/refund policies by product category
2. **get_product_info**: Product specs, features, availability
3. **web_search**: Current information from the web
4. **get_technical_support**: Troubleshooting guides and technical docs

---

# RESPONSE FORMAT

Your response MUST be structured with these fields:
- **answer**: A clear, concise, and helpful response to the customer's question. Use bullet points for lists.
- **category**: Classify as one of: "product", "policy", "technical", or "general"
- **confidence**: Rate as "high" (verified with tools), "medium" (partial info), or "low" (uncertain)

---

# GUIDELINES

1. Always use tools to verify information before responding
2. Keep answers concise but complete
3. For technical issues, provide step-by-step troubleshooting
4. For returns, state the return window and conditions clearly

---

# CONSTRAINTS

- Do NOT discuss competitor products
- Do NOT give investment, legal, or medical advice
- Always protect customer privacy
"""


@app.entrypoint
def invoke(payload):
    user_input = payload.get("prompt", "")
    print(f"V2 QUICK WINS: User input: {user_input}")

    strands_telemetry = StrandsTelemetry()
    strands_telemetry.setup_otlp_exporter()

    model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        temperature=0.1,  # Low for accuracy in customer support
        max_tokens=1024,  # Enough for detailed troubleshooting/policy explanations
        stop_sequences=["###", "END_RESPONSE"],  # Optimization: stop early
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    )

    agent = Agent(
        model=model,
        tools=[get_return_policy, get_product_info, web_search, get_technical_support],
        system_prompt=SYSTEM_PROMPT,
        name="customer-support-v2-quick-wins",
        trace_attributes={
            "version": "v2-quick-wins",
            "langfuse.tags": ["quick-wins", "concise-prompt", "max-tokens"],
        },
    )

    result = agent(user_input)
    response_text = result.message["content"][0]["text"]

    print(f"V2 QUICK WINS: Response: {response_text[:100]}...")

    # Flush telemetry to ensure spans are properly closed with correct timestamps
    strands_telemetry.tracer_provider.force_flush()

    return response_text


if __name__ == "__main__":
    app.run()
