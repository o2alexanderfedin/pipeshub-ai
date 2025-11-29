# Migration Guide

Guide for integrating LLM optimization into existing PipesHub AI codebase.

## Overview

This guide shows how to add LLM cost optimization to existing code with **zero breaking changes**.

## Migration Strategy

### ✅ Recommended: Gradual Rollout

1. **Dev Environment**: Enable for development/testing
2. **Staging**: Enable for single service
3. **Production**: Gradual rollout by service
4. **Monitor**: Track costs and performance

### ❌ Not Recommended: Big Bang

- Don't enable everywhere at once
- Don't skip testing phase
- Don't modify existing code unnecessarily

## Step-by-Step Migration

### Step 1: Add Configuration (ArangoDB)

Add `optimization` field to existing AI model configurations:

```json
// Example: Update anthropic_config document
{
    "_key": "anthropic_config",
    "provider": "anthropic",
    "isDefault": true,
    "configuration": {
        "apiKey": "sk-ant-...",
        "model": "claude-sonnet-4-5-20250929"
    },
    // NEW: Add optimization configuration
    "optimization": {
        "cache": {
            "enabled": false,  // Start disabled!
            "min_tokens_to_cache": 1024,
            "auto_detect_cacheable": true,
            "default_ttl_seconds": 300
        },
        "fallback": {
            "enabled": true,
            "log_failures": true
        },
        "provider": "anthropic"
    }
}
```

### Step 2: Update Model Creation

#### Before (Existing Code)

```python
from app.utils.aimodels import get_generator_model

class IndexingService:
    def __init__(self, config):
        # Existing model creation
        self.model = get_generator_model(
            provider="anthropic",
            config=config,
            model_name="claude-sonnet-4-5-20250929"
        )

    def index_content(self, content):
        messages = [
            {"role": "system", "content": "Extract key information..."},
            {"role": "user", "content": content}
        ]
        return self.model.invoke(messages)
```

#### After (With Optimization)

```python
from app.utils.aimodels import get_generator_model
from app.utils.llm_optimization.wrapper import OptimizedLLMWrapper
from app.utils.llm_optimization.config import OptimizationConfig

class IndexingService:
    def __init__(self, config):
        # Create base model (unchanged)
        base_model = get_generator_model(
            provider="anthropic",
            config=config,
            model_name="claude-sonnet-4-5-20250929"
        )

        # NEW: Wrap with optimization if configured
        if "optimization" in config:
            opt_config = OptimizationConfig.from_dict(config["optimization"])
            self.model = OptimizedLLMWrapper(base_model, opt_config)
        else:
            self.model = base_model  # Fallback to base model

    def index_content(self, content):
        # Unchanged! Code works exactly the same
        messages = [
            {"role": "system", "content": "Extract key information..."},
            {"role": "user", "content": content}
        ]
        return self.model.invoke(messages)  # Transparent optimization
```

### Step 3: Enable Optimization (When Ready)

Update ArangoDB configuration to enable:

```json
{
    "optimization": {
        "cache": {
            "enabled": true  // Changed from false → true
        }
    }
}
```

**That's it!** No code changes needed. Optimization applies automatically.

## Common Migration Patterns

### Pattern 1: Service-Level Wrapper

```python
# services/ai_service.py

class AIService:
    def __init__(self):
        self.models = {}

    def get_model(self, provider: str, model_name: str):
        """Get or create optimized model."""
        key = f"{provider}:{model_name}"

        if key not in self.models:
            # Load config from ArangoDB
            config = self._load_config(provider)

            # Create base model
            base_model = get_generator_model(provider, config, model_name)

            # Apply optimization if configured
            if config.get("optimization"):
                opt_config = OptimizationConfig.from_dict(config["optimization"])
                self.models[key] = OptimizedLLMWrapper(base_model, opt_config)
            else:
                self.models[key] = base_model

        return self.models[key]

    def _load_config(self, provider: str):
        """Load configuration from ArangoDB."""
        # Your existing config loading logic
        pass
```

### Pattern 2: Factory Enhancement

Enhance `app/utils/aimodels.py` factory:

