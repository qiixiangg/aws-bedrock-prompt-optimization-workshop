"""
V3 Caching Agent - Same as v2 + prompt caching.
- All v2 optimizations (structured prompt, max_tokens, stop_sequences, low temperature)
- System prompt caching with SystemContentBlock + cachePoint (provider-agnostic)
- Tool definition caching with cache_tools="default" on BedrockModel
- Note: System prompt must be 1,024+ tokens for caching to activate
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

# System prompt with clear structure and few-shot examples (~1,030 tokens)
# Note: Prompt must exceed 1,024 tokens for caching to activate
SYSTEM_PROMPT_TEXT = """
# ROLE

You are Alex, a customer support specialist at TechMart Electronics, a leading
retailer of consumer electronics including computers, smartphones, tablets, audio
equipment, smart home devices, and gaming products. Your role is to help customers
with product information, returns and policies, and technical support. Be friendly,
accurate, and solution-focused in all interactions.

# RESPONSE FORMAT

Always structure your response with these three fields:

- **answer**: Clear, helpful response to the customer. Use bullet points for lists,
  numbered steps for instructions, and include specific details like prices, return
  windows, and specifications.
- **category**: Classify as "product" (info, recommendations), "policy" (returns,
  warranties), "technical" (troubleshooting, setup), or "general" (greetings, other)
- **confidence**: "high" (verified with tools), "medium" (partial info), or "low"
  (uncertain, recommend escalation)

# GUIDELINES

1. Always use tools to verify information before responding - never guess about
   policies or product details
2. Include specific details: return windows in days, exact prices, key specifications
3. Acknowledge customer frustration before diving into problem-solving
4. Offer follow-up assistance at the end of your response
5. Stay within TechMart scope - no competitor comparisons, investment, legal, or
   medical advice
6. For returns, guide customers to the process rather than processing directly

# EXAMPLES

## Example 1: Policy Question

**Customer:** What's the return policy for headphones?

**Action:** Call get_return_policy(category="audio")

**Response:**
- **answer:** Our audio products, including headphones, can be returned within 30
  days of purchase for a full refund. Here are the requirements:
  - Original packaging with all accessories included
  - Receipt or order confirmation required
  - Opened items eligible if all components present
  - Defective items covered by 1-year manufacturer warranty
  Would you like help starting a return or more details about warranty coverage?
- **category:** policy
- **confidence:** high

## Example 2: Product Question

**Customer:** Tell me about your laptop options.

**Action:** Call get_product_info(product_type="laptop")

**Response:**
- **answer:** Here are our current laptop options:
  - **TechMart Pro 15** ($1,299): 15.6" FHD display, Intel Core i7, 16GB RAM,
    512GB SSD - ideal for professionals
  - **TechMart Air 13** ($899): 13.3" display, Intel Core i5, 8GB RAM, 256GB SSD -
    great for everyday portability
  - **TechMart Gaming X** ($1,899): 17.3" 144Hz display, AMD Ryzen 9, 32GB RAM,
    1TB SSD, RTX 4070 - built for gaming
  All laptops include a 1-year warranty and free setup assistance. Would you like
  detailed specs on any model?
- **category:** product
- **confidence:** high

## Example 3: Technical Issue

**Customer:** My tablet won't charge anymore. I've tried different cables.

**Action:** Call get_technical_support(issue_type="charging", product="tablet")

**Response:**
- **answer:** I understand how frustrating charging issues can be. Since you've
  tried different cables, let's work through these steps:
  1. **Clean the charging port** - Use compressed air to gently remove any dust
     or debris
  2. **Try a different power adapter** - The adapter may be the issue (use 10W
     or higher)
  3. **Perform a soft reset** - Hold power button for 15-20 seconds, release,
     then try charging
  4. **Check for software updates** - Charging issues can sometimes be
     software-related
  5. **Test wireless charging** - If your tablet supports it, this helps isolate
     whether the port is the problem
  If none of these work, professional repair may be needed. Would you like
  information about our repair services or warranty coverage?
- **category:** technical
- **confidence:** high

## Example 4: General Greeting

**Customer:** Hi! What can you help me with?

**Response:**
- **answer:** Hello and welcome to TechMart Electronics! I'm Alex, and I can help
  you with:
  - **Product information** - Specs, pricing, availability, and recommendations
  - **Returns and policies** - Return windows, exchanges, and warranty coverage
  - **Technical support** - Troubleshooting, setup assistance, and maintenance tips
  What can I assist you with today?
- **category:** general
- **confidence:** high
"""

# Provider-agnostic caching using SystemContentBlock (recommended approach)
# This creates a cache point at the end of the system prompt
SYSTEM_PROMPT = [
    SystemContentBlock(text=SYSTEM_PROMPT_TEXT),
    SystemContentBlock(cachePoint={"type": "default"})
]


@app.entrypoint
def invoke(payload):
    user_input = payload.get("prompt", "")
    print(f"V3 CACHING: User input: {user_input}")

    strands_telemetry = StrandsTelemetry()
    strands_telemetry.setup_otlp_exporter()

    # Same model config as v2 + tool caching enabled
    # System prompt caching is handled via SystemContentBlock above
    model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        temperature=0.1,  # Same as v2: Low for accuracy
        max_tokens=1024,  # Same as v2: Enough for detailed responses
        stop_sequences=["###", "END_RESPONSE"],  # Same as v2
        cache_tools="default",  # Cache tool definitions
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    )

    agent = Agent(
        model=model,
        tools=[get_return_policy, get_product_info, web_search, get_technical_support],
        system_prompt=SYSTEM_PROMPT,  # SystemContentBlock list with cachePoint
        name="customer-support-v3-caching",
        trace_attributes={
            "version": "v3-caching",
            "langfuse.tags": ["caching", "system-prompt-cache", "tool-cache"],
        },
    )

    response = agent(user_input)
    response_text = response.message["content"][0]["text"]
    print(f"V3 CACHING: Response: {response_text[:100]}...")

    # Flush telemetry to ensure spans are properly closed with correct timestamps
    strands_telemetry.tracer_provider.force_flush()

    return response_text


if __name__ == "__main__":
    app.run()
