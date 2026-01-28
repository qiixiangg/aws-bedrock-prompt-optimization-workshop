# Part 1: Basics (Fundamentals)

This section covers the foundational concepts for optimizing GenAI applications on Amazon Bedrock.

## Learning Objectives

After completing this section, you will:
- Understand tokens, pricing models, and throughput limits (TPM/RPM)
- Apply low-hanging fruit optimization strategies
- Use the CountTokens API for accurate token estimation
- Implement basic prompt caching patterns

## Notebooks

| Notebook | Duration | Description |
|----------|----------|-------------|
| [01-prompts-101](./01-prompts-101.ipynb) | 30 min | Tokens, pricing, TPM/RPM, terminology |
| [02-optimization-strategy](./02-optimization-strategy.ipynb) | 45 min | Model selection, prompt design, parameter tuning, basic caching |
| [03-langfuse-observability](./03-langfuse-observability.ipynb) | TBD | Observability with LangFuse (Pending) |

## Prerequisites

- AWS Account with Amazon Bedrock access
- Python 3.10+
- `.env` file with AWS credentials (see root `.env.example`)

## Key Metrics Covered

| Metric | Description |
|--------|-------------|
| **Accuracy** | Response correctness (LLM-as-judge, human eval) |
| **Cost** | Token costs (input, output, cache) |
| **Latency** | TTFT, TTLT, generation time |
| **Throughput** | TPM, RPM |
