# AWS Bedrock Prompt Optimization Workshop

This hands-on workshop teaches you how to build production-grade generative AI applications with a focus on cost optimization, performance enhancement, and operational excellence.

**Target Audience**: AI/ML Developers, Software Engineers working with agentic systems, DevOps Engineers deploying GenAI workloads

---

## Workshop Objectives

This workshop focuses on optimizing three key metrics for production GenAI applications:

| Objective | Definition | Why It Matters |
|-----------|------------|----------------|
| **Accuracy** | The quality and correctness of model outputs relative to expected results | Ensures your application delivers value to users and meets business requirements |
| **Cost** | Total expenditure on model inference, including input tokens, output tokens, and cache operations | Controls operational expenses and enables sustainable scaling |
| **Latency** | Time elapsed from request initiation to response completion | Impacts user experience and application responsiveness |

---

## Workshop Structure

This workshop is organized into progressive parts:

### Part 1: Basis - Fundamentals
*Estimated time: 1.5 hours*

Build a solid understanding of tokens, pricing, and optimization strategies.

| Topic | Duration | Description |
|-------|----------|-------------|
| [Prompts 101](./01-basis/01-prompts-101.ipynb) | 30 min | Tokens, pricing, TPM/RPM, terminology |
| [Optimization Strategy](./01-basis/02-optimization-strategy.ipynb) | 45 min | Model selection, prompt design, parameter tuning, basic caching |
| [Langfuse Observability](./01-basis/03-langfuse-observability.ipynb) | TBD | Observability with LangFuse (Pending) |

### Part 2: Developer Journey
*Estimated time: 2 hours*

Build a production-ready application applying optimization techniques (coming soon).

### Part 3: Advanced Concepts
*Estimated time: 2-2.5 hours*

Advanced prompt engineering techniques and complex caching patterns.

| Topic | Duration | Description |
|-------|----------|-------------|
| Advanced Prompt Engineering | 60-90 min | CoT, Self-Refine, CoD, technique selection |
| Advanced Prompt Caching | 60 min | Multi-checkpoint patterns, cache strategies |
| TBD | TBD | TBD |

---

## Prerequisites

### Required
- AWS Account with Amazon Bedrock access enabled
- Python 3.9 or higher
- Basic familiarity with Python and Jupyter notebooks

---

## Setup Instructions

### 1. Local Environment Setup

#### Option A: Using uv (Recommended - Fast!)

**Install uv** (if not already installed):

**macOS/Linux**:
```bash
# Option 1: Official installer (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Option 2: Using Homebrew
brew install uv

# Option 3: Using pipx
brew install pipx
pipx install uv
```

**Windows**:
```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Create and activate virtual environment**:
```bash
# Create virtual environment with Python 3.9+
uv venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies (uv is much faster than pip!)
uv pip install -r requirements.txt
```

#### Option B: Using standard pip

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

### 2. Configure AWS Credentials

The workshop supports multiple credential methods:

#### Method 1: AWS CLI Credentials (Recommended)

If you already have AWS CLI configured, the notebooks will automatically use your credentials:

```bash
# No additional setup needed - boto3 uses ~/.aws/credentials
```

#### Method 2: Environment Variables (.env file)

If you prefer to use a `.env` file:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and uncomment the AWS credentials
# Then add your actual credentials:
# AWS_ACCESS_KEY_ID=your-actual-access-key-id
# AWS_SECRET_ACCESS_KEY=your-actual-secret-access-key
# AWS_DEFAULT_REGION=us-east-1
```

The notebooks will automatically load credentials using `python-dotenv`.

---

### 3. Test Bedrock Connectivity

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); import boto3; client = boto3.client('bedrock-runtime'); print('Bedrock connection successful'); print(f'Region: {client.meta.region_name}')"
```

---

## License

This workshop is provided under the MIT-0 license. See LICENSE file for details.

---

**Last Updated**: January 2026
