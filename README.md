# Amazon Bedrock Prompt Optimization Workshop

## Workshop Overview

### Purpose
This workshop empowers AI developers to build production-grade generative AI applications with a focus on cost optimization, performance enhancement, and operational excellence. Participants will learn advanced prompt optimization techniques, implement prompt caching strategies, and integrate production-ready tooling for GenAI application lifecycle management.

### Target Audience
- AI/ML Developers building GenAI and LLM applications
- Software Engineers working with agentic systems
- DevOps Engineers deploying production GenAI workloads
- Solution Architects designing enterprise AI solutions

### Workshop Duration
4-5 hours (instructor-led with hands-on labs)

### Prerequisites
- AWS Account with Amazon Bedrock access enabled
- Python 3.9+ installed locally
- boto3 SDK familiarity
- Basic understanding of LLMs and prompt engineering concepts

### Key Learning Objectives

By the end of this workshop, you will be able to:

1. **Optimize costs and latency** through strategic prompt caching (significant cost and latency reductions)
2. **Apply systematic prompt optimization techniques** using manual and automated methods
3. **Build production-grade agentic systems** with proper observability, monitoring, and evaluation
4. **Integrate CI/CD practices** for prompt lifecycle management
5. **Implement evaluation frameworks** for systematic prompt testing and validation

---

## Workshop Structure

### **Part 1: Theory & Foundations** (01-theory-foundations/)
Learn the fundamentals of prompt optimization economics and caching mechanics.

**Notebooks**:
- `01-economics-of-optimization.ipynb` - Why optimization matters (cost, latency, scale)
- `02-understanding-prompt-caching.ipynb` - Cache mechanics, TTL, cost structure

**Duration**: ~60 minutes

---

### **Part 2: Best Practices** (02-best-practices/)
Master caching patterns and systematic optimization with hands-on practice.

**Notebooks**:
- `01-prompt-caching.ipynb` (2.5 hours)
  - **Caching Patterns**: Pattern 1, 2, 3 with immediate hands-on practice after each
  - **Strategy Principles**: Longest prefix, static/dynamic separation, monitoring, warm-up
  - **7 integrated exercises**: Learn → Practice flow for better retention

- `02-prompt-optimization.ipynb` (2.5 hours)
  - **Decision Framework**: Manual vs. automated optimization
  - **Manual Optimization**: Clear instructions, few-shot examples, Chain-of-Thought, structured output
  - **Automated Optimization**: Bedrock API, Metaprompting, Data-Aware, DSPy
  - **Comprehensive Lab**: Apply optimization techniques systematically
  - **Best Practices**: Model selection, version control, monitoring

**Duration**: ~5 hours

---

### **Part 3: Developer Journey** (03-developer-journey/)
Build a production customer support agent with optimization, caching, observability, and CI/CD.

**Use Case**: CloudCommerce Customer Support AI Assistant

**Notebooks**:
- `01-baseline-prompt.ipynb` - v1.0.0 baseline with clear instructions and examples
- `02-optimized-prompt.ipynb` - v1.1.0 with optimization techniques (CoT + structured output)
- `03-caching-implementation.ipynb` - Apply multi-checkpoint caching
- `04-observability.ipynb` - LangFuse + CloudWatch integration
- `05-evaluation-framework.ipynb` - Systematic testing & metrics
- `06-cicd-simulation.ipynb` - CI/CD workflow walkthrough

**Duration**: ~2 hours

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
python -c "from dotenv import load_dotenv; load_dotenv(); import boto3; client = boto3.client('bedrock-runtime'); print('✅ Bedrock connection successful'); print(f'Region: {client.meta.region_name}')"
```

Expected output:
```
✅ Bedrock connection successful
Region: us-east-1
```

---

### 4. Optional: Observability Tools

**LangFuse Setup** (for Lab 4):
1. Sign up at [langfuse.com](https://langfuse.com)
2. Create a new project
3. Copy API keys (public key + secret key)
4. Add credentials to your `.env` file:
```bash
# Add to .env
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## Workshop Flow

1. **Start with Part 1** to understand the fundamentals
2. **Move to Part 2** for hands-on practice with patterns and labs
3. **Complete Part 3** to build a full production use case
4. **Optional**: Extend the use case with your own data and requirements

---

## Additional Resources

- **AWS Documentation**: [Amazon Bedrock User Guide](https://docs.aws.amazon.com/bedrock/)
- **Pricing**: [Amazon Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- **Samples**: [Amazon Bedrock Samples GitHub](https://github.com/aws-samples/amazon-bedrock-samples)
- **Community**: [AWS re:Post - Bedrock](https://repost.aws/tags/TA4ckIB8_RRRKfB_okAkg39g/amazon-bedrock)

---

## Support

For questions or issues during the workshop:
- Raise your hand for instructor assistance
- Check the troubleshooting section in each notebook
- Refer to AWS documentation links provided

---

## License

This workshop is provided under the MIT-0 license. See LICENSE file for details.
