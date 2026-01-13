"""
V4 Routing Agent - Model routing based on query complexity.
- Same system prompt as v3 with prompt caching
- LLM-based classification using Haiku
- Simple queries -> Haiku (cheaper)
- Complex queries -> Sonnet (better quality)
"""

import base64
import json
import os

from opentelemetry import trace

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

# Model IDs
MODEL_HAIKU = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
MODEL_SONNET = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"


# Classifier prompt for LLM-based routing
CLASSIFIER_PROMPT = """Classify customer support queries for model routing.

SIMPLE queries (route to cheaper model):
- Greetings and general questions
- Single factual lookups (price, policy, hours)
- Direct questions with straightforward answers

COMPLEX queries (route to powerful model):
- Multi-step troubleshooting
- Product comparisons or recommendations
- Questions requiring analysis or reasoning
- Multiple questions in one message

Respond with ONLY one word: simple or complex

Examples:

Query: "What is your return policy for laptops?"
simple

Query: "Tell me about your smartphone options"
simple

Query: "Hello! What can you help me with today?"
simple

Query: "My laptop won't turn on, can you help me troubleshoot?"
complex

Query: "I want to buy a laptop. What are the specs and what's the return policy?"
complex"""

# System prompt with clear structure and few-shot examples (~1,030 tokens)
# Same as v3 - meets 1,024 token minimum for caching
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

# Provider-agnostic caching using SystemContentBlock
SYSTEM_PROMPT = [
    SystemContentBlock(text=SYSTEM_PROMPT_TEXT),
    SystemContentBlock(cachePoint={"type": "default"})
]


def classify_query_complexity(query: str, region: str) -> str:
    """Use Haiku to classify query complexity."""
    classifier_model = BedrockModel(
        model_id=MODEL_HAIKU,
        temperature=0,
        max_tokens=50,
        region_name=region,
    )
    classifier = Agent(
        model=classifier_model,
        system_prompt=CLASSIFIER_PROMPT,
        name="customer-support-v4-classifier",
        trace_attributes={
            "version": "v4-routing",
            "component": "classifier",
            "langfuse.tags": ["routing", "classifier"],
        },
    )
    # Use regular agent call for proper cost tracking in Langfuse
    result = classifier(query)
    response_text = result.message["content"][0]["text"].strip().lower()

    # Parse the response - expect "simple" or "complex"
    if "simple" in response_text:
        return "simple"
    return "complex"


@app.entrypoint
def invoke(payload):
    user_input = payload.get("prompt", "")
    print(f"V4 ROUTING: User input: {user_input}")

    strands_telemetry = StrandsTelemetry()
    strands_telemetry.setup_otlp_exporter()

    # Get the tracer to create a parent span that wraps both classifier and main agent
    tracer = trace.get_tracer("customer-support-v4-routing")

    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

    # Create a parent span to nest both classifier and main agent calls
    with tracer.start_as_current_span(
        "customer-support-v4-routing",
        attributes={
            "gen_ai.system": "strands",
            "gen_ai.agent.name": "customer-support-v4-routing",
            "version": "v4-routing",
            # Langfuse input attribute (must be JSON string)
            "langfuse.observation.input": json.dumps({"prompt": user_input}),
        }
    ) as parent_span:
        # Classify query complexity using Haiku (will be a child span)
        complexity = classify_query_complexity(user_input, region)
        model_id = MODEL_HAIKU if complexity == "simple" else MODEL_SONNET
        print(f"V4 ROUTING: Query complexity: {complexity}, using model: {model_id}")

        # Add routing info to parent span
        parent_span.set_attribute("query_complexity", complexity)
        parent_span.set_attribute("model_used", model_id)

        # Create model with caching enabled (inside parent span)
        model = BedrockModel(
            model_id=model_id,
            temperature=0.1,
            max_tokens=1024,
            stop_sequences=["###", "END_RESPONSE"],
            cache_tools="default",
            region_name=region,
        )

        # Main agent call (will be a child span of parent)
        agent = Agent(
            model=model,
            tools=[get_return_policy, get_product_info, web_search, get_technical_support],
            system_prompt=SYSTEM_PROMPT,
            name="customer-support-v4-main",
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

        # Set Langfuse output attribute BEFORE span closes (must be JSON string)
        parent_span.set_attribute(
            "langfuse.observation.output",
            json.dumps({"response": response_text, "model_used": model_id, "complexity": complexity})
        )

    # Flush telemetry to ensure spans are properly closed with correct timestamps
    strands_telemetry.tracer_provider.force_flush()

    return {"response": response_text, "model_used": model_id, "complexity": complexity}


if __name__ == "__main__":
    app.run()
