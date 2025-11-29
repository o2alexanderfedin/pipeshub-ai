# LLM Optimization Phase 1 - Architecture Overview

**Quick visual reference for the optimization module architecture**

---

## Module Structure

```
backend/python/app/utils/llm_optimization/
│
├── __init__.py                     # Public API
│   └── exports: OptimizedLLMWrapper, ProviderCapabilities
│
├── capabilities.py                 # Provider capability detection
│   ├── ProviderCapabilities (dataclass)
│   ├── detect(provider, model) -> ProviderCapabilities
│   └── Maps all 14 LLM providers to their optimization features
│
├── wrapper.py                      # Main optimization wrapper
│   └── OptimizedLLMWrapper(BaseChatModel)
│       ├── __init__(base_model, provider, config)
│       ├── ainvoke(messages) -> response
│       ├── abatch(messages_list) -> responses
│       └── _retry_individually(messages_list) -> responses
│
├── batch_client.py                 # Batch API client
│   └── AnthropicBatchClient
│       ├── process_batch(messages_list) -> results
│       ├── submit_batch(messages_list) -> batch_id
│       ├── poll_until_complete(batch_id) -> None
│       └── get_results(batch_id) -> results
│
├── cache_manager.py                # Prompt caching logic
│   └── CacheManager
│       ├── add_cache_markers(messages) -> marked_messages
│       ├── _add_anthropic_cache_markers(messages)
│       └── _should_cache_message(msg, index, total) -> bool
│
├── config.py                       # Configuration models
│   └── OptimizationConfig (dataclass)
│       ├── from_dict(config) -> OptimizationConfig
│       └── validate() -> bool
│
├── exceptions.py                   # Custom exceptions
│   ├── OptimizationError
│   ├── BatchError
│   └── CacheError
│
└── tests/                          # Test suite
    ├── test_capabilities.py        # Unit tests for capabilities
    ├── test_wrapper.py             # Unit tests for wrapper
    ├── test_batch_client.py        # Unit tests for batch client
    ├── test_cache_manager.py       # Unit tests for cache manager
    ├── test_config.py              # Unit tests for config
    └── integration/
        ├── test_wrapper_integration.py
        ├── test_batch_api_integration.py
        └── test_backward_compatibility.py
```

---

## Class Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    LangChain BaseChatModel                        │
│  (Interface from langchain.chat_models.base)                     │
│                                                                   │
│  + ainvoke(messages, **kwargs) -> response                       │
│  + abatch(messages_list, **kwargs) -> responses                  │
│  + _generate(...) -> result                                      │
│  + _agenerate(...) -> result                                     │
│  + _identifying_params: Dict                                     │
│  + _llm_type: str                                                │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             │ inherits
                             │
                             ↓
┌──────────────────────────────────────────────────────────────────┐
│              OptimizedLLMWrapper (wrapper.py)                     │
│  Wraps any LangChain model with batch/cache optimizations        │
│                                                                   │
│  Fields:                                                          │
│  - base_model: BaseChatModel                                     │
│  - provider: str                                                 │
│  - config: OptimizationConfig                                    │
│  - capabilities: ProviderCapabilities                            │
│  - batch_client: Optional[BatchClient]                           │
│  - cache_manager: CacheManager                                   │
│                                                                   │
│  Methods:                                                         │
│  + ainvoke(messages) -> response                                 │
│    └─> cache_manager.add_cache_markers(messages)                │
│    └─> base_model.ainvoke(marked_messages)                      │
│                                                                   │
│  + abatch(messages_list) -> responses                            │
│    └─> if batching_enabled:                                     │
│        └─> batch_client.process_batch(messages_list)            │
│    └─> else:                                                     │
│        └─> base_model.abatch(messages_list)                     │
│                                                                   │
│  + _retry_individually(messages_list) -> responses               │
│    └─> for each message: ainvoke(message)                       │
└────────────┬──────────────┬──────────────┬────────────────────────┘
             │              │              │
             │ uses         │ uses         │ uses
             ↓              ↓              ↓
