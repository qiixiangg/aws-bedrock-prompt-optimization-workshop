"""
Langfuse metrics helper - Query traces directly to get accurate metrics.
"""

import os
import time
from dotenv import load_dotenv

load_dotenv()

# Global list to collect metrics across invocations
_collected_metrics = []


def clear_metrics():
    """Clear all collected metrics."""
    global _collected_metrics
    _collected_metrics = []


def collect_metric(metrics: dict, test_name: str = ""):
    """Add a metric result to the collection."""
    global _collected_metrics
    entry = {"test_name": test_name, **metrics}
    _collected_metrics.append(entry)


def get_collected_metrics():
    """Return all collected metrics."""
    return _collected_metrics.copy()


def print_metrics_table():
    """Print all collected metrics as a formatted table."""
    global _collected_metrics

    if not _collected_metrics:
        print("No metrics collected yet.")
        return

    # Try to use pandas for nicer display
    try:
        import pandas as pd

        rows = []
        for m in _collected_metrics:
            if "error" not in m:
                rows.append({
                    "Test": m.get("test_name", ""),
                    "Latency": f"{m.get('latency_seconds', 0):.2f}s" if m.get('latency_seconds') else "N/A",
                    "Cost": f"${m.get('cost_usd', 0):.4f}",
                    "Input": f"{m.get('input_tokens', 0):,}",
                    "Output": f"{m.get('output_tokens', 0):,}",
                    "Cache Read Tokens": f"{m.get('cache_read_tokens', 0):,}",
                    "Cache Write Tokens": f"{m.get('cache_write_tokens', 0):,}",
                })
            else:
                rows.append({
                    "Test": m.get("test_name", ""),
                    "Latency": "ERROR",
                    "Cost": "-",
                    "Input": "-",
                    "Output": "-",
                    "Cache Read Tokens": "-",
                    "Cache Write Tokens": "-",
                })

        df = pd.DataFrame(rows)

        # Calculate totals
        total_cost = sum(m.get('cost_usd', 0) for m in _collected_metrics if "error" not in m)
        total_input = sum(m.get('input_tokens', 0) for m in _collected_metrics if "error" not in m)
        total_output = sum(m.get('output_tokens', 0) for m in _collected_metrics if "error" not in m)
        total_cache_read = sum(m.get('cache_read_tokens', 0) for m in _collected_metrics if "error" not in m)
        total_cache_write = sum(m.get('cache_write_tokens', 0) for m in _collected_metrics if "error" not in m)
        avg_latency = sum(m.get('latency_seconds', 0) or 0 for m in _collected_metrics if "error" not in m) / max(len([m for m in _collected_metrics if "error" not in m]), 1)

        print("\n" + "=" * 105)
        print("                                  METRICS SUMMARY")
        print("=" * 105)
        print(df.to_string(index=False))
        print("-" * 105)
        print(f"  TOTALS: Latency(avg): {avg_latency:.2f}s | Cost: ${total_cost:.4f} | Input: {total_input:,} | Output: {total_output:,}")
        print(f"          Cache Read Tokens: {total_cache_read:,} | Cache Write Tokens: {total_cache_write:,}")
        print("=" * 105 + "\n")

        return df

    except ImportError:
        # Fallback to manual formatting
        print("\n" + "=" * 120)
        print("                                           METRICS SUMMARY")
        print("=" * 120)
        print(f"{'Test':<20} {'Latency':>8} {'Cost':>10} {'Input':>10} {'Output':>10} {'Cache Read Tokens':>18} {'Cache Write Tokens':>19}")
        print("-" * 120)

        total_cost = 0
        total_input = 0
        total_output = 0
        total_cache_read = 0
        total_cache_write = 0
        total_latency = 0
        count = 0

        for m in _collected_metrics:
            test = m.get("test_name", "")[:19]
            if "error" not in m:
                lat = f"{m.get('latency_seconds', 0):.2f}s" if m.get('latency_seconds') else "N/A"
                cost = f"${m.get('cost_usd', 0):.4f}"
                inp = f"{m.get('input_tokens', 0):,}"
                out = f"{m.get('output_tokens', 0):,}"
                c_read = f"{m.get('cache_read_tokens', 0):,}"
                c_write = f"{m.get('cache_write_tokens', 0):,}"

                total_cost += m.get('cost_usd', 0)
                total_input += m.get('input_tokens', 0)
                total_output += m.get('output_tokens', 0)
                total_cache_read += m.get('cache_read_tokens', 0)
                total_cache_write += m.get('cache_write_tokens', 0)
                total_latency += m.get('latency_seconds', 0) or 0
                count += 1
            else:
                lat, cost, inp, out, c_read, c_write = "ERROR", "-", "-", "-", "-", "-"

            print(f"{test:<20} {lat:>8} {cost:>10} {inp:>10} {out:>10} {c_read:>18} {c_write:>19}")

        print("-" * 120)
        avg_lat = total_latency / max(count, 1)
        print(f"{'TOTALS':<20} {f'{avg_lat:.2f}s':>8} {f'${total_cost:.4f}':>10} {f'{total_input:,}':>10} {f'{total_output:,}':>10} {f'{total_cache_read:,}':>18} {f'{total_cache_write:,}':>19}")
        print("=" * 120 + "\n")


