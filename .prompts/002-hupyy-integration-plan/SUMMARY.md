# Hupyy-PipesHub Integration: Executive Summary

## One-Liner
**6-phase incremental rollout with shadow mode validation, feature flags at every stage, and 5-minute rollback capability to achieve 98% Precision@5 through SMT verification-guided ranking.**

---

## Version
**v1.0** - Initial implementation plan
**Date:** 2025-11-27
**Status:** Ready for user approval

---

## Key Findings

### 1. Architecture Decision: Separate Microservice
**Recommendation:** Deploy Hupyy Integration Service as standalone Docker container (not integrated into pipeshub-ai).

**Rationale:**
- **Fault isolation**: Hupyy API issues don't cascade to core search
- **Independent scaling**: Allocate dedicated resources (2G RAM, 2 CPUs)
- **Clean separation**: SOLID principles, easier to swap verification providers
- **Rollback safety**: Can stop verification service independently

**Trade-off:** Additional deployment complexity (1 extra container) vs. production safety.

---

### 2. Verification Timing: Asynchronous (Recommended)
**Decision:** Run verification in background after returning search results to user.

**Why:**
- **Low latency**: User sees results immediately (<100ms impact)
- **Eventual consistency**: Verification updates scores for future queries
- **Better UX**: No 20-30s wait per search

**Alternative (Sync):** User waits for verification (20-30s), gets immediate scores. Poor UX for interactive search.

**UI Impact:** Requires "verification in progress" indicator (optional enhancement).

---

### 3. Adaptive Sampling Strategy
**Recommendation:** Start with 10% of queries, gradually increase to 30% during rollout.

**Sampling Logic:**
- **Top-K selection**: Verify 10-50 results per query (configurable)
- **Adaptive threshold**: More verification for high-uncertainty queries
- **Priority ranking**: Unverified chunks + high semantic similarity = high priority
- **Cost optimization**: Cache results (40%+ hit rate expected)

**Budget Consideration:** 10K verifications/day at $X per verification = $Y/month (requires Hupyy pricing confirmation).

---

### 4. Shadow Mode Validation (Phases 1-3, Weeks 1-11)
**Critical Safety Net:** Run verification for 11 weeks WITHOUT affecting ranking.

**Purpose:**
- Validate Hupyy API accuracy and stability
- Tune failure mode classification
- Optimize circuit breaker thresholds
- Collect baseline comparison data

**Exit Criteria:**
- Verification success rate >50%
- No circuit breaker trips during normal load
- Coverage reaches 30% of chunks

---

### 5. Gradual Weight Transition (Phase 4, Weeks 12-13)
**Ranking Weight:** Increase verification influence from 0% → 15% over 2 weeks (linear ramp).

**Formula:**
```
final_score = (
  0.45 × semantic_similarity +
  0.30 × pagerank_score +
  0.15 × verification_confidence +  // Gradually increased
  0.10 × historical_success
) × failure_mode_multiplier
```

**Monitoring:** A/B test at 10% users, compare Precision@5 vs. control group.

**Target:** +5% Precision@5 improvement before full rollout.

---

### 6. Canary Rollout (Phase 5, Weeks 14-16)
**Rollout Schedule:**
- Week 14: 5% → 25% → 50% (2-day intervals)
- Week 15: 75% → 100% (3-day intervals)
- Week 16: Monitoring and optimization

**Rollback Trigger:** Precision@5 drops >5% at any stage → revert to previous percentage.

**Success Criteria:** 98% Precision@5 achieved at 100% rollout.

---

## Plan Structure

### Phase Breakdown (16 weeks total)

| Phase | Duration | Objectives | Key Deliverables |
|-------|----------|------------|------------------|
| **Phase 0: Infrastructure** | Weeks 1-2 | Monitoring, Kafka topics, feature flags | Grafana dashboards, baseline metrics |
| **Phase 1: Hupyy Service** | Weeks 3-5 | Core verification, circuit breaker | Hupyy Integration Service deployed |
| **Phase 2: Orchestrator** | Weeks 6-8 | Event-driven coordination, Qdrant updates | Verification trigger in search pipeline |
| **Phase 3: Feedback Loop** | Weeks 9-11 | ArangoDB updates, PageRank calculation | Document-level verification metrics |
| **Phase 4: Enhanced Ranking** | Weeks 12-13 | Integrate scores into ranking, A/B test | Verification affects ranking (10% users) |
| **Phase 5: Canary Rollout** | Weeks 14-16 | Gradual rollout to 100%, optimization | 98% Precision@5 achieved |