┌────────────────┐  ┌──────────────┐  ┌──────────────────┐
│ProviderCapabili│  │ BatchClient  │  │  CacheManager    │
│ties             │  │              │  │                  │
│(capabilities.py)│  │(batch_client)│  │(cache_manager.py)│
│                 │  │              │  │                  │
│Fields:          │  │Fields:       │  │Fields:           │
│- provider: str  │  │- client:     │  │- capabilities    │
│- supports_batch │  │  AsyncAnthro │  │- config          │
│- supports_cache │  │  pic         │  │- default_ttl     │
│- batch_max_req  │  │- config      │  │                  │
│- cache_ttl_def  │  │- max_retries │  │Methods:          │
│- cache_marker   │  │              │  │+ add_cache_      │
│  _type          │  │Methods:      │  │  markers()       │
│                 │  │+ process_    │  │+ _should_cache   │
│Methods:         │  │  batch()     │  │  _message()      │
│+ detect(        │  │+ submit_     │  │+ _add_anthropic  │
│  provider,      │  │  batch()     │  │  _cache_markers()│
│  model)         │  │+ poll_until_ │  │                  │
│                 │  │  complete()  │  │                  │
│                 │  │+ get_results│  │                  │
│                 │  │  ()          │  │                  │
└─────────────────┘  └──────────────┘  └──────────────────┘
         ↑                   ↑                   ↑
         │                   │                   │
         │ reads             │ reads             │ reads
         └───────────────────┴───────────────────┘
                             │
                   ┌─────────┴──────────┐
                   │ OptimizationConfig │
                   │    (config.py)     │
                   │                    │
                   │ Fields:            │
                   │ - batching_enabled │
                   │ - batch_max_size   │
                   │ - batch_timeout    │
                   │ - caching_enabled  │
                   │ - cache_ttl        │
                   │ - fallback_to_std  │
                   │                    │
                   │ Methods:           │
                   │ + from_dict(dict)  │
                   │ + validate()       │
                   └────────────────────┘
```

---

## Request Flow Diagrams

### 1. Standard Request (Optimization Disabled)

```
┌─────────────┐
│ User Code   │
│ (retrieval_ │
│  service)   │
└──────┬──────┘
       │
       │ llm = get_generator_model(provider, config)
       │ (optimizationEnabled: false)
       ↓
┌──────────────────────────────────────────┐
│  get_generator_model() (aimodels.py)     │
│  - Check: optimizationEnabled == false   │
│  - Return: ChatAnthropic (base model)    │
└──────┬───────────────────────────────────┘
       │
       │ return ChatAnthropic
       ↓
┌──────────────┐
│ User Code    │
│ response =   │
│ llm.ainvoke()│
└──────┬───────┘
       │
       │ ainvoke(messages)
       ↓
┌──────────────────────┐
│  ChatAnthropic       │
│  (LangChain native)  │
└──────┬───────────────┘
       │
       │ HTTP POST /v1/messages
       ↓
┌──────────────────┐
│  Anthropic API   │
│  (Standard)      │
└──────┬───────────┘
       │
       │ Response
       ↓
┌─────────────┐
│ User Code   │
│ (result)    │
└─────────────┘

Flow: User → Factory → Base Model → API → Response
Time: ~1-2s (standard API latency)
Cost: Full price ($3/M input, $15/M output)
```

---

### 2. Optimized Request with Caching (Enabled)

```
┌─────────────┐
│ User Code   │
└──────┬──────┘
       │
       │ llm = get_generator_model(provider, config)
       │ (optimizationEnabled: true, cachingEnabled: true)
       ↓
┌──────────────────────────────────────────────┐
│  get_generator_model() (aimodels.py)         │
│  - Check: optimizationEnabled == true        │
│  - Create: ChatAnthropic (base)              │
│  - Wrap: OptimizedLLMWrapper(base, ...)      │
│  - Return: OptimizedLLMWrapper               │
└──────┬───────────────────────────────────────┘
       │
       │ return OptimizedLLMWrapper
       ↓
┌──────────────┐
│ User Code    │
│ response =   │
│ llm.ainvoke()│
└──────┬───────┘
       │
       │ ainvoke(messages)
       ↓
┌───────────────────────────────────────────────┐
│  OptimizedLLMWrapper.ainvoke()                │
│                                               │
│  1. Check: cachingEnabled? Yes                │
│  2. Call: cache_manager.add_cache_markers()   │
└──────┬────────────────────────────────────────┘
       │
       │ add_cache_markers(messages)
       ↓
