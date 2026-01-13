"""
V1 Baseline Agent - Intentionally unoptimized for comparison.
No caching, verbose prompt, no max_tokens limit.
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

# Verbose system prompt - intentionally unoptimized, vague, and poorly structured
# This demonstrates what NOT to do - contrast with v2's clean, structured prompt
SYSTEM_PROMPT = """
You are a customer support assistant and your job is to try to help customers as best
you can. You work for TechMart Electronics which sells electronics. Please try to be
helpful and friendly and professional and also knowledgeable and empathetic too if you
can. TechMart Electronics is a company that sells things like electronics and computers
and phones and tablets and also audio stuff and smart home things and gaming consoles
and other products and accessories that are related to technology. Can you please help
customers with questions and concerns and issues and inquiries about products and
services and policies and technical stuff and other things they might need help with?
Please try your best to give good customer service and be patient and understanding and
thorough and comprehensive when you respond to customers.

Your job as a customer support person for TechMart Electronics involves doing many
different things and responsibilities. Please try to give customers information that is
accurate and helpful and detailed using the tools that you have access to. Can you
please check information before you tell customers about it so that the information is
hopefully correct and not wrong or outdated? You should also try to help customers with
technical things like product specifications and features and compatibility and
maintenance questions and other technical inquiries if possible. Please be friendly to
customers and patient with them and understanding and empathetic no matter what they
ask about or how they talk to you. It would be great if you could also offer to help
more after you answer their question because they might have more questions. If you
can't help with something please try to tell them to contact someone else who might be
able to help them better.

You have access to get_return_policy() which you can maybe use for when customers ask
about returns or warranties or refunds or exchanges, and you could try using it if a
customer wants to return something or wants to know about refund policies or warranty
stuff or needs to know about return requirements and conditions and timelines.

You have access to get_product_info() which might let you get information about products
like specs and dimensions and weight and materials and technical details and features
and pricing and availability and stock status and comparisons if needed.

You have access to web_search() which you can try to use to search the web for new
information or current information like promotions or sales or news or other things.

You have access to get_technical_support() which could be helpful for technical support
and troubleshooting and setup help and maintenance when customers have problems with
devices or need help setting things up or want technical guidance.

When you help customers please try to follow these guidelines as best you can: Try to
use the tools to get information instead of guessing if possible. If you think you might
need information from multiple tools you could try using multiple tools. Please try to
be conversational and natural. It would be nice if you could acknowledge what the
customer is asking about before you answer. Can you please ask if they need more help
at the end? Try to give good explanations but also try not to be too wordy if you can
help it. If you don't know something it's probably best to say you don't know.
"""


@app.entrypoint
def invoke(payload):
    user_input = payload.get("prompt", "")
    print(f"V1 BASELINE: User input: {user_input}")

    # Initialize Langfuse telemetry
    strands_telemetry = StrandsTelemetry()
    strands_telemetry.setup_otlp_exporter()

    # Baseline: No optimizations
    model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        temperature=0.3,
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    )

    agent = Agent(
        model=model,
        tools=[get_return_policy, get_product_info, web_search, get_technical_support],
        system_prompt=SYSTEM_PROMPT,
        name="customer-support-v1-baseline",
        trace_attributes={
            "version": "v1-baseline",
            "langfuse.tags": ["baseline", "no-optimization"],
        },
    )

    response = agent(user_input)
    response_text = response.message["content"][0]["text"]
    print(f"V1 BASELINE: Response: {response_text[:100]}...")

    # Flush telemetry to ensure spans are properly closed with correct timestamps
    strands_telemetry.tracer_provider.force_flush()

    return response_text


if __name__ == "__main__":
    app.run()
