# Plan: LLM Optimization Phase 1 - Foundation Implementation

**Status**: ✅ COMPLETED - Implementation plan ready
**Date**: 2025-11-28

---

## Quick Navigation

This planning prompt has been completed and comprehensive documentation created.

**Start here**:
- 📖 [README.md](./README.md) - Overview and navigation guide
- 📋 [SUMMARY.md](./SUMMARY.md) - Executive summary (5 min read)
- 📘 [llm-optimization-phase1-plan.md](./llm-optimization-phase1-plan.md) - Full implementation plan (30 min read)
- 🏗️ [ARCHITECTURE.md](./ARCHITECTURE.md) - Architecture diagrams and flows (15 min read)

---

## Original Planning Prompt

<objective>
Create a detailed implementation plan for Phase 1 (Week 1 - Foundation) of the LLM Batch API & Prompt Caching optimization project. This plan will guide the development of the core optimization wrapper module with zero breaking changes to existing functionality.

Phase 1 deliverable: A tested, production-ready optimization wrapper that can be deployed (disabled by default) without affecting any existing PipesHub functionality.
</objective>

<context>
## Research Foundation

Based on completed research: @.prompts/005-llm-batch-caching-abstraction-research/

**Key Decisions Made** (assumptions - verify with user):
- Architecture: Decorator pattern
- Provider scope: Anthropic Claude initially
- Default mode: Disabled by default (opt-in)
- Batch accumulation: 100 docs OR 30 seconds (hybrid)
- Cache TTL: 5 min default, 1 hour for domains
- Failure handling: Retry individually up to 3x

## Current PipesHub Architecture

**Relevant Files** (from codebase analysis):
- `/app/utils/aimodels.py` - LLM factory with `get_generator_model()`
- `/app/services/aiconfig/aiconfig_service.py` - Configuration service
- `/app/services/indexing/` - Indexing pipeline that calls LLMs
- `/app/services/retrieval/` - Retrieval service for domain extraction

**Technology Stack**:
- Python 3.11+
- LangChain for LLM abstraction
- ArangoDB for configuration storage
- Kafka for async message processing

## Phase 1 Scope

**In Scope**:
- Create optimization wrapper module
- Implement provider capability detection
- Add basic batch API support (Anthropic only)
- Add basic prompt caching support (Anthropic only)
- Write comprehensive unit tests
- Deploy to dev (disabled by default)
- Verify backward compatibility

**Out of Scope** (later phases):
- OpenAI/Gemini provider support
- Production rollout
- Kafka batch accumulation
- Monitoring dashboard
- Cost tracking integration
</context>

<requirements>

## Plan Structure

Create a hierarchical plan with the following structure:

### 1. Pre-Implementation Setup
- Development environment configuration
- Dependencies and library installations
- Test environment setup
- Code structure decisions

### 2. Core Module Development

#### 2.1 Provider Capability Detection
**File**: `/app/utils/llm_optimization/capabilities.py`

Tasks:
- Define provider enum with capabilities
- Implement detection for Anthropic batch API
- Implement detection for Anthropic prompt caching
- Add fallback logic for unknown providers

Deliverables:
- `ProviderCapabilities` class
- Unit tests with 90%+ coverage
- Documentation strings

#### 2.2 Optimization Wrapper
**File**: `/app/utils/llm_optimization/wrapper.py`

Tasks:
- Create `OptimizedLLMWrapper` class extending `BaseChatModel`
- Implement `ainvoke()` with cache marker injection
- Implement `abatch()` with batch API routing
- Add configuration parsing
- Implement graceful fallback on errors

Deliverables:
- `OptimizedLLMWrapper` class
- Cache marker injection logic
- Batch API integration
- Error handling with fallback
- Unit tests with 85%+ coverage

#### 2.3 Batch API Client
**File**: `/app/utils/llm_optimization/batch_client.py`

Tasks:
- Implement Anthropic Batch API client
- Add batch submission logic
- Add batch status polling
- Add result retrieval
- Handle batch failures with retry

Deliverables:
- `AnthropicBatchClient` class
- Async batch operations
- Retry logic (up to 3 attempts)
- Unit tests with mocked API calls

#### 2.4 Cache Manager
**File**: `/app/utils/llm_optimization/cache.py`

Tasks:
- Implement cache marker injection for Anthropic
- Add TTL configuration
- Implement cache breakpoint detection
- Add cache key generation

Deliverables:
- `CacheManager` class
- Cache marker formatting
- TTL handling
- Unit tests

### 3. Factory Integration

#### 3.1 Update aimodels.py
**File**: `/app/utils/aimodels.py`