┌───────────────────────────────────────────────┐
│  CacheManager.add_cache_markers()             │
│                                               │
│  1. Detect cacheable content:                 │
│     - System prompts                          │
│     - Long messages (>1024 tokens)            │
│     - First user message                      │
│  2. Add cache_control blocks:                 │
│     {                                         │
│       "type": "text",                         │
│       "text": "...",                          │
│       "cache_control": {"type": "ephemeral"}  │
│     }                                         │
│  3. Return: marked_messages                   │
└──────┬────────────────────────────────────────┘
       │
       │ return marked_messages
       ↓
┌───────────────────────────────────────────────┐
│  OptimizedLLMWrapper.ainvoke() (continued)    │
│                                               │
│  3. Call: base_model.ainvoke(marked_messages) │
└──────┬────────────────────────────────────────┘
       │
       │ ainvoke(marked_messages)
       ↓
┌──────────────────────────────┐
│  ChatAnthropic.ainvoke()     │
│  (passes through marked msgs)│
└──────┬───────────────────────┘
       │
       │ HTTP POST /v1/messages
       │ (with cache_control blocks)
       ↓
┌───────────────────────────────────────────┐
│  Anthropic API                            │
│                                           │
│  1. Check cache for marked content        │
│  2. Cache hit? Use cached (90% discount)  │
│  3. Cache miss? Process & cache           │
│  4. Return response                       │
└──────┬────────────────────────────────────┘
       │
       │ Response
       ↓
┌─────────────┐
│ User Code   │
│ (result)    │
└─────────────┘

Flow: User → Factory → Wrapper → Cache Manager → Base Model → API → Response
Time: ~1-2s (same latency, caching on API side)
Cost: 90% cheaper on cached tokens ($0.30/M vs $3/M)
```

---

### 3. Batch Request (Batching Enabled)

```
┌─────────────────────┐
│ User Code           │
│ (Kafka handler      │
│  processing 100     │
│  documents)         │
└──────┬──────────────┘
       │
       │ llm = get_generator_model(provider, config)
       │ (batchingEnabled: true)
       ↓
┌──────────────────────────────────────────────┐
│  get_generator_model()                       │
│  - Returns: OptimizedLLMWrapper              │
└──────┬───────────────────────────────────────┘
       │
       │ return wrapper
       ↓
┌──────────────────┐
│ User Code        │
│ responses =      │
│ llm.abatch(      │
│   [msg1, msg2,   │
│    ..., msg100]) │
└──────┬───────────┘
       │
       │ abatch(messages_list)
       ↓
┌────────────────────────────────────────────────┐
│  OptimizedLLMWrapper.abatch()                  │
│                                                │
│  1. Check: batchingEnabled? Yes                │
│  2. Check: batch_client exists? Yes            │
│  3. Call: batch_client.process_batch()         │
└──────┬─────────────────────────────────────────┘
       │
       │ process_batch(messages_list)
       ↓
┌────────────────────────────────────────────────┐
│  AnthropicBatchClient.process_batch()          │
│                                                │
│  Step 1: Submit Batch                          │
│  ├─> Format requests as JSONL                  │
│  ├─> Call: client.batches.create()             │
│  └─> Get: batch_id                             │
│                                                │
│  Step 2: Poll Status                           │
│  ├─> Loop: client.batches.retrieve(batch_id)   │
│  ├─> Check: processing_status                  │
│  ├─> Wait with exponential backoff             │
│  │    (1s → 2s → 4s → ... → 60s max)           │
│  └─> Exit when: status == "ended"              │
│                                                │
│  Step 3: Get Results                           │
│  ├─> Download results JSONL                    │
│  ├─> Parse results                             │
│  ├─> Map back to original order                │
│  └─> Return: results                           │
└──────┬─────────────────────────────────────────┘
       │
       │ Timeline:
       │ T+0s: Submit batch
       │ T+1s: Poll (in_progress)
       │ T+3s: Poll (in_progress)
       │ T+7s: Poll (in_progress)
       │ ...
       │ T+5min: Poll (ended)
       │ T+5min: Retrieve results
       ↓