def get_latest_trace_metrics(
    agent_name: str = "customer-support-v1-baseline",
    wait_seconds: int = 5,
    max_retries: int = 5,
    timeout_seconds: int = 120,
) -> dict:
    """
    Get metrics from the latest trace for a given agent using Langfuse SDK.

    Args:
        agent_name: Name of the agent to filter traces by
        wait_seconds: Seconds to wait for trace to be ingested
        max_retries: Number of retries on timeout
        timeout_seconds: Timeout per request

    Returns:
        dict with metrics
    """
    from langfuse import Langfuse
    import httpx

    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        return {"error": "LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY not set"}

    # Wait for trace to be ingested (silently)
    if wait_seconds > 0:
        time.sleep(wait_seconds)

    # Create client with extended timeout
    langfuse = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=host,
        httpx_client=httpx.Client(timeout=timeout_seconds),
    )

    # Fetch traces with retries (silently)
    traces = None
    for attempt in range(max_retries):
        try:
            traces = langfuse.api.trace.list(limit=5)
            break
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                return {"error": f"Failed after {max_retries} attempts: {e}"}

    if not traces or not traces.data:
        return {"error": "No traces returned"}

    # Find the latest trace for this agent
    latest_trace = None
    for trace in traces.data:
        trace_name = getattr(trace, 'name', '') or ''
        if agent_name in trace_name:
            latest_trace = trace
            break

    if not latest_trace:
        return {"error": f"No trace found for agent: {agent_name}"}

    trace_id = latest_trace.id

    # Get observations for this trace
    try:
        obs_response = langfuse.api.observations.get_many(trace_id=trace_id, limit=50)
        observations = obs_response.data if hasattr(obs_response, 'data') else []
    except Exception:
        observations = []

    # Helper to safely convert string/int/dict values to int
    def safe_int(val):
        if val is None:
            return 0
        if isinstance(val, (int, float)):
            return int(val)
        if isinstance(val, str):
            # Check if it's a JSON string like '{"intValue":0}'
            if val.startswith('{'):
                try:
                    import json
                    parsed = json.loads(val)
                    if isinstance(parsed, dict):
                        return int(parsed.get('intValue', 0) or 0)
                except (json.JSONDecodeError, ValueError):
                    pass
            # Try direct int conversion
            try:
                return int(val)
            except ValueError:
                return 0
        if isinstance(val, dict):
            # OTEL sometimes stores as {"intValue": 123}
            return int(val.get('intValue', 0) or 0)
        return 0

    # Calculate metrics from observations - only count GENERATION type to avoid double-counting
    total_input_tokens = 0
    total_output_tokens = 0
    total_cache_read_tokens = 0
    total_cache_write_tokens = 0
    total_cost = 0.0

    for obs in observations:
        obs_type = getattr(obs, 'type', None)
        # Only count GENERATION observations to avoid double-counting with spans
        if obs_type != 'GENERATION':
            continue

        usage = getattr(obs, 'usage', None) or {}
        metadata = getattr(obs, 'metadata', None) or {}

        # Extract from usage dict
        if isinstance(usage, dict):
            inp = safe_int(usage.get('input') or usage.get('promptTokens') or usage.get('input_tokens'))
            out = safe_int(usage.get('output') or usage.get('completionTokens') or usage.get('output_tokens'))
            # Cache metrics - check multiple possible locations
            cache_read = safe_int(
                usage.get('cache_read_input_tokens') or
                usage.get('cacheReadInputTokens') or
                usage.get('cacheRead')
            )
            cache_write = safe_int(
                usage.get('cache_creation_input_tokens') or
                usage.get('cacheWriteInputTokens') or
                usage.get('cacheCreationInputTokens') or
                usage.get('cacheWrite')
            )
        else:
            inp = safe_int(getattr(usage, 'input', None) or getattr(usage, 'prompt_tokens', None))
            out = safe_int(getattr(usage, 'output', None) or getattr(usage, 'completion_tokens', None))
            cache_read = safe_int(getattr(usage, 'cache_read_input_tokens', None))
            cache_write = safe_int(getattr(usage, 'cache_creation_input_tokens', None))

        # Check metadata['attributes'] for OTEL gen_ai attributes
        if isinstance(metadata, dict):
            attrs = metadata.get('attributes', {})
            if isinstance(attrs, dict):
                if cache_read == 0:
                    cache_read = safe_int(attrs.get('gen_ai.usage.cache_read_input_tokens'))
                if cache_write == 0:
                    cache_write = safe_int(
                        attrs.get('gen_ai.usage.cache_creation_input_tokens') or
                        attrs.get('gen_ai.usage.cache_write_input_tokens')
                    )

        total_input_tokens += inp
        total_output_tokens += out
        total_cache_read_tokens += cache_read
        total_cache_write_tokens += cache_write

        cost = getattr(obs, 'calculated_total_cost', None) or getattr(obs, 'calculatedTotalCost', 0) or 0
        total_cost += float(cost) if cost else 0.0

    # Get latency from trace
    latency_seconds = getattr(latest_trace, 'latency', None)

    langfuse.shutdown()

    return {
        "trace_id": trace_id,
        "trace_name": getattr(latest_trace, 'name', 'unknown'),
        "latency_seconds": latency_seconds,
        "cost_usd": total_cost,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens,
        "cache_read_tokens": total_cache_read_tokens,
        "cache_write_tokens": total_cache_write_tokens,
        "langfuse_url": f"{host}/trace/{trace_id}",
    }


