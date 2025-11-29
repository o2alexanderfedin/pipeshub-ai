"""
LLM Optimization Module

Provides batch API and prompt caching optimizations for LLM providers
while maintaining backward compatibility and provider-agnostic interface.

This module implements the Decorator pattern to wrap LangChain models
with cost optimization features (Batch API, Prompt Caching) without
modifying existing code.
"""

from app.utils.llm_optimization.capabilities import ProviderCapabilities
from app.utils.llm_optimization.config import OptimizationConfig
from app.utils.llm_optimization.exceptions import (
    OptimizationError,
    BatchAPIError,
    CacheError,
    ConfigurationError,
)

__all__ = [
    "ProviderCapabilities",
    "OptimizationConfig",
    "OptimizationError",
    "BatchAPIError",
    "CacheError",
    "ConfigurationError",
]

__version__ = "0.1.0"
