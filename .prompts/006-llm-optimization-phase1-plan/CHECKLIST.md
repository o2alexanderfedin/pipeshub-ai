# Phase 1 Implementation Checklist

**Project**: LLM Optimization - Batch API & Prompt Caching
**Phase**: 1 of 5 (Foundation)
**Duration**: 5 working days
**Status**: Ready to Start

---

## Pre-Implementation (2 hours)

### Stakeholder Approvals
- [ ] Architecture design approved
- [ ] Timeline approved (1 week)
- [ ] Success criteria agreed upon
- [ ] Resources assigned (1 developer)

### Critical Decisions Made
- [ ] **Decision 1**: Batch accumulation strategy
  - Options: Time-based, count-based, hybrid
  - Decision: _______________
- [ ] **Decision 2**: Default cache TTL
  - Options: 5 min, 1 hour, configurable
  - Decision: _______________
- [ ] **Decision 3**: Phase 1 provider scope
  - Options: Anthropic only, or Anthropic + others
  - Decision: _______________

### Environment Setup
- [ ] Feature branch created: `feature/llm-batch-caching-phase1`
- [ ] Development environment configured
- [ ] Python 3.11+ verified
- [ ] Anthropic API key configured in dev environment
  ```bash
  export ANTHROPIC_API_KEY="sk-ant-..."
  ```
- [ ] Dependencies installed
  ```bash
  pip install anthropic>=0.40.0
  pip install pytest pytest-cov pytest-asyncio pytest-mock
  ```
- [ ] ArangoDB access verified
- [ ] Database backup created
  ```bash
  arango dump --database es --output-directory /backup/pre-phase1-$(date +%Y%m%d)
  ```

---

## Day 1: Foundation (6-8 hours)

### Module Structure Creation
- [ ] Created directory: `backend/python/app/utils/llm_optimization/`
- [ ] Created directory: `backend/python/app/utils/llm_optimization/tests/`
- [ ] Created: `__init__.py` (public API exports)
- [ ] Created: `capabilities.py`
- [ ] Created: `config.py`
- [ ] Created: `exceptions.py`
- [ ] Created: `tests/conftest.py` (pytest fixtures)

### Component 1: Provider Capabilities (6 hours)

**Implementation** (`capabilities.py`):
- [ ] Defined `ProviderCapabilities` dataclass
- [ ] Implemented `detect()` static method
- [ ] Mapped all 14 LLM providers:
  - [ ] Anthropic (batch + cache)
  - [ ] OpenAI (batch + cache)
  - [ ] Gemini (batch + cache)
  - [ ] AWS Bedrock (batch + cache via Claude)
  - [ ] Azure OpenAI (batch + cache)
  - [ ] Cohere (no optimization)
  - [ ] Fireworks (no optimization)
  - [ ] Groq (no optimization)
  - [ ] Mistral (no optimization)
  - [ ] Ollama (no optimization)
  - [ ] Together (no optimization)
  - [ ] Vertex AI (via Gemini)
  - [ ] xAI (no optimization)
  - [ ] OpenAI Compatible (depends on provider)
- [ ] Defined batch limits for each provider
- [ ] Defined cache marker types (explicit vs automatic)

**Testing** (`tests/test_capabilities.py`):
- [ ] Test: `test_anthropic_capabilities()` - Batch + cache support verified
- [ ] Test: `test_openai_capabilities()` - Batch + cache support verified
- [ ] Test: `test_gemini_capabilities()` - Batch + cache support verified
- [ ] Test: `test_ollama_capabilities()` - No optimization verified
- [ ] Test: `test_unknown_provider()` - Graceful degradation verified
- [ ] Test coverage: ≥95%
- [ ] All tests passing

**Documentation**:
- [ ] Docstrings complete for all public methods
- [ ] Examples added to docstrings
- [ ] Type hints complete

**Code Review Checkpoint**:
- [ ] Code reviewed by senior developer
- [ ] Feedback addressed
- [ ] Committed to feature branch

---

## Day 2: Batch API Integration (8 hours)

### Component 2: Batch API Client (8 hours)

**Implementation** (`batch_client.py`):
- [ ] Created `AnthropicBatchClient` class
- [ ] Implemented `__init__(capabilities, config)`
- [ ] Implemented `process_batch(messages_list)` - Main entry point
- [ ] Implemented `submit_batch(messages_list)` - JSONL formatting + API call
- [ ] Implemented `poll_until_complete(batch_id)` - Exponential backoff polling
- [ ] Implemented `get_results(batch_id)` - Result retrieval and parsing
- [ ] Implemented `_format_messages()` - LangChain to Anthropic format
- [ ] Error handling for batch failures
- [ ] Retry logic (up to 3 attempts)