┌─────────────────┐
│ Anthropic API   │
│                 │
│ Batch Queue:    │
│ ┌─────────────┐ │
│ │ Request 1   │ │
│ │ Request 2   │ │
│ │ ...         │ │
│ │ Request 100 │ │
│ └─────────────┘ │
│                 │
│ Processing:     │
│ - Parallel      │
│ - Low priority  │
│ - 24h window    │
│                 │
│ Results:        │
│ ┌─────────────┐ │
│ │ Response 1  │ │
│ │ Response 2  │ │
│ │ ...         │ │
│ │ Response100 │ │
│ └─────────────┘ │
└────┬────────────┘
     │
     │ Results ready
     ↓
┌─────────────────┐
│ User Code       │
│ (results)       │
└─────────────────┘

Flow: User → Wrapper → Batch Client → Submit → Poll → Retrieve → Results
Time: 5 minutes to 24 hours (async, non-urgent workloads)
Cost: 50% cheaper ($1.50/M input, $7.50/M output)
```

---

### 4. Error Handling Flow (Fallback)

```
┌──────────────┐
│ User Code    │
└──────┬───────┘
       │
       │ llm.abatch(messages_list)
       ↓
┌────────────────────────────────────┐
│  OptimizedLLMWrapper.abatch()      │
│                                    │
│  Try: batch_client.process_batch() │
└──────┬─────────────────────────────┘
       │
       │ process_batch() raises BatchError
       ↓
┌────────────────────────────────────────────┐
│  Exception Handler                         │
│                                            │
│  1. Catch: BatchError                      │
│  2. Log: "Batch failed, retrying..."       │
│  3. Check: fallbackToStandard? Yes         │
│  4. Call: _retry_individually()            │
└──────┬─────────────────────────────────────┘
       │
       │ _retry_individually(messages_list)
       ↓
┌────────────────────────────────────────────┐
│  OptimizedLLMWrapper._retry_individually() │
│                                            │
│  For each message in messages_list:        │
│    Try:                                    │
│      result = ainvoke(message)             │
│      results.append(result)                │
│    Except:                                 │
│      results.append(None)                  │
│      log_error()                           │
│                                            │
│  Return: results                           │
└──────┬─────────────────────────────────────┘
       │
       │ ainvoke() for each message
       ↓
┌──────────────────────┐
│  ChatAnthropic       │
│  (Standard API)      │
└──────┬───────────────┘
       │
       │ Individual API calls
       ↓
┌──────────────────┐
│  Anthropic API   │
│  (Standard)      │
└──────┬───────────┘
       │
       │ Responses
       ↓
┌─────────────┐
│ User Code   │
│ (results)   │
└─────────────┘

Fallback Strategy:
1. Batch fails → Retry individually
2. Individual fails → Retry up to 3x
3. Still fails → Return None or raise (based on config)

Guarantee: No silent failures, always get result or clear error
```

---

## Integration Points

### Factory Integration (aimodels.py)

```
Before Phase 1:
┌────────────────────────────────────┐
│ get_generator_model(provider, cfg) │
│                                    │
│ if provider == "anthropic":        │
│   return ChatAnthropic(...)        │
│ elif provider == "openAI":         │
│   return ChatOpenAI(...)           │
│ ...                                │
└────────────────────────────────────┘
                │
                ↓
        ┌───────────────┐
        │ ChatAnthropic │
        │ (base model)  │
        └───────────────┘

After Phase 1:
┌────────────────────────────────────────────────┐
│ get_generator_model(provider, cfg)             │
│                                                │
│ base_model = _create_base_model(provider, cfg) │
│                                                │
│ if cfg.get("optimizationEnabled", False):     │
│   return OptimizedLLMWrapper(                  │
│     base_model, provider, cfg                  │
│   )                                            │
│ return base_model                              │
└────────────────────────────────────────────────┘
                │
                ├─────────────┬──────────────┐
                │             │              │
         optimization    optimization    optimization
         disabled        enabled          enabled
                │             │              │
                ↓             ↓              ↓
        ┌───────────┐  ┌──────────────────────────┐
        │ChatAnthro │  │OptimizedLLMWrapper       │
        │pic        │  │  wraps: ChatAnthropic    │
        │(native)   │  │  adds: batch + cache     │
        └───────────┘  └──────────────────────────┘