Tasks:
- Add import for optimization wrapper
- Modify `get_generator_model()` to optionally wrap models
- Add configuration flag check
- Ensure backward compatibility (disabled by default)

Deliverables:
- Updated factory function
- Configuration flag handling
- Backward compatibility verification
- Integration tests

### 4. Configuration Schema

#### 4.1 ArangoDB Schema Update
**Collection**: `aiconfigs`

Tasks:
- Design optimization configuration schema
- Add migration script
- Set safe defaults (all optimizations disabled)
- Document configuration options

Deliverables:
- Schema definition
- Migration script
- Configuration documentation

### 5. Testing Strategy

#### 5.1 Unit Tests
Tasks:
- Test each module independently
- Mock external API calls
- Test error conditions
- Test fallback behavior
- Target 85%+ coverage

#### 5.2 Integration Tests
Tasks:
- Test wrapper with real LangChain models
- Test factory integration
- Test configuration loading
- Verify no side effects on existing code

#### 5.3 Backward Compatibility Tests
Tasks:
- Run existing test suite
- Verify all existing tests pass
- Test with optimization disabled (default)
- Test with optimization enabled

### 6. Documentation

Tasks:
- Module documentation (docstrings)
- Configuration guide
- Architecture decision records
- Code examples

### 7. Deployment to Dev

Tasks:
- Deploy to dev environment
- Verify service starts successfully
- Run smoke tests
- Monitor logs for errors
- Confirm backward compatibility

</requirements>

<output>
Save comprehensive implementation plan to: `.prompts/006-llm-optimization-phase1-plan/llm-optimization-phase1-plan.md`

## Plan Document Structure

### Executive Summary
- Phase 1 objectives
- Key deliverables
- Success criteria
- Timeline estimate (1 week)

### Architecture Overview
- Module structure diagram (ASCII)
- Class relationships
- Integration points
- Data flow

### Task Breakdown

For each major component:

**Component Name**: [e.g., Provider Capability Detection]

**Files**:
- Primary: `/path/to/file.py`
- Tests: `/path/to/test_file.py`
- Docs: `/path/to/docs.md`

**Dependencies**:
- External libraries
- Internal modules
- Configuration requirements

**Tasks** (numbered, with time estimates):
1. [Task 1] - 2h
2. [Task 2] - 3h
3. [Task 3] - 1h

**Acceptance Criteria**:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Testing Requirements**:
- Unit tests: [specific test cases]
- Integration tests: [scenarios to test]
- Coverage target: [percentage]

**Risks & Mitigations**:
- Risk: [description] → Mitigation: [approach]

### Implementation Sequence

**Day 1**: [Tasks for day 1]
**Day 2**: [Tasks for day 2]
**Day 3**: [Tasks for day 3]
**Day 4**: [Tasks for day 4]
**Day 5**: [Tasks for day 5]

### Quality Gates

Checkpoints before proceeding:
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Backward compatibility verified
- [ ] Code review completed
- [ ] Documentation updated

### Rollback Plan

If issues detected:
- Steps to disable optimization
- Steps to revert changes
- Data recovery (if applicable)

### Success Metrics

How to verify Phase 1 is complete:
- ✅ Module deployed to dev
- ✅ All tests passing (>85% coverage)
- ✅ Backward compatibility confirmed
- ✅ Configuration schema updated
- ✅ Documentation complete
- ✅ No production impact (disabled by default)

Create SUMMARY.md with:
- **One-liner**: What Phase 1 delivers
- **Key Deliverables**: List of files/features created
- **Decisions Needed**: Any open decisions before implementation
- **Blockers**: Any dependencies or prerequisites
- **Next Step**: First concrete task to start Phase 1

<metadata>
- `<confidence>`: High/Medium based on research completeness
- `<dependencies>`: Research findings, dev environment access, stakeholder decisions
- `<open_questions>`: Any unknowns about implementation approach
- `<assumptions>`: Technology choices, architecture decisions
</metadata>
</output>

<verification>
Before finalizing, verify:
- [ ] All research findings incorporated
- [ ] Dependencies on research document explicit
- [ ] Tasks are concrete and actionable
- [ ] Time estimates are realistic
- [ ] Success criteria are measurable
- [ ] Rollback plan is clear
- [ ] No breaking changes introduced
- [ ] Testing strategy is comprehensive
</verification>

<success_criteria>
- Clear task breakdown with time estimates
- Concrete deliverables for each component
- Testing requirements specified
- Integration points identified
- Backward compatibility ensured
- Rollback plan defined
- Success metrics measurable
- Ready to assign to developer and start implementation
</success_criteria>