**Testing** (`tests/test_batch_client.py`):
- [ ] Test: `test_submit_batch()` - JSONL format correct
- [ ] Test: `test_poll_status_in_progress()` - Continues polling
- [ ] Test: `test_poll_status_completed()` - Returns when done
- [ ] Test: `test_poll_status_failed()` - Handles batch failure
- [ ] Test: `test_get_results()` - Parses results correctly
- [ ] Test: `test_partial_failures()` - Handles mixed success/failure
- [ ] Test: `test_exponential_backoff()` - Polling intervals correct
- [ ] All tests passing with mocked API
- [ ] Test coverage: ≥85%

**Integration Testing** (dev environment only):
- [ ] Test: `test_real_batch_submission()` - End-to-end with Anthropic API
- [ ] Verified batch submission works
- [ ] Verified polling works
- [ ] Verified result retrieval works
- [ ] Verified cost savings (50% discount confirmed)

**Code Review Checkpoint**:
- [ ] Code reviewed
- [ ] Integration test results reviewed
- [ ] Committed to feature branch

---

## Day 3: Prompt Caching (6-7 hours)

### Component 3: Cache Manager (6-7 hours)

**Implementation** (`cache_manager.py`):
- [ ] Created `CacheManager` class
- [ ] Implemented `__init__(capabilities, config)`
- [ ] Implemented `add_cache_markers(messages)` - Main entry point
- [ ] Implemented `_add_anthropic_cache_markers(messages)` - Anthropic-specific
- [ ] Implemented `_should_cache_message(msg, index, total)` - Auto-detection
- [ ] Auto-detection logic:
  - [ ] System prompts cached
  - [ ] Long messages (>1024 tokens) cached
  - [ ] First user message cached
  - [ ] Manual `[CACHE_BREAKPOINT]` markers supported
- [ ] TTL configuration support
- [ ] Cache marker formatting (Anthropic `cache_control` blocks)

**Testing** (`tests/test_cache_manager.py`):
- [ ] Test: `test_add_cache_markers_anthropic()` - Correct format
- [ ] Test: `test_cache_ttl_configuration()` - TTL parsing works
- [ ] Test: `test_auto_detect_system_prompt()` - System messages cached
- [ ] Test: `test_auto_detect_long_content()` - Long content cached
- [ ] Test: `test_auto_detect_first_message()` - First message cached
- [ ] Test: `test_manual_breakpoints()` - Manual markers work
- [ ] Test: `test_no_markers_when_disabled()` - Respects config
- [ ] Test: `test_openai_automatic_caching()` - No markers for OpenAI
- [ ] All tests passing
- [ ] Test coverage: ≥90%

**Integration Testing** (dev environment):
- [ ] Test: `test_cache_with_real_api()` - Verify actual caching
- [ ] Verified cache markers accepted by API
- [ ] Verified cache hit on second request
- [ ] Verified cost savings (90% discount on cached tokens)
- [ ] Measured cache hit rate in test scenario

**Code Review Checkpoint**:
- [ ] Code reviewed
- [ ] Integration test results reviewed
- [ ] Committed to feature branch

---

## Day 4: Wrapper & Integration (8 hours)

### Component 4: Configuration Models (1 hour)

**Implementation** (`config.py`):
- [ ] Created `OptimizationConfig` dataclass
- [ ] Fields defined:
  - [ ] `optimization_enabled: bool`
  - [ ] `batching_enabled: bool`
  - [ ] `batch_max_size: int`
  - [ ] `batch_timeout: int`
  - [ ] `caching_enabled: bool`
  - [ ] `cache_ttl: int`
  - [ ] `cache_breakpoints: str`
  - [ ] `fallback_to_standard: bool`
- [ ] Implemented `from_dict(config)` - Parse from ArangoDB config
- [ ] Implemented `validate()` - Validate configuration values
- [ ] Default values set

**Testing** (`tests/test_config.py`):
- [ ] Test: `test_config_from_dict()` - Parsing works
- [ ] Test: `test_config_validation()` - Validation works
- [ ] Test: `test_config_defaults()` - Defaults applied
- [ ] Test: `test_invalid_config()` - Errors raised for invalid values

### Component 5: Optimization Wrapper (5 hours)

**Implementation** (`wrapper.py`):
- [ ] Created `OptimizedLLMWrapper(BaseChatModel)` class
- [ ] Implemented `__init__(base_model, provider, config)`
- [ ] Initialized:
  - [ ] `self.base_model`
  - [ ] `self.provider`
  - [ ] `self.config = OptimizationConfig.from_dict(config)`
  - [ ] `self.capabilities = ProviderCapabilities.detect(provider)`
  - [ ] `self.cache_manager = CacheManager(...)`
  - [ ] `self.batch_client = AnthropicBatchClient(...)` (if supported)
