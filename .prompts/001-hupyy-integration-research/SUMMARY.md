# Executive Summary: Hupyy-PipesHub Integration Research

**One-liner:** Comprehensive technical analysis confirms feasibility of integrating Hupyy SMT verification into PipesHub's search pipeline via event-driven architecture with 3 new microservices, backward-compatible database extensions, and 30-day cold-start period to achieve 98% Precision@5 target.

**Version:** v1

---

## Key Findings

### 1. Hupyy API is Production-Ready with Known Constraints
- **Single endpoint** (`POST /pipeline/process`) with 20-30s typical latency, 3-10s best case
- **Quality gates built-in**: formalization_similarity ≥0.91, extraction_degradation ≤0.05
- **No authentication required** (confirmed via OpenAPI spec)
- **Critical gap**: Rate limits and pricing not documented - requires confirmation before production deployment

### 2. PipesHub Infrastructure Supports Integration with Minimal Changes
- **Kafka infrastructure exists**: Retry logic, consumer groups, and batching already implemented
- **Qdrant supports real-time updates**: Payload extensions via `overwrite_payload()` method, no re-indexing needed
- **ArangoDB flexibility**: JSON document structure allows metadata additions without schema migration
- **Backward compatibility**: All database changes are additive, no breaking changes to existing search API