```

---

## Configuration Flow

```
┌───────────────────────────────────────────────────────┐
│            ArangoDB (aiconfigs collection)            │
│                                                       │
│ {                                                     │
│   "llm": [{                                           │
│     "provider": "anthropic",                          │
│     "configuration": {                                │
│       "model": "claude-sonnet-4-5",                   │
│       "apiKey": "${ANTHROPIC_API_KEY}",               │
│       "optimizationEnabled": false,  ← Master switch  │
│       "batchingEnabled": false,                       │
│       "cachingEnabled": false,                        │
│       "cacheTTL": 300,                                │
│       "fallbackToStandard": true                      │
│     }                                                 │
│   }]                                                  │
│ }                                                     │
└───────────────┬───────────────────────────────────────┘
                │
                │ ConfigurationService.get_config()
                ↓
┌───────────────────────────────────────────────────────┐
│           RetrievalService.get_llm_instance()         │
│                                                       │
│ ai_models = await config_service.get_config(...)     │
│ llm_config = ai_models["llm"][0]                      │
│                                                       │
│ llm = get_generator_model(                            │
│   provider=llm_config["provider"],                    │
│   config=llm_config                                   │
│ )                                                     │
└───────────────┬───────────────────────────────────────┘
                │
                │ get_generator_model()
                ↓
┌───────────────────────────────────────────────────────┐
│                  aimodels.py                          │
│                                                       │
│ config = cfg["configuration"]                         │
│                                                       │
│ if config.get("optimizationEnabled", False):          │
│   # Parse optimization settings                       │
│   opt_config = OptimizationConfig.from_dict(config)   │
│                                                       │
│   # Wrap base model                                   │
│   return OptimizedLLMWrapper(                         │
│     base_model, provider, opt_config                  │
│   )                                                   │
└───────────────────────────────────────────────────────┘

Configuration Hierarchy:
1. ArangoDB → 2. ConfigService → 3. Factory → 4. Wrapper

Default Behavior:
- optimizationEnabled: false → No wrapper, base model only
- optimizationEnabled: true → Wrapper applied with sub-features
```

---

## Testing Strategy Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Testing Pyramid                        │
│                                                             │
│                        ┌───────┐                            │
│                        │  E2E  │  ← Manual/Smoke (5%)       │
│                        │ Tests │                            │
│                        └───────┘                            │
│                    ┌───────────────┐                        │
│                    │  Integration  │  ← Real APIs (15%)     │
│                    │     Tests     │                        │
│                    └───────────────┘                        │
│              ┌─────────────────────────┐                    │
│              │     Unit Tests          │  ← Mocked (80%)    │
│              │  (85%+ coverage)        │                    │
│              └─────────────────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Test Organization:

Unit Tests (80% of test effort):
├── test_capabilities.py          ← Provider detection
├── test_config.py                ← Config parsing
├── test_cache_manager.py         ← Cache marker injection
├── test_batch_client.py          ← Batch API (mocked)
└── test_wrapper.py               ← Wrapper logic

Integration Tests (15% of test effort):
├── test_wrapper_integration.py   ← Real LangChain models
├── test_batch_api_integration.py ← Real Anthropic Batch API
└── test_backward_compatibility.py ← Full test suite regression

E2E Tests (5% of test effort):
└── Manual smoke tests in dev environment

Quality Gates:
✓ Unit tests: 85%+ coverage
✓ Integration tests: All pass
✓ Backward compat: 100% existing tests pass
✓ Performance: <1ms wrapper overhead
```

---

## Deployment Strategy

```
┌─────────────────────────────────────────────────────────┐
│                   Phase 1 Deployment                    │
│                 (Safe, Gradual, Reversible)             │
└─────────────────────────────────────────────────────────┘

Step 1: Pre-Deployment
┌────────────────────────────┐
│ 1. Create DB Backup        │
│ 2. Run All Tests           │
│ 3. Code Review Approval    │
│ 4. Merge to develop        │
└────────────┬───────────────┘
             │
             ↓
Step 2: Database Migration
┌────────────────────────────┐
│ 1. Run migration script    │
│ 2. Add optimization fields │
│ 3. Verify schema           │
│ 4. All disabled by default │
└────────────┬───────────────┘
             │
             ↓
Step 3: Code Deployment
┌────────────────────────────┐
│ 1. Deploy to dev           │
│ 2. docker-compose build    │
│ 3. docker-compose up -d    │
│ 4. Check logs (no errors)  │
└────────────┬───────────────┘
             │
             ↓
Step 4: Smoke Tests
┌────────────────────────────┐
│ 1. Service starts?         │
│ 2. LLM calls work?         │
│ 3. No performance impact?  │
│ 4. Logs clean?             │
└────────────┬───────────────┘
             │
             ↓
Step 5: Verification
┌────────────────────────────┐
│ 1. Backward compat OK?     │
│ 2. Config accessible?      │
│ 3. Wrapper can be enabled? │
│ 4. Rollback tested?        │
└────────────┬───────────────┘
             │
             ↓
Phase 1 Complete ✓
(Ready for Phase 2 - Testing)

Rollback Plan:
Any Step Fails → Immediate Rollback
├─ Code revert: git revert + redeploy
├─ Config disable: optimizationEnabled = false
└─ DB restore: arango restore --backup
```