---

## Critical Success Factors

### 1. Feature Flags Everywhere
Every phase must be independently toggleable via feature flags:
- `verification_enabled`: Master kill switch
- `verification_shadow_mode`: Run without ranking impact
- `verification_ranking_weight`: Gradual weight increase (0.0-0.15)
- `verification_rollout_percentage`: Canary rollout (0-100%)

**Rollback Time:** <5 minutes (config update via ETCD).

---

### 2. Circuit Breaker for Resilience
**Configuration:**
- Fail threshold: 5 consecutive errors → OPEN circuit
- Timeout: 60s in OPEN state before half-open
- Fallback: Neutral multiplier (1.0x) when circuit open

**Purpose:** Prevent cascading failures if Hupyy API goes down.

**Monitoring:** Alert if circuit remains open >10 minutes.

---

### 3. Observability First
**Dashboards Created in Phase 0:**
- Verification service health (circuit breaker, API latency)
- Search quality metrics (Precision@5, NDCG@10)
- System resources (Kafka lag, Qdrant latency)

**Alerts:**
- CRITICAL: Precision drops >10%, circuit breaker open, verification success <30%
- WARNING: Kafka lag >1000, Qdrant latency >100ms, feedback diversity <3.0

---

### 4. No Breaking Changes
**Backward Compatibility:**
- Qdrant payload extensions are optional (existing chunks work)
- ArangoDB document properties are optional
- Search API unchanged (verification transparent to users)
- Rollback to pre-verification state anytime

---

### 5. Testing at Every Stage
**Test Types:**
- **Unit tests:** 80%+ coverage for core logic
- **Integration tests:** End-to-end verification flow
- **Load tests:** 100-200 queries/minute sustained
- **A/B tests:** Compare verification group vs. control
- **Chaos tests:** Circuit breaker, Kafka failures, Hupyy API outages

---

## Decisions Needed from User

### 1. Service Architecture (REQUIRED before Phase 0)
**Question:** Deploy as separate microservice or integrate into pipeshub-ai container?

**Options:**
- **A (Recommended):** Separate microservice - Better isolation, independent scaling
- **B:** Integrated service - Simpler deployment, shared resources

**Impact:** Affects Docker Compose configuration and resource allocation.

**User Decision:** [ ] Option A (Separate) [ ] Option B (Integrated)

---

### 2. Verification Timing (REQUIRED before Phase 2)
**Question:** Run verification synchronously (blocking) or asynchronously (eventual consistency)?

**Options:**
- **A (Recommended):** Async - Low latency, better UX, requires "verification pending" UI
- **B:** Sync - High latency (20-30s), immediate scores, poor UX

**Impact:** Affects search pipeline integration and UI requirements.

**User Decision:** [ ] Option A (Async) [ ] Option B (Sync)

---

### 3. Verification Sampling Strategy (REQUIRED before Phase 2)
**Question:** How many search results to verify per query?

**Options:**
- **A:** All top-50 results (comprehensive, higher cost)
- **B:** Top-10 only (lower cost, faster feedback)
- **C (Recommended):** Adaptive 10-50 based on query confidence

**Impact:** Affects Hupyy API call volume and cost.

**User Decision:** [ ] Option A (50) [ ] Option B (10) [ ] Option C (Adaptive)

---

### 4. Shadow Mode Duration (REQUIRED before Phase 4)
**Question:** How long to validate verification accuracy before affecting ranking?

**Options:**
- **A (Recommended):** 2-4 weeks (Phases 1-3)
- **B:** 1 week (compressed timeline, higher risk)
- **C:** 6+ weeks (conservative, slower delivery)

**Impact:** Affects Phase 4 start date and confidence in accuracy.

**User Decision:** [ ] Option A (2-4 weeks) [ ] Option B (1 week) [ ] Option C (6+ weeks)

---

### 5. Canary Rollout Percentages (REQUIRED before Phase 5)
**Question:** What percentages for gradual rollout?

**Options:**
- **A (Recommended):** 5% → 25% → 50% → 100% (1 week per stage)
- **B:** 10% → 50% → 100% (faster, higher risk)
- **C:** 1% → 5% → 10% → 25% → 50% → 100% (slower, safer)

**Impact:** Affects Phase 5 timeline and rollback frequency.

**User Decision:** [ ] Option A (4 stages) [ ] Option B (3 stages) [ ] Option C (6 stages)

---

### 6. Hupyy API Budget (REQUIRED before Phase 5)
**Question:** What is the monthly budget for Hupyy API calls?

