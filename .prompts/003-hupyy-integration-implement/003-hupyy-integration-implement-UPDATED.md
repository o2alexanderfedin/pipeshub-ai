<objective>
Implement the Hupyy SMT verification integration into PipesHub following the UPDATED 4-phase fast-track plan.

Execute each phase incrementally with TDD (Test-Driven Development), creating tests before implementation, and verifying success criteria at each stage.

**CRITICAL CONSTRAINTS (User-provided):**
- Hupyy verification takes 1-2 minutes per call (very slow!)
- Must be async and parallel (don't block UX)
- UI checkbox to enable/disable Hupyy
- Progress indicators required (show verification status)
- Metadata display on click
- enrich=false always
- Chunk large inputs (<10KB per chunk)
- Top-5 to top-10 sampling max
- Simple caching implementation
- NOT in production yet (skip shadow mode delays, canary rollout)
</objective>

<context>
Research findings: .prompts/001-hupyy-integration-research/hupyy-integration-research.md
Updated plan: .prompts/002-hupyy-integration-plan/SUMMARY-UPDATED.md

PipesHub codebase:
- Backend: backend/python/app/, backend/nodejs/apps/
- Frontend: frontend/src/
- Deployment: deployment/docker-compose/

Project conventions: /Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/CLAUDE.md

**Timeline: 11 weeks (4 phases)**
- Phase 0: Infrastructure (Week 1)
- Phase 1: Hupyy Service + UI (Weeks 2-4)
- Phase 2: Orchestrator + Feedback (Weeks 5-7)
- Phase 3: Ranking + PageRank (Weeks 8-10)
- Phase 4: Polish (Week 11)
</context>

<implementation_requirements>
For each phase:

## 1. Test-Driven Development (TDD)
**CRITICAL: Write tests FIRST, then minimal code to pass, then refactor.**

For each deliverable:
1. Write failing unit test
2. Write minimal implementation
3. Write integration test
4. Refactor while keeping tests green
5. Code review (subtask)
6. Run linters (ESLint, Prettier, mypy, black, flake8)

## 2. Type Safety (MANDATORY)
- **Explicit types everywhere** - No `any`, use `unknown` with type guards
- **Interface definitions** - For all API contracts
- **Enum usage** - For verification verdicts (SAT/UNSAT/UNKNOWN)
- **Strict TypeScript/Python typing** - Enable all strict flags
- **Runtime validation** - Use zod (TypeScript) / pydantic (Python)

## 3. Phase-by-Phase Implementation

### Phase 0: Infrastructure Setup (Week 1)
**Deliverables:**
- Create Kafka topics: `verify_chunks`, `verification_complete`, `verification_failed`
- Feature flag system: MongoDB collection for feature flags
- Simple cache: Redis or in-memory dict with TTL
- Prometheus metrics: Basic counters, histograms
- Grafana dashboard: Verification health, query latency

**File Structure:**
```
backend/python/app/
  config/
    feature_flags.py         # Feature flag client
  infrastructure/
    kafka_setup.py           # Create topics
    cache.py                 # Simple cache implementation
    metrics.py               # Prometheus metrics
deployment/docker-compose/
  docker-compose.prod.yml    # Add Redis service
  grafana/
    dashboards/
      hupyy-verification.json
```

**Tests:**
- Unit: Feature flags, cache operations
- Integration: Kafka topic creation, Redis connection

---

### Phase 1: Hupyy Integration Service + UI (Weeks 2-4)

**Backend Deliverables:**

**File: backend/python/app/verification/hupyy_client.py**
- Async HTTP client (httpx)
- Circuit breaker implementation (5-failure threshold, 60s timeout)
- Input chunking logic (split >10KB inputs)
- Force enrich=false
- Simple caching (chunk_hash → result)
- Parallel async verification (asyncio.gather)

**File: backend/python/app/verification/models.py**
- Pydantic models for request/response
- Verification result schema
- Cache entry schema

**File: backend/python/app/verification/circuit_breaker.py**
- CircuitBreaker class (CLOSED/OPEN/HALF_OPEN states)
- Failure tracking, timeout logic

**Frontend Deliverables:**

**File: frontend/src/components/chat/HupyyControls.tsx**
- Checkbox component to enable/disable Hupyy
- Integrates with chat UI

**File: frontend/src/components/chat/VerificationProgress.tsx**
- Progress bar component (0-100%)
- WebSocket or polling for updates
- Toast notifications on completion

**File: frontend/src/components/chat/VerificationMetadata.tsx**
- Expandable metadata viewer
- Display SAT/UNSAT/UNKNOWN verdict
- Show confidence scores, formalization similarity

**File: frontend/src/hooks/useVerification.ts**
- React hook for verification state
- WebSocket connection management
- Progress updates

**Tests:**
- Unit: Circuit breaker state transitions, chunking logic, cache operations
- Integration: Full Hupyy API call with mocked 1-2 min delay
- UI: Component tests (React Testing Library)

---

### Phase 2: Verification Orchestrator + Feedback (Weeks 5-7)

**Deliverables:**

**File: backend/python/app/verification/orchestrator.py**
- Kafka consumer for verify_chunks
- Batch processing (5-10 chunks at a time)
- Parallel worker pool (asyncio)
- Produce to verification_complete/failed topics

**File: backend/python/app/feedback/qdrant_updater.py**
- Consume verification_complete events
- Update Qdrant payloads with verification scores
- Fast feedback tier (<100ms updates)

**File: backend/python/app/feedback/arangodb_updater.py**
- Consume verification_complete events
- Update ArangoDB documents with verification metrics
- Trigger PageRank recalculation

**File: backend/python/app/verification/cache_manager.py**
- Cache invalidation on source changes
- LRU eviction policy
- Cache hit/miss metrics

**File: backend/nodejs/apps/src/services/verification.service.ts**
- Trigger verification from search pipeline
- Top-5 to top-10 sampling logic
- Produce to verify_chunks topic

**Tests:**
- Unit: Orchestrator batch logic, cache invalidation
- Integration: Full Kafka flow (produce → consume → update DBs)
- Load: 10 parallel verifications, measure throughput

---

### Phase 3: Enhanced Ranking + PageRank (Weeks 8-10)

**Deliverables:**

**File: backend/python/app/ranking/enhanced_ranker.py**
- Integrate verification scores into ranking formula:
  ```python
  final_score = (
      0.45 * semantic_similarity +
      0.30 * pagerank_score +
      0.15 * verification_confidence +
      0.10 * historical_success
  ) * failure_mode_multiplier
  ```
- Gradual weight transition (0% → 15% over 1 week)
- Feature flag: `verification_ranking_weight` (0.0 to 0.15)

**File: backend/python/app/graph/pagerank_calculator.py**
- Modified PageRank for ArangoDB
- Citation network traversal
- Damping factor 0.85
- Convergence threshold 1e-6

**File: backend/python/app/graph/failure_mode_classifier.py**
- Classify UNKNOWN verdicts into failure modes
- Apply multipliers based on failure mode

**Tests:**
- Unit: Ranking formula, PageRank algorithm, failure mode classification
- Integration: End-to-end search with verification scores
- Validation: Measure Precision@5 on test set

---

### Phase 4: Polish + Documentation (Week 11)

**Deliverables:**
- Code review (subtask for all phases)
- Comprehensive linting (ESLint, Prettier, mypy, black, flake8)
- Documentation:
  - API docs (OpenAPI/Swagger)
  - Architecture diagrams (Mermaid)
  - Runbooks (operations guide)
  - README updates
- Git commit and push
- Final test coverage report (aim for 80%+)

---

## 4. File Organization (SOLID Principles)

Follow project structure:
```
backend/python/app/
  verification/
    __init__.py
    hupyy_client.py          # Hupyy API client
    orchestrator.py          # Verification orchestrator
    circuit_breaker.py       # Circuit breaker pattern
    models.py                # Pydantic models
    cache_manager.py         # Caching logic
  feedback/
    __init__.py
    qdrant_updater.py        # Update vector DB
    arangodb_updater.py      # Update knowledge graph
  ranking/
    __init__.py
    enhanced_ranker.py       # Integrate verification scores
  graph/
    __init__.py
    pagerank_calculator.py   # PageRank algorithm
    failure_mode_classifier.py
  tests/
    verification/
      test_hupyy_client.py
      test_orchestrator.py
      test_circuit_breaker.py
    feedback/
      test_qdrant_updater.py
      test_arangodb_updater.py
    ranking/
      test_enhanced_ranker.py

backend/nodejs/apps/src/
  services/
    verification.service.ts  # Trigger verification
  types/
    verification.types.ts    # TypeScript interfaces

frontend/src/
  components/
    chat/
      HupyyControls.tsx      # Enable/disable checkbox
      VerificationProgress.tsx
      VerificationMetadata.tsx
  hooks/
    useVerification.ts       # Verification state management
```

---

## 5. Error Handling (Critical for Slow API)

- **Never ignore errors**
- **Fail fast** with meaningful error messages
- **Retry strategies**: Exponential backoff (1s → 10s), max 3 retries
- **Circuit breaker**: Open after 5 failures, 60s timeout, neutral fallback (1.0x)
- **Timeouts**: 150s request timeout (1-2 min + buffer), 5s connection timeout
- **Graceful degradation**: Search works even if Hupyy fails

---

## 6. Configuration

**Environment Variables:**
```bash
HUPYY_API_URL=https://verticalslice-smt-service-gvav8.ondigitalocean.app
HUPYY_TIMEOUT_SECONDS=150
HUPYY_ENRICH=false  # Always false
VERIFICATION_ENABLED=false  # Feature flag
VERIFICATION_TOP_K=5  # Default sampling
CACHE_TTL_SECONDS=86400  # 24 hours
```

**MongoDB Feature Flags:**
```json
{
  "verification_enabled": false,
  "verification_ranking_weight": 0.0,
  "verification_top_k": 5
}
```

---

## 7. Monitoring & Observability

**Prometheus Metrics:**
- `hupyy_verification_requests_total` (counter)
- `hupyy_verification_duration_seconds` (histogram, p50/p95/p99)
- `hupyy_verification_success_rate` (gauge)
- `hupyy_circuit_breaker_state` (gauge: 0=closed, 1=open, 2=half-open)
- `cache_hit_rate` (gauge)
- `verification_queue_depth` (gauge)

**Grafana Dashboard:**
- Verification latency (p95, p99)
- Success/failure rate
- Circuit breaker state timeline
- Cache hit rate
- Kafka consumer lag

**Alerts:**
- CRITICAL: Circuit breaker open >10 min, success rate <30%
- WARNING: Latency p95 >180s, queue depth >100

---

## 8. Testing Strategy

**Unit Tests (80%+ coverage):**
- Mock Hupyy API responses (including 1-2 min delay simulation)
- Test circuit breaker state transitions
- Test chunking logic
- Test cache operations

**Integration Tests:**
- Full Kafka flow (produce → consume → update DBs)
- Hupyy API call with retry logic
- Database updates (Qdrant, ArangoDB)

**Load Tests:**
- 10 parallel verifications (measure throughput)
- 100 queries with verification enabled
- Cache performance under load

**UI Tests:**
- Component rendering (React Testing Library)
- Progress updates (mock WebSocket)
- Metadata display

---

## 9. Execution Strategy (Parallel Subtasks)

**Use parallel subtasks extensively:**

**Phase 0:**
- Subtask 1: Create Kafka topics
- Subtask 2: Setup feature flags
- Subtask 3: Implement cache
- Subtask 4: Setup monitoring
(All in parallel)

**Phase 1:**
- Subtask 1: Hupyy client (backend)
- Subtask 2: Circuit breaker (backend)
- Subtask 3: UI components (frontend)
- Subtask 4: WebSocket/polling (frontend)
(Backend and frontend in parallel)

**Phase 2:**
- Subtask 1: Orchestrator
- Subtask 2: Qdrant updater
- Subtask 3: ArangoDB updater
- Subtask 4: Cache manager
(All in parallel where possible)

**For maximum efficiency:**
- Spawn parallel subtasks for independent components
- Use map-reduce for repetitive tasks
- Each subtask reports back briefly
- If blocked, spawn additional subtasks for research

---

## 10. Output Specification

**Create implementation artifacts:**

1. **Code files** - Following project structure
2. **Test files** - Unit and integration tests (TDD)
3. **Configuration files** - Feature flags, env vars, docker-compose updates
4. **Documentation** - README updates, API docs, architecture diagrams

5. **SUMMARY.md** - Track progress:
   - **One-liner**: Current implementation status
   - **Version**: Update per phase (v1, v2, v3, v4)
   - **Key Findings**: What worked, what didn't
   - **Files Created**: List all new files
   - **Decisions Needed**: User input required
   - **Blockers**: External impediments
   - **Next Step**: Next phase or final verification

Save SUMMARY.md in: `.prompts/003-hupyy-integration-implement/SUMMARY.md`

---

## 11. Verification Per Phase

After each phase, verify:

□ All tests passing (unit + integration)
□ Linters passing (no warnings or errors)
□ Feature flag implemented and tested
□ Monitoring metrics collecting data
□ Documentation updated
□ Code reviewed by subtask
□ Success criteria from plan met
□ SUMMARY.md updated with phase completion
□ Git commit created with conventional commit message
□ Git push to repository

Only proceed to next phase when all checkboxes checked.

---

## 12. Final Verification (After Phase 4)

□ Full integration tests passing
□ Load tests meet performance targets
□ All linters clean
□ Test coverage ≥80%
□ All documentation complete
□ Monitoring dashboards operational
□ Feature flags working (can enable/disable)
□ UI components functional (checkbox, progress, metadata)
□ Precision@5 measured (target: 98%, acceptable if close)
□ SUMMARY.md shows final status

---

</implementation_requirements>

<constraints>
From CLAUDE.md:
- **SOLID, KISS, DRY, YAGNI, TRIZ principles**
- **TDD mandatory**: Tests before code
- **Strong typing**: No `any`, explicit types everywhere
- **Linting before commit**: Run all linters
- **Code review**: Separate subtask reviews changes
- **Git flow**: Commit and push after each phase
- **No database schema changes**: Verify before touching (we're adding optional fields only)
- **Parallel subtasks**: Maximize efficiency

**User Constraints:**
- Hupyy takes 1-2 minutes (adjust expectations)
- Async mandatory
- UI work required
- Top-5 to top-10 sampling
- Simple caching
- enrich=false always
</constraints>

<success_criteria>
- All 4 phases implemented with TDD
- All tests passing (unit, integration, load)
- Type safety enforced throughout
- Monitoring and observability complete
- Feature flags working
- UI components functional (checkbox, progress, metadata)
- Documentation comprehensive
- Code reviewed and linted
- Git commits follow conventions
- SUMMARY.md provides clear implementation status
- Precision@5 improvement demonstrated (target: 98%, acceptable if close)
</success_criteria>