### 3. Circuit Breaker Pattern is Critical for Reliability
- **Failure threshold**: Open circuit after 5 consecutive Hupyy API failures
- **Fallback strategy**: Apply neutral 1.0x multiplier when circuit open (no penalty for external service failure)
- **Recovery mechanism**: Half-open state with 2 consecutive successes required to close circuit
- **Research-backed**: Pattern aligns with [Microservices.io best practices](https://microservices.io/patterns/reliability/circuit-breaker.html)

### 4. Cold Start Requires 30-Day Gradual Transition
- **Days 1-7**: Verification weight 0%, rely on semantic similarity (90%) + pseudo-feedback (10%)
- **Days 8-30**: Gradual increase to 15% verification weight, prioritize high-traffic chunks
- **Day 30+**: Full integration with final weights (Semantic 45%, PageRank 30%, Verification 15%, Historical 10%)
- **Transfer learning**: Estimate scores for unverified chunks using similar chunks (0.7 × similar_avg + 0.3 × global_avg)

### 5. Separate Microservice Architecture Recommended
- **Isolation benefits**: Independent scaling, fault isolation, cleaner separation of concerns
- **Resource requirements**: 2G RAM, 2 CPUs for `hupyy-verification` service
- **Deployment complexity**: Minimal - single Docker Compose service addition
- **Alternative considered**: Integrated service within `pipeshub-ai` container (higher resource contention risk)

---

## Decisions Needed

### Priority 1: Critical User Decisions (Blocking Implementation)

1. **Sync vs. Async Verification** (High Impact on UX)
   - **Async (Recommended)**: Return search results immediately, verify in background, update scores for future queries
     - Pros: Low latency (<200ms impact), better UX for interactive search
     - Cons: Requires "verification in progress" UI indicator, eventual consistency
   - **Sync**: Wait for verification before returning results
     - Pros: Immediate verification scores, no UI changes needed
     - Cons: 20-30s added latency per query, poor UX

2. **Verification Sampling Strategy** (Impacts Hupyy API Load)
   - **Option A**: Verify all top-50 results per query (high load, comprehensive verification)
   - **Option B**: Verify top-10 only (lower load, faster feedback loop)
   - **Option C (Recommended)**: Adaptive sampling based on query confidence
     - High-confidence queries: verify top-5
     - Medium-confidence: verify top-15
     - Low-confidence: verify top-30

3. **Deployment Architecture** (Infrastructure Planning)
   - **Recommended**: Separate `hupyy-verification` microservice container
   - **Alternative**: Integrated within `pipeshub-ai` container
   - **Rationale**: Independent scaling, fault isolation outweigh deployment complexity

### Priority 2: Hupyy API Clarifications (Risk Mitigation)

4. **Rate Limits and Pricing**
   - Question: Does Hupyy API have requests/minute limits or pricing tiers?
   - Impact: Budget planning, adaptive throttling implementation
   - Action: Contact Hupyy team or test with production-scale load

5. **API Key Management**
   - Question: How should credentials be stored and rotated?
   - Options: Environment variables, Docker secrets, external secrets manager (AWS Secrets Manager, HashiCorp Vault)
   - Impact: Security posture, multi-tenant support

### Priority 3: Migration Strategy (Operational Planning)

6. **Existing Chunk Verification Approach**
   - **Option A (Recommended)**: Gradual on-demand verification (verify chunks as they're retrieved in searches)
   - **Option B**: Batch backfill job (verify all existing chunks over time, independent of search traffic)
   - **Option C**: Hybrid approach (on-demand for frequently accessed, batch for long-tail)
   - **Rationale**: On-demand prioritizes high-value chunks, avoids unnecessary API costs

---

## Blockers

### External Dependencies
1. **Hupyy API Rate Limits**: Not documented in OpenAPI spec
   - **Impact**: Cannot finalize adaptive throttling or cost estimates
   - **Resolution**: Contact Hupyy team or test empirically
   - **Timeline**: 1-2 days

2. **Network Latency to Hupyy Service**: Assumed <100ms, not verified
   - **Impact**: Total verification latency could exceed 30s if network is slow
   - **Resolution**: Production network testing from PipesHub environment
   - **Timeline**: 1 day

### Internal Dependencies
None identified - all PipesHub infrastructure components are in place.

---

## Next Step

**Create detailed implementation plan** with sprint-by-sprint breakdown once:
1. User confirms sync/async verification model decision
2. User confirms verification sampling strategy
3. Hupyy API rate limits clarified (or assumed based on testing)

**Estimated timeline to first working prototype:**
- Phase 1 (Foundation): 2 weeks
- Phase 2 (Fast Feedback Loop): 4 weeks
- Phase 3 (Medium Feedback Loop): 6 weeks
- Phase 4 (Validation & Deployment): 4 weeks
- **Total: 16 weeks (4 months)**

**Quick-win option for faster feedback:**
- Implement Phase 1-2 only (Foundation + Fast Feedback) for initial validation
- Defer PageRank integration and reranker optimization to later phases
- **Reduced timeline: 6 weeks to production-ready MVP**

---

## Risk Summary

| Risk Category | Level | Mitigation |
|--------------|-------|------------|
| Technical Feasibility | Low | All integration points verified in codebase, backward compatible changes only |
| Hupyy API Availability | Medium | Circuit breaker pattern, fallback to neutral scoring, monitoring with alerts |
| Performance Impact | Medium | Async processing, cold start strategy, gradual weight transition |
| Cost Overruns | Medium | Rate limiting, adaptive sampling, caching verified results |
| Migration Complexity | Low | Additive schema changes, feature flags for rollback, A/B testing capability |
| Operational Overhead | Medium | Comprehensive monitoring dashboard, runbooks, PagerDuty integration |

**Overall Risk Level: Medium** - Primary risks are external (Hupyy API dependency) and can be mitigated through resilience patterns.

---

## Research Quality Assessment

**Confidence Level: High**

**Sources Verified:**
- Hupyy OpenAPI specification (official API contract)
- PipesHub architecture document (authoritative spec)
- PipesHub codebase analysis (Kafka, Qdrant, ArangoDB services)
- Industry best practices (circuit breaker, retry logic, event-driven architecture)

**Assumptions Documented:**
- PageRank implementation not found in codebase (requires implementation)
- Hupyy API is stateless and idempotent (standard assumption for REST APIs)
- Network latency to Hupyy is <100ms (requires production testing)
- No authentication required (confirmed in OpenAPI spec, but may change)

**Open Questions Identified:**
- 6 critical questions documented in main research report
- All questions mapped to specific user decisions or external clarifications
- No technical unknowns blocking implementation planning

---

## Appendix: Quick Reference

### Database Schema Extensions
- **Qdrant**: Add `verification`, `verification_history`, `verification_metrics` to existing payload (JSON extension)
- **ArangoDB**: Add `verification_metrics`, `quality_signals`, `pagerank_data` to documents (JSON extension)
- **Migration**: None required - backward compatible additions

### Kafka Topics (New)
1. `verify_chunks` - Queue chunks for verification (Producers: Node.js API, Consumers: Verification Orchestrator)
2. `verification_complete` - Broadcast successful results (Producers: Verification Orchestrator, Consumers: Qdrant/ArangoDB Updaters)
3. `verification_failed` - Track failures (Producers: Verification Orchestrator, Consumers: Metrics Collector)
4. `pagerank_recalc` - Trigger PageRank recalculation (Producers: ArangoDB Updater, Consumers: PageRank Calculator)

### New Microservices
1. **Verification Orchestrator**: Consumes `verify_chunks`, calls Hupyy API, classifies failure modes, produces results
2. **Qdrant Updater**: Consumes `verification_complete`, updates chunk payloads with EMA scores (<100ms latency)
3. **ArangoDB Updater**: Consumes `verification_complete`, updates document-level metrics, triggers PageRank recalc

### Monitoring Metrics (Critical)
- **Quality**: NDCG@10 (target: 0.75), MRR (target: 0.70), Precision@5 (target: 0.98), Recall@50 (target: 0.90)
- **Verification**: Success rate, avg confidence, failure mode distribution (target: 40-50% verified_sat)
- **System**: Query latency, verification queue depth, Kafka consumer lag, circuit breaker state

### Alert Thresholds
- **CRITICAL**: Holdout performance drop >10%, verification success rate <50%, circuit breaker open
- **WARNING**: Diversity entropy <3.0, verification queue >100, query drift >0.3, Kafka lag >1000
- **INFO**: Success rate change >5% WoW, new document type detected

---

**For detailed technical analysis, see:** `hupyy-integration-research.md`

**Research completed:** 2025-11-27
**Researcher:** Claude Code (Sonnet 4.5)
**Codebase:** PipesHub AI (pipeshub-ai-orig)