**Estimate:** 10K verifications/day × 30 days = 300K verifications/month

**Impact:** May need to implement rate limiting or reduce sampling rate.

**User Input:** Monthly budget: $_______ (or "No limit")

---

## Blockers & Dependencies

### External Dependencies
1. **Hupyy API availability:** Requires 99.5%+ uptime and <30s latency
   - **Action:** Confirm SLA with Hupyy team
   - **Status:** Assumed based on research

2. **Hupyy API pricing:** Need to understand rate limits and cost structure
   - **Action:** Obtain pricing information from Hupyy
   - **Status:** Not confirmed (see Open Question #6 in plan)

3. **Infrastructure capacity:** Docker Compose must support additional 2G RAM + 2 CPUs
   - **Action:** Verify available resources on deployment server
   - **Status:** Assumed sufficient

---

### Internal Dependencies
1. **Team availability:** 1-2 engineers full-time for 16 weeks
   - **Action:** Confirm resource allocation
   - **Status:** Pending approval

2. **PageRank implementation:** Not found in current codebase, must be built
   - **Action:** Implement modified PageRank algorithm (Phase 3)
   - **Status:** Planned

3. **Citation network data:** Required for PageRank calculation
   - **Action:** Verify citation metadata exists in ArangoDB
   - **Status:** Assumed (needs verification)

---

### Technical Blockers (None identified)
- All required infrastructure exists (Kafka, Qdrant, ArangoDB, MongoDB)
- No breaking changes to existing system
- Backward compatible schema extensions

---

## Risk Mitigation

### Top 5 Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Hupyy API downtime** | Medium | High | Circuit breaker, neutral fallback (1.0x), monitoring alerts |
| **Verification accuracy issues** | Low | High | Shadow mode (11 weeks), quality gates (formalization similarity ≥0.91) |
| **Feedback loop instability** | Medium | High | Query drift detection (<0.3 limit), L2 regularization, ε-greedy exploration |
| **Cost overruns** | Medium | Medium | Cache results (40%+ hit rate), adaptive sampling, rate limiting |
| **Cold start poor performance** | High | Medium | Gradual weight transition (0% → 15% over 2 weeks), transfer learning |

---

## Timeline & Milestones

```
Week 1-2:   Phase 0 - Infrastructure setup (Kafka, monitoring, feature flags)
Week 3-5:   Phase 1 - Hupyy Integration Service (API client, circuit breaker)
Week 6-8:   Phase 2 - Verification Orchestrator (search integration, Qdrant updates)
Week 9-11:  Phase 3 - Feedback Integration (ArangoDB, PageRank)
Week 12-13: Phase 4 - Enhanced Ranking (A/B test, gradual weight transition)
Week 14-16: Phase 5 - Canary Rollout (5% → 100%), optimization

Total: 16 weeks (4 months)
```

**Key Milestones:**
- ✅ Week 2: Baseline metrics collected
- ✅ Week 5: Shadow mode verification operational
- ✅ Week 11: 30% verification coverage achieved
- ✅ Week 13: A/B test shows +5% Precision@5 improvement
- ✅ Week 16: **98% Precision@5 achieved at 100% rollout**

---

## Cost Estimate

### Development Cost
**Effort:** 1-2 engineers × 16 weeks = 16-32 engineer-weeks

**Breakdown:**
- Phase 0: 2 weeks (1 engineer)
- Phase 1: 3 weeks (1-2 engineers)
- Phase 2: 3 weeks (1-2 engineers)
- Phase 3: 3 weeks (1-2 engineers)
- Phase 4: 2 weeks (1-2 engineers)
- Phase 5: 3 weeks (1-2 engineers)

**Recommended:** 2 engineers working in parallel where possible (compress timeline).

---

### Infrastructure Cost
**Additional Resources:**
- Hupyy verification service: 2G RAM, 2 CPUs (marginal cost in Docker Compose)
- Kafka storage: ~1-5 MB/s additional throughput (negligible)
- Qdrant metadata: Minimal storage increase (<1% of total)

**Estimated Monthly Increase:** <$50 for additional compute resources.

---

### Hupyy API Cost
**Depends on pricing model (not yet confirmed):**
- Estimated volume: 300K verifications/month (10K/day at 30% sampling)
- If pay-per-call: $X × 300K = $Y/month
- If subscription: Fixed monthly fee

**Action Required:** Obtain Hupyy pricing to finalize budget.

---

## Success Metrics

### Primary Goal
**Precision@5 = 98%** (target specified in architecture)

**Current Baseline:** ~40% (assumed, requires Phase 0 validation)

**Target Improvement:** +58 percentage points (145% relative improvement)

---

### Secondary Goals
- **NDCG@10 ≥ 0.75** (10-point improvement from baseline ~0.65)
- **Query latency increase <200ms** (async verification)
- **Verification coverage ≥ 80%** of documents
- **Feedback loop stable:** Coverage >80%, diversity >3.0 bits, drift <0.3
- **Uptime ≥ 99.9%** (maintain existing SLA)

---

### Quality Gates (Pass/Fail per Phase)
- Phase 0: Baseline metrics collected ✅
- Phase 1: Verification success rate >50% ✅
- Phase 2: Qdrant update latency <100ms ✅
- Phase 3: PageRank calculation <60s ✅
- Phase 4: A/B test shows +5% Precision@5 ✅
- Phase 5: 98% Precision@5 at 100% rollout ✅

**Failure Handling:** If any gate fails, halt progression and debug before continuing.

---

## Next Steps

### 1. User Approval Required
**Review this plan and the detailed implementation plan** (hupyy-integration-plan.md)

**Approve or request changes:**
- [ ] Approve plan as-is → Proceed to Phase 0
- [ ] Request modifications → Iterate on plan
- [ ] Reject plan → Discuss alternative approaches

---

### 2. Make Key Decisions
**Answer the 6 decision points** (see "Decisions Needed from User" section above):
1. Service architecture: Separate microservice or integrated? → **Recommend: Separate**
2. Verification timing: Async or sync? → **Recommend: Async**
3. Sampling strategy: 10, 50, or adaptive? → **Recommend: Adaptive**
4. Shadow mode duration: 1, 2-4, or 6+ weeks? → **Recommend: 2-4 weeks**
5. Canary rollout: 4, 3, or 6 stages? → **Recommend: 4 stages**
6. Hupyy API budget: $______/month → **Pending**

---

### 3. Confirm Dependencies
- [ ] Confirm 1-2 engineers available full-time for 16 weeks
- [ ] Obtain Hupyy API pricing and SLA documentation
- [ ] Verify infrastructure capacity (2G RAM, 2 CPUs available)
- [ ] Confirm citation network data exists in ArangoDB (for PageRank)

---

### 4. Kickoff Phase 0 (Upon Approval)
**First Actions:**
1. Create Kafka topics (verify_chunks, verification_complete, verification_failed, pagerank_recalc)
2. Setup Grafana dashboards and Prometheus metrics
3. Implement feature flag system (MongoDB + ETCD integration)
4. Run baseline metrics collection for 1 week
5. Setup alerting (PagerDuty for CRITICAL, Slack for WARNING)

**Timeline:** Weeks 1-2 (2 weeks)

**Deliverable:** Infrastructure ready for Phase 1 development.

---

## Confidence Assessment

**Overall Confidence: High (85%)**

**High Confidence (90%+):**
- Hupyy API integration (OpenAPI spec verified)
- Kafka event-driven architecture (existing infrastructure proven)
- Qdrant payload updates (documented capability)
- Feature flag rollback strategy (simple config changes)

**Medium Confidence (70-80%):**
- PageRank implementation (not in codebase, must build from scratch)
- Cold start performance (30-day ramp may be optimistic)
- Feedback loop stability (requires tuning, may need L2 regularization adjustments)

**Low Confidence (<70%):**
- Hupyy API cost and rate limits (not confirmed)
- Citation network completeness (assumed to exist, needs verification)
- 98% Precision@5 achievability (ambitious target, may require iteration)

**Risk Acceptance:** Plan includes extensive testing, shadow mode, and gradual rollout to mitigate uncertainties.

---

## Conclusion

This plan provides a **safe, incremental rollout** strategy for integrating Hupyy's SMT verification into PipesHub's search pipeline. Key safety mechanisms include:

1. **Feature flags** at every phase (instant rollback)
2. **Shadow mode** for 11 weeks (validate before impacting users)
3. **A/B testing** in Phase 4 (prove value before full rollout)
4. **Canary deployment** in Phase 5 (gradual exposure, halt on degradation)
5. **Circuit breaker** (resilience against Hupyy API failures)

**Expected Outcome:** 98% Precision@5 achieved within 16 weeks with minimal production risk.

**Action Required:** User approval to proceed with Phase 0 kickoff.

---

**Document Version:** v1.0
**Date:** 2025-11-27
**Status:** Awaiting user approval
**Next Review:** Upon user feedback