- [ ] Implemented `ainvoke(messages, **kwargs)`:
  - [ ] Check if caching enabled
  - [ ] Add cache markers via cache_manager
  - [ ] Call base_model.ainvoke()
  - [ ] Error handling with fallback
- [ ] Implemented `abatch(messages_list, **kwargs)`:
  - [ ] Check if batching enabled
  - [ ] Route to batch_client if enabled
  - [ ] Fallback to base_model.abatch() if disabled
  - [ ] Error handling with individual retry
- [ ] Implemented `_retry_individually(messages_list)`:
  - [ ] Retry each message individually
  - [ ] Handle individual failures
  - [ ] Return results list
- [ ] Implemented pass-through methods:
  - [ ] `_identifying_params` property
  - [ ] `_llm_type` property
  - [ ] Other BaseChatModel methods

**Testing** (`tests/test_wrapper.py`):
- [ ] Test: `test_wrapper_initialization()` - Config parsed, capabilities detected
- [ ] Test: `test_ainvoke_with_cache_enabled()` - Cache markers injected
- [ ] Test: `test_ainvoke_with_cache_disabled()` - No cache markers
- [ ] Test: `test_abatch_with_batching_enabled()` - Routes to batch client
- [ ] Test: `test_abatch_with_batching_disabled()` - Uses base model
- [ ] Test: `test_fallback_on_batch_error()` - Retries individually
- [ ] Test: `test_fallback_on_cache_error()` - Falls back to standard
- [ ] Test: `test_pass_through_methods()` - Delegates correctly
- [ ] Test: `test_wrapper_preserves_identity()` - Base model identity preserved
- [ ] All tests passing
- [ ] Test coverage: ≥85%

### Component 6: Factory Integration (2 hours)

**Implementation** (`aimodels.py` updates):
- [ ] Extracted existing logic to `_create_base_model(provider, configuration, model_name)`
- [ ] Updated `get_generator_model()`:
  - [ ] Call `_create_base_model()` to get base model
  - [ ] Check `configuration.get("optimizationEnabled", False)`
  - [ ] If enabled, import `OptimizedLLMWrapper`
  - [ ] Wrap base model: `OptimizedLLMWrapper(base_model, provider, configuration)`
  - [ ] Return wrapped or base model
- [ ] Added logging for optimization enable/disable
- [ ] Error handling (fallback to base model if wrapper fails)

**Testing** (`tests/test_aimodels_integration.py` - new file):
- [ ] Test: `test_get_generator_model_optimization_disabled()` - Default behavior
- [ ] Test: `test_get_generator_model_optimization_enabled()` - Wrapped
- [ ] Test: `test_all_providers_backward_compatible()` - All 14 providers work
- [ ] Test: `test_wrapper_applied_for_supported_providers()` - Only supported providers wrapped
- [ ] Test: `test_configuration_parsing()` - Config correctly parsed
- [ ] All tests passing

**Regression Testing**:
- [ ] Run full existing test suite: `pytest backend/python/app/`
- [ ] All existing tests pass (100%)
- [ ] No performance regression measured
- [ ] No new errors in logs

**Code Review Checkpoint**:
- [ ] Code reviewed
- [ ] All tests reviewed
- [ ] Regression test results reviewed
- [ ] Committed to feature branch

---

## Day 5: Deployment & Verification (6-8 hours)

### Component 7: Configuration Schema (3 hours)

**Migration Script** (`migrations/add_llm_optimization_config.py`):
- [ ] Created migration script
- [ ] Defined optimization defaults:
  - [ ] `optimizationEnabled: false`
  - [ ] `batchingEnabled: false`
  - [ ] `cachingEnabled: false`
  - [ ] `cacheTTL: 300`
  - [ ] `batchMaxSize: 10000`
  - [ ] `batchTimeout: 30`
  - [ ] `fallbackToStandard: true`
- [ ] Implemented migration logic:
  - [ ] Connect to ArangoDB
  - [ ] Fetch all `aiconfigs` documents
  - [ ] For each LLM config, add optimization fields
  - [ ] Preserve existing configuration
  - [ ] Update documents
- [ ] Added rollback logic
- [ ] Added validation

**Testing** (dev environment):
- [ ] Test: Migration adds fields correctly
- [ ] Test: Existing configuration preserved
- [ ] Test: Safe defaults applied
- [ ] Backup created before migration
- [ ] Migration executed successfully in dev
- [ ] Configuration accessible via ConfigurationService
- [ ] Verified: All optimizations disabled by default

### Deployment to Dev (2 hours)

**Pre-Deployment**:
- [ ] All unit tests passing (≥85% coverage)
- [ ] All integration tests passing
- [ ] All regression tests passing (100% existing tests)
- [ ] Code review completed and approved
- [ ] Database backup created
- [ ] Rollback plan documented and tested