def print_metrics(metrics: dict, test_name: str = "") -> None:
    """Pretty print metrics from get_latest_trace_metrics."""
    host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

    print("\n" + "=" * 60)
    print("                    LANGFUSE METRICS")
    print("=" * 60)

    if test_name:
        print(f"  Test:          {test_name}")

    if "error" in metrics:
        print(f"  Status:        ERROR")
        print(f"  Message:       {metrics['error']}")
        print("-" * 60)
        print(f"  Dashboard:     {host}")
    else:
        print(f"  Trace ID:      {metrics['trace_id']}")
        print("-" * 60)
        if metrics.get('latency_seconds') is not None:
            print(f"  Latency:       {metrics['latency_seconds']:.2f}s")
        else:
            print(f"  Latency:       N/A")
        print(f"  Cost:          ${metrics.get('cost_usd', 0):.6f}")
        print(f"  Input tokens:  {metrics.get('input_tokens', 0):,}")
        print(f"  Output tokens: {metrics.get('output_tokens', 0):,}")
        print(f"  Total tokens:  {metrics.get('total_tokens', 0):,}")
        print("-" * 60)
        print(f"  Cache read tokens:   {metrics.get('cache_read_tokens', 0):,}")
        print(f"  Cache write tokens:  {metrics.get('cache_write_tokens', 0):,}")
        print("-" * 60)
        print(f"  View trace:    {metrics.get('langfuse_url', host)}")

    print("=" * 60 + "\n")