---

## Performance Characteristics

```
┌──────────────────────────────────────────────────────────┐
│           Wrapper Performance Overhead                   │
└──────────────────────────────────────────────────────────┘

Optimization Disabled (Default):
┌────────────┐
│ User Code  │
└─────┬──────┘
      │ <1ms (minimal factory overhead)
      ↓
┌────────────┐
│Base Model  │
└─────┬──────┘
      │ ~1-2s (API latency, unchanged)
      ↓
┌────────────┐
│   Result   │
└────────────┘
Total: Same as before (no performance impact)

Optimization Enabled (Caching):
┌────────────┐
│ User Code  │
└─────┬──────┘
      │ <1ms (wrapper creation)
      ↓
┌────────────┐
│  Wrapper   │
└─────┬──────┘
      │ <1ms (cache marker injection)
      ↓
┌────────────┐
│Base Model  │
└─────┬──────┘
      │ ~1-2s (API latency, same)
      ↓
┌────────────┐
│   Result   │
└────────────┘
Total: ~1-2s + 1-2ms overhead (<0.1% increase)

Optimization Enabled (Batching):
┌────────────┐
│ User Code  │
└─────┬──────┘
      │ <1ms (wrapper creation)
      ↓
┌────────────┐
│  Wrapper   │
└─────┬──────┘
      │ <1ms (batch submission)
      ↓
┌────────────┐
│Batch Client│
└─────┬──────┘
      │ 5min-24h (async processing)
      ↓
┌────────────┐
│  Results   │
└────────────┘
Total: 5min-24h (acceptable for non-urgent workloads)

Performance Targets:
✓ Wrapper overhead: <1ms
✓ Cache injection: <1ms
✓ No impact on API latency
✓ Batch acceptable: 5min-24h for bulk workloads
```

---

## Security Considerations

```
┌──────────────────────────────────────────────────────────┐
│                  Security Architecture                   │
└──────────────────────────────────────────────────────────┘

API Key Handling:
┌────────────────────────────┐
│ Environment Variables      │
│ ANTHROPIC_API_KEY=sk-...   │
└────────┬───────────────────┘
         │ Loaded at startup
         ↓
┌────────────────────────────┐
│ ArangoDB Configuration     │
│ (encrypted at rest)        │
└────────┬───────────────────┘
         │ Retrieved on demand
         ↓
┌────────────────────────────┐
│ OptimizedLLMWrapper        │
│ (memory only, not logged)  │
└────────┬───────────────────┘
         │ Passed to API client
         ↓
┌────────────────────────────┐
│ Anthropic SDK              │
│ (HTTPS only)               │
└────────────────────────────┘

Data Flow Security:
✓ API keys never logged
✓ Messages not persisted in wrapper
✓ HTTPS for all API communication
✓ No PII in error messages
✓ Batch results deleted after retrieval

Threat Model:
┌────────────────────┬──────────────┬─────────────────┐
│ Threat             │ Probability  │ Mitigation      │
├────────────────────┼──────────────┼─────────────────┤
│ API key leak       │ Low          │ Env vars, logs  │
│ Message interception│ Low         │ HTTPS only      │
│ Batch result leak  │ Low          │ Auto-delete     │
│ Config injection   │ Medium       │ Schema validate │
└────────────────────┴──────────────┴─────────────────┘

Compliance:
✓ No additional PII collection
✓ No data retention changes
✓ Same security posture as base LangChain models
```

---

**End of Architecture Overview**

For more details, see:
- Full implementation plan: `llm-optimization-phase1-plan.md`
- Summary: `SUMMARY.md`
