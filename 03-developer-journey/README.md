# Part 3: Developer Journey

## Overview

Build a production customer support agent for **CloudCommerce** by applying everything from Parts 1 and 2.

**Use Case**: Customer Support AI Assistant
- Handles returns/refunds, order inquiries, product questions
- 3 tools: Knowledge Base, Order Management, Ticket System

**Duration**: ~2 hours

---

## Notebooks

### **01-baseline-prompt.ipynb** (30 min)

Create baseline with clear instructions and few-shot examples.

**Build**:
- Company policies document
- System prompt with role and instructions
- Few-shot examples
- Test with sample queries and measure metrics

---

### **02-optimized-prompt.ipynb** (30 min)

Apply optimization techniques (Chain-of-Thought + structured thinking).

**Improvements**:
- CoT instructions ("think step-by-step")
- Structured thinking blocks
- Enhanced policy adherence

---

### **03-caching-implementation.ipynb** (45 min)

Implement multi-checkpoint caching (tools → system → history).

**3-Checkpoint Strategy**:
- Checkpoint 1: Tool definitions
- Checkpoint 2: System prompt + policies
- Checkpoint 3: Conversation history

---

### **04-observability.ipynb** (45 min)

Integrate LangFuse and CloudWatch for monitoring.

**LangFuse**: Prompt tracing, cost tracking, A/B testing, version comparison
**CloudWatch**: Latency metrics, error rates, cache hit rate, custom alarms

---

### **05-evaluation-framework.ipynb** (60 min)

Build systematic evaluation with multiple metrics.

**Evaluation Metrics**:
- Semantic similarity (embeddings)
- Keyword/topic coverage
- Tool usage validation
- LLM-as-judge (Claude Opus)

---

### **06-cicd-simulation.ipynb** (30 min)

Simulate CI/CD workflow for prompt lifecycle management.

**Pipeline Stages**:
1. Syntax check & security scan
2. Functional tests (evaluation framework)
3. Performance tests (latency, cost)
4. Cost estimation & approval gate
5. Deployment with backup
6. Smoke tests
7. Rollback capability

---

## Prerequisites

- Completed Parts 1 and 2
- AWS Bedrock access
- Optional: LangFuse account (for Lab 4)

---

## Success Criteria

Production-ready agent when you can:

- [ ] Build baseline with systematic optimization
- [ ] Implement multi-checkpoint caching with effective hit rate
- [ ] Monitor with LangFuse and CloudWatch
- [ ] Evaluate systematically with high pass rate
- [ ] Deploy with CI/CD simulation

---

## What's Next?

Extend the agent with your own use case, data, and requirements.
