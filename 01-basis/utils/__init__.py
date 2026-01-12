"""
Utility functions for prompt caching workshops.
"""

from .cache_metrics import (
    extract_cache_metrics,
    print_cache_metrics,
    calculate_cache_savings
)

from .pricing import (
    PRICING,
    OUTPUT_BURNDOWN_RATE,
    calculate_cost,
    calculate_actual_cost,
    compare_optimization,
    calculate_tpm_reservation,
    calculate_tpm_actual,
    print_pricing_table
)

__all__ = [
    # Cache metrics
    'extract_cache_metrics',
    'print_cache_metrics',
    'calculate_cache_savings',
    # Pricing
    'PRICING',
    'OUTPUT_BURNDOWN_RATE',
    'calculate_cost',
    'calculate_actual_cost',
    'compare_optimization',
    'calculate_tpm_reservation',
    'calculate_tpm_actual',
    'print_pricing_table'
]
