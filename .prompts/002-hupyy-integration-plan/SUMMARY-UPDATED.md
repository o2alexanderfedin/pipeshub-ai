# Hupyy-PipesHub Integration: Updated Executive Summary

## Critical Constraint Updates (2025-11-27)

### User Clarifications Applied:
1. **Hupyy Performance**: 1-2 minutes per verification (NOT 20-30s)
2. **Not in Production**: Skip shadow mode delays and canary rollout
3. **UI Requirements**: Checkbox to enable/disable, progress indicators, metadata display
4. **API Constraints**: enrich=false always, chunking for large inputs
5. **Caching**: Implement simple version
6. **Sampling**: Top-5 to top-10 max (NOT top-50)

---

## Revised Plan: 4-Phase Fast-Track Implementation

### Phase 0: Infrastructure Setup (Week 1)
**Duration:** 1 week
**Deliverables:**
- Kafka topics (verify_chunks, verification_complete, verification_failed)
- Feature flags (verification_enabled, in MongoDB)
- Basic monitoring (Prometheus metrics, Grafana dashboard)
- Simple cache schema (Redis or in-memory)

**No shadow mode delay - proceed immediately to Phase 1**

---

### Phase 1: Hupyy Integration Service + UI (Weeks 2-4)
**Duration:** 3 weeks
**Deliverables:**

**Backend:**
- Hupyy API client (Python, async httpx)
- Circuit breaker pattern (5-failure threshold, 60s timeout)
- Input chunking logic (split large inputs into <10KB chunks)
- Simple cache (chunk_hash → verification_result)
- Parallel async verification (asyncio.gather for batch processing)
- Force enrich=false on all requests

**Frontend:**
- Checkbox in chat UI to enable/disable Hupyy
- Progress indicator for verification (percentage, spinner)
- Metadata viewer (click to expand verification details)
- Toast notifications for completion/errors

**Key Constraint:** Handle 1-2 minute latency gracefully, don't block UX

---

### Phase 2: Verification Orchestrator + Feedback (Weeks 5-7)
**Duration:** 3 weeks
**Deliverables:**

- Kafka consumer for verify_chunks topic
- Verification orchestrator (batch processing, parallel workers)
- Qdrant updater (fast feedback tier, <100ms updates)
- ArangoDB updater (document-level metrics)
- Cache invalidation on source changes
- Top-5 to top-10 sampling (configurable, default: 5)

**Testing:**
- Unit tests with mocked Hupyy (1-2 min simulated delay)
- Integration tests (full Kafka flow)
- Load test: 10 parallel verifications

---

### Phase 3: Enhanced Ranking + PageRank (Weeks 8-10)
**Duration:** 3 weeks
**Deliverables:**

- Integrate verification scores into ranking formula:
  - Semantic: 45%
  - PageRank: 30%
  - Verification: 15%
  - Historical: 10%
- PageRank calculator (ArangoDB graph traversal)
- Gradual weight transition (0% → 15% over 1 week, NOT 2 weeks)
- Final validation tests (Precision@5 measurement)

**Target:** 98% Precision@5 (ambitious, may need iteration)

---

### Phase 4: Polish + Documentation (Week 11)
**Duration:** 1 week
**Deliverables:**

- Code review and refactoring
- Comprehensive documentation (API docs, architecture diagrams)
- Runbooks for operators
- Final linting and test coverage report
- Git commit and release

**Total Timeline: 11 weeks (reduced from 16 weeks)**

---

## Key Decisions (LOCKED IN)

✅ **Service architecture:** Separate microservice
✅ **Verification timing:** Async (mandatory, 1-2 min latency)
✅ **Sampling strategy:** Top-5 to top-10 (configurable, default: 5)
✅ **Shadow mode:** Skip delays (validate but don't wait weeks)
✅ **Canary rollout:** Skip (not in production)
✅ **Caching:** Simple version (chunk_hash → result)
✅ **UI work:** Required (checkbox, progress, metadata)
✅ **enrich parameter:** Always false

---

## Updated Success Criteria

### Primary Goal
**Precision@5 = 98%** (aspirational, may require tuning)

### Secondary Goals
- **Query latency:** User sees results immediately, verification runs in background
- **Verification coverage:** 30-50% of chunks (lower due to slow API)
- **UI responsiveness:** Progress updates every 5-10 seconds
- **Cache hit rate:** 40%+ (reduces Hupyy API load)
- **Uptime:** 99.9% (circuit breaker prevents cascading failures)

---

## Implementation Notes

### Performance Expectations
- **Verification latency:** 60-120 seconds per chunk (not 20-30s)
- **Parallel processing:** 5-10 concurrent verifications max
- **Batch size:** 5-10 chunks per query (top-K sampling)
- **Total verification time:** 60-120s for batch (with parallelization)

### UI Behavior
1. User submits query
2. Results appear immediately (<200ms)
3. If Hupyy enabled (checkbox):
   - Progress bar appears: "Verifying 5 chunks... 0%"
   - Updates every 10s: "20%... 40%... 60%... 80%... 100%"
   - Toast notification: "Verification complete! Scores updated."
4. User can click metadata icon to view verification details

### Caching Strategy (Simple Version)
```python
cache_key = hash(chunk_content + chunk_metadata)
if cache_key in cache:
    return cache[cache_key]
else:
    result = await hupyy_api.verify(chunk)
    cache[cache_key] = result
    return result

# Invalidation: On source file change, clear all cache entries for that source
```

### Input Chunking Logic
- If input > 10KB: Split into logical chunks (paragraphs, sections)
- Each chunk verified independently
- Results aggregated (average confidence score)

---

## Risk Mitigation

### Top Risks (Updated)
1. **Slow verification (1-2 min)** → Parallel async, progress indicators, top-5 sampling
2. **Hupyy API downtime** → Circuit breaker, neutral fallback (1.0x)
3. **Cache invalidation bugs** → Simple hash-based approach, conservative invalidation
4. **UI unresponsiveness** → WebSocket updates, optimistic UI updates
5. **Precision@5 target missed** → Iterative tuning, acceptable to fall short initially

---

## Blockers Removed
- ✅ Shadow mode duration: No wait needed
- ✅ Canary rollout: Skipped (not in production)
- ✅ Hupyy API budget: Don't worry about it

## Remaining Prerequisites
- Infrastructure capacity: 2G RAM, 2 CPUs for hupyy-verification service
- Team availability: 1-2 engineers × 11 weeks
- Hupyy service: Already deployed at https://verticalslice-smt-service-gvav8.ondigitalocean.app

---

## Next Step: Proceed to Implementation

**Phase 0 starts now** - Infrastructure setup (Kafka, monitoring, feature flags, caching)

**Document Version:** v1.1 (Updated with user constraints)
**Date:** 2025-11-27
**Status:** Ready for implementation