**Deployment Steps**:
- [ ] Merged feature branch to `develop`
- [ ] Pulled latest code on dev server
- [ ] Ran migration script
- [ ] Built Docker images: `docker-compose build backend`
- [ ] Deployed services: `docker-compose up -d`
- [ ] Verified services started: `docker-compose ps`
- [ ] Checked logs for errors: `docker-compose logs backend | grep -i error`

**Smoke Tests** (1 hour):
- [ ] Test 1: Service health check - `/health` endpoint responds
- [ ] Test 2: LLM call works (optimization disabled) - Standard flow works
- [ ] Test 3: Configuration accessible - Can retrieve LLM config via API
- [ ] Test 4: No performance regression - Response times unchanged
- [ ] Test 5: No errors in logs - Clean logs for 15 minutes
- [ ] Test 6: Can enable optimization - Config update works
- [ ] Test 7: Optimization works when enabled - Cache markers present (if enabled for test)

### Backward Compatibility Verification (1 hour)

**Verification Tests**:
- [ ] Test existing retrieval service - Works unchanged
- [ ] Test existing chat/QnA - Works unchanged
- [ ] Test existing indexing pipeline - Works unchanged
- [ ] Test all 14 LLM providers - All work
- [ ] Test configuration changes - Hot reload works
- [ ] Performance benchmarks - No degradation
- [ ] Memory usage - No increase
- [ ] CPU usage - No increase

### Documentation (1 hour)

**Documentation Completed**:
- [ ] Architecture documentation - `ARCHITECTURE.md` ✅
- [ ] Implementation plan - `llm-optimization-phase1-plan.md` ✅
- [ ] Summary - `SUMMARY.md` ✅
- [ ] README - `README.md` ✅
- [ ] Inline code documentation - Docstrings complete
- [ ] Configuration guide - Usage examples in docs
- [ ] Migration guide - How to run migration
- [ ] Rollback procedures - Documented and tested

### Final Code Review (1 hour)

**Review Items**:
- [ ] Code quality - SOLID principles followed
- [ ] Test coverage - ≥85% achieved
- [ ] Error handling - Comprehensive
- [ ] Logging - Appropriate
- [ ] Security - No secrets in code, secure API calls
- [ ] Performance - <1ms wrapper overhead
- [ ] Documentation - Complete
- [ ] Backward compatibility - 100% verified

**Approval**:
- [ ] Senior developer approval
- [ ] Tech lead approval
- [ ] Final commit to `develop`

---

## Success Criteria Verification

### Technical Success
- [ ] ✅ All 7 module files created and tested
- [ ] ✅ Unit tests passing with ≥85% coverage
  - Measured coverage: _____%
- [ ] ✅ Integration tests passing with real Anthropic API
  - Batch API test: PASS
  - Prompt caching test: PASS
  - Cache hit rate measured: _____%
- [ ] ✅ All existing tests still passing (backward compatibility)
  - Total existing tests: _____
  - Passing: _____ (100%)
- [ ] ✅ Performance benchmarks met
  - Wrapper overhead measured: _____ms (<1ms target)

### Deployment Success
- [ ] ✅ Code deployed to dev environment
  - Deployment date/time: _____________
- [ ] ✅ Migration executed successfully
  - Migration completed without errors
  - Configuration verified
- [ ] ✅ Services start without errors
  - All containers running
  - No errors in logs
- [ ] ✅ Optimizations disabled by default verified
  - Checked configuration: `optimizationEnabled: false`
  - Standard flow working

### Quality Success
- [ ] ✅ Code review completed and approved
  - Reviewer: _____________
  - Approval date: _____________
- [ ] ✅ Documentation complete
  - All 4 docs created and reviewed
- [ ] ✅ Rollback plan tested
  - Rollback test: PASS
  - Restore from backup: PASS
- [ ] ✅ Zero production impact confirmed
  - No existing functionality affected
  - No performance regression
  - No errors introduced

---

## Phase 1 Completion Sign-Off

**Completion Date**: _____________

**Sign-Offs**:
- [ ] Developer: _____________ (Date: _____)
- [ ] Senior Developer / Code Reviewer: _____________ (Date: _____)
- [ ] Tech Lead: _____________ (Date: _____)
- [ ] Product Owner: _____________ (Date: _____)

**Ready for Phase 2**: ⏳

---

## Notes & Lessons Learned

**Blockers Encountered**:
-

**Issues Resolved**:
-

**Performance Measurements**:
- Wrapper overhead: _____ms
- Cache hit rate (test): _____%
- Test coverage achieved: _____%

**Deviations from Plan**:
-

**Recommendations for Phase 2**:
-

---

**Next Phase**: Phase 2 - Testing & Validation
- Enable optimizations in dev environment
- Test with real workloads
- Measure actual cost savings
- Validate cache hit rates
- Fine-tune configuration

---

**End of Checklist**