```python
# app/utils/aimodels.py

def get_generator_model(
    provider: str,
    config: Dict[str, Any],
    model_name: str | None = None,
    enable_optimization: bool = True,  # NEW optional parameter
) -> BaseChatModel:
    """
    Get generator model with optional optimization.

    Args:
        provider: Provider name
        config: Configuration dict (may include 'optimization' key)
        model_name: Optional model name
        enable_optimization: Whether to apply optimization wrapper

    Returns:
        BaseChatModel or OptimizedLLMWrapper
    """
    # Existing model creation logic
    configuration = config['configuration']
    # ... create base_model ...

    # NEW: Apply optimization if enabled and configured
    if enable_optimization and "optimization" in config:
        from app.utils.llm_optimization.wrapper import OptimizedLLMWrapper
        from app.utils.llm_optimization.config import OptimizationConfig

        try:
            opt_config = OptimizationConfig.from_dict(config["optimization"])
            return OptimizedLLMWrapper(base_model, opt_config)
        except Exception as e:
            logger.warning(f"Failed to apply optimization: {e}")
            return base_model  # Fallback to base model

    return base_model
```

Usage:

```python
# Automatically applies optimization if configured
model = get_generator_model("anthropic", config)

# Explicitly disable optimization
model = get_generator_model("anthropic", config, enable_optimization=False)
```

### Pattern 3: Repository Pattern

```python
# repositories/llm_repository.py

class LLMRepository:
    def __init__(self, db_connection):
        self.db = db_connection
        self._models_cache = {}

    def get_model(self, provider: str, purpose: str = "general"):
        """Get optimized model for specific purpose."""
        cache_key = f"{provider}:{purpose}"

        if cache_key in self._models_cache:
            return self._models_cache[cache_key]

        # Load purpose-specific configuration
        config = self._get_config_for_purpose(provider, purpose)

        # Create and cache model
        base_model = get_generator_model(provider, config)

        if config.get("optimization"):
            opt_config = OptimizationConfig.from_dict(config["optimization"])

            # Purpose-specific optimization tuning
            if purpose == "indexing":
                # Indexing benefits from caching domain definitions
                opt_config.cache.domain_definitions_ttl_seconds = 3600

            model = OptimizedLLMWrapper(base_model, opt_config)
        else:
            model = base_model

        self._models_cache[cache_key] = model
        return model
```

## Testing Your Migration

### 1. Unit Tests

```python
import pytest
from unittest.mock import Mock, patch

def test_service_with_optimization():
    """Test service works with optimization enabled."""
    config = {
        "provider": "anthropic",
        "configuration": {"apiKey": "test"},
        "optimization": {
            "cache": {"enabled": True},
            "provider": "anthropic"
        }
    }

    service = IndexingService(config)

    # Should be wrapped
    assert isinstance(service.model, OptimizedLLMWrapper)

    # Should work the same
    with patch.object(service.model.base_model, 'invoke') as mock_invoke:
        mock_invoke.return_value = "Response"
        result = service.index_content("Test content")
        assert result == "Response"


def test_service_without_optimization():
    """Test service works without optimization."""
    config = {
        "provider": "anthropic",
        "configuration": {"apiKey": "test"},
        # No optimization key
    }

    service = IndexingService(config)

    # Should NOT be wrapped
    assert not isinstance(service.model, OptimizedLLMWrapper)
```

### 2. Integration Tests

```python
def test_end_to_end_with_caching():
    """Test full workflow with caching enabled."""
    # Load real config from test DB
    config = load_test_config("anthropic_optimized")

    # Create service
    service = IndexingService(config)

    # First request - creates cache
    response1 = service.index_content("Test document")
    stats1 = service.model.get_cache_stats()

    # Second request - uses cache
    response2 = service.index_content("Another document")
    stats2 = service.model.get_cache_stats()

    # Verify caching working
    assert stats2.cached_blocks >= stats1.cached_blocks
```

### 3. Smoke Tests

```bash
# Test in development
pytest app/services/tests/test_indexing_service.py -v

# Verify no regressions
pytest app/ -k "llm or model or generation" -v
```

## Monitoring Post-Migration

### 1. Log Monitoring

Look for optimization-related logs:

```python
# Check logs for these patterns:
# - "Cache optimization enabled for provider: anthropic"
# - "Cache optimization failed, falling back to standard API"
# - "Cache optimization requested but not supported by provider"
```

### 2. Statistics Collection

Add monitoring endpoints:

```python
# endpoints/monitoring.py

@app.get("/api/monitoring/llm-optimization")
async def get_optimization_stats():
    """Get LLM optimization statistics."""
    # Collect stats from all services
    stats = {}

    for service_name, service in get_all_services():
        if hasattr(service, 'model') and isinstance(service.model, OptimizedLLMWrapper):
            service_stats = service.model.get_cache_stats()
            stats[service_name] = {
                "total_blocks": service_stats.total_content_blocks,
                "cached_blocks": service_stats.cached_blocks,
                "estimated_tokens": service_stats.estimated_cached_tokens,
                "hit_rate": f"{service_stats.cache_hit_potential:.1%}",
                "is_optimized": service.model.is_optimized,
            }

    return stats
```

### 3. Cost Tracking

Monitor API costs in your billing dashboard:

**Before Migration**:
- Establish baseline costs
- Note average tokens/request
- Calculate daily/monthly spend

**After Migration**:
- Compare costs week-over-week
- Verify expected savings (up to 90%)
- Monitor for unexpected increases

## Rollback Plan

If issues occur, rollback is simple:

### Option 1: Disable via Configuration

```json
// Update ArangoDB configuration
{
    "optimization": {
        "cache": {
            "enabled": false  // Disable optimization
        }
    }
}
```

### Option 2: Conditional Wrapper

```python
# Add feature flag
USE_OPTIMIZATION = os.getenv("LLM_OPTIMIZATION_ENABLED", "false").lower() == "true"

if USE_OPTIMIZATION and "optimization" in config:
    model = OptimizedLLMWrapper(base_model, opt_config)
else:
    model = base_model
```

### Option 3: Code Rollback

Simply remove the wrapper - your original code still works:

```python
# Rollback: Remove wrapper lines
# self.model = OptimizedLLMWrapper(base_model, opt_config)

# Back to original
self.model = base_model
```

## Troubleshooting Migration Issues

### Issue: Tests Failing

**Symptom**: Tests that mock LLM calls are failing

**Solution**: Update mocks to handle wrapper:

```python
# Before
mock_model = Mock()

# After
mock_model = Mock(spec=BaseChatModel)  # Or actual model class
```

### Issue: Type Errors

**Symptom**: Type checker complaining about wrapper

**Solution**: Use `BaseChatModel` type hint:

```python
from langchain.chat_models.base import BaseChatModel

class MyService:
    def __init__(self):
        self.model: BaseChatModel = self._create_model()  # Works with wrapper!
```

### Issue: Unexpected Behavior

**Symptom**: Responses different after migration

**Steps**:
1. Check if caching is accidentally enabled
2. Verify configuration loaded correctly
3. Test with optimization disabled
4. Check logs for fallback messages
5. Compare request/response logs

### Issue: Performance Degradation

**Symptom**: Slower response times

**Possible Causes**:
1. Deep copy overhead (minimal, but check)
2. Statistics collection overhead (minimal)
3. Cache marker injection (minimal)

**Investigation**:
```python
import time

start = time.time()
response = model.invoke(messages)
duration = time.time() - start

print(f"Request took {duration:.3f}s")
```

## Checklist

Before migrating a service:

- [ ] Add `optimization` configuration to ArangoDB
- [ ] Start with `enabled: false`
- [ ] Update service to conditionally wrap models
- [ ] Write/update unit tests
- [ ] Write/update integration tests
- [ ] Test in development environment
- [ ] Monitor logs for warnings/errors
- [ ] Enable optimization (`enabled: true`)
- [ ] Monitor costs for 24-48 hours
- [ ] Verify expected savings
- [ ] Document any issues encountered
- [ ] Move to next service

## Support

Questions during migration?

1. Check README.md for usage examples
2. Review test files for patterns
3. Check module docstrings
4. Test in isolated environment first

---

**Remember**: The wrapper is designed for **zero breaking changes**. If your existing code breaks, something is wrong with the migration - not the wrapper!
