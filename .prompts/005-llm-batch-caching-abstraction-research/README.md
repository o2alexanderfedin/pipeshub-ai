# Provider-Agnostic Batch API & Prompt Caching Research

**Research Date**: 2025-11-28
**Status**: Complete - Ready for Implementation
**Estimated Cost Savings**: 50-95% (up to $102,876/year)
**Implementation Timeline**: 5 weeks

---

## Quick Links

1. **[SUMMARY.md](./SUMMARY.md)** - Executive summary with key findings and decisions needed (15 min read)
2. **[llm-batch-caching-abstraction-research.md](./llm-batch-caching-abstraction-research.md)** - Complete research documentation (45 min read)
3. **[architecture-diagram.md](./architecture-diagram.md)** - Visual architecture and flow diagrams (10 min read)

---

## TL;DR

### Problem
PipesHub's LLM indexing costs are high at $13,500/month for processing 1M documents, with no optimization for batch processing or prompt caching.

### Solution
Implement a provider-agnostic optimization layer that:
- Uses Batch APIs for 50% cost savings on high-volume workloads
- Uses Prompt Caching for 90% savings on repeated content
- Maintains backward compatibility with all 14 existing LLM providers
- Gracefully falls back to standard API when optimizations unavailable

### Results
- **Cost**: $4,927/month (63.5% savings) with moderate caching
- **Best Case**: $4,442/month (67% savings) with optimal caching
- **Annual Savings**: $102,876/year
- **ROI**: Immediate (first month)
- **Implementation**: 5 weeks, 1 developer

### Architecture
- **Pattern**: Decorator pattern wrapping LangChain models
- **Zero Breaking Changes**: Existing code works unchanged
- **Configuration**: ArangoDB-based, per-provider settings
- **Monitoring**: Built-in metrics, cost tracking, alerts

---

## Document Guide

### For Decision Makers
**Read**: [SUMMARY.md](./SUMMARY.md)
- Executive summary
- Cost projections
- Key decisions needed
- Implementation timeline

**Time**: 15 minutes

### For Architects
**Read**:
1. [SUMMARY.md](./SUMMARY.md) - Overview and architecture decisions
2. [architecture-diagram.md](./architecture-diagram.md) - Visual architecture
3. [llm-batch-caching-abstraction-research.md](./llm-batch-caching-abstraction-research.md) - Section 3 (Architecture)

**Time**: 30 minutes

### For Implementers
**Read**: [llm-batch-caching-abstraction-research.md](./llm-batch-caching-abstraction-research.md)
- Complete technical documentation
- Code examples
- Integration plan
- Testing strategy
- Migration checklist

**Time**: 45-60 minutes

### For Product/Business
**Read**:
- [SUMMARY.md](./SUMMARY.md) - Focus on "Cost Savings Analysis" and "Success Criteria"
- [llm-batch-caching-abstraction-research.md](./llm-batch-caching-abstraction-research.md) - Section 12 (Cost Projections)

**Time**: 20 minutes

---

## Key Findings Summary

### Provider Support

| Feature | Anthropic | OpenAI | Gemini | Others |
|---------|-----------|--------|--------|--------|
| **Batch API** | ✅ 50% off | ✅ 50% off | ✅ 50% off | ❌ |
| **Prompt Caching** | ✅ 90% off | ✅ 50% off (auto) | ✅ 90% off | ❌ |
| **Combined Savings** | **95%** | **75%** | **50-90%*** | N/A |

*Gemini: Batch and cache discounts don't stack

### Recommended Approach

**Pattern**: Decorator Pattern
```python
# Existing code works unchanged!
llm, config = await get_llm(config_service)
response = await llm.ainvoke(messages)  # Auto-cached
responses = await llm.abatch(messages_list)  # Auto-batched
```

**Why**:
- Zero breaking changes
- Transparent optimization
- Graceful fallback
- Easy to enable/disable

### Cost Impact

**Baseline**: $13,500/month (no optimization)
**Optimized**: $4,927/month (63.5% savings)
**Annual Savings**: $102,876

**ROI**: Immediate (first month covers implementation cost)

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
- Create optimization wrapper module
- Implement provider capability detection
- Add unit tests
- Deploy disabled by default

**Deliverables**:
- `/app/utils/llm_optimization.py` (new)
- Unit tests (80%+ coverage)
- Updated `aimodels.py` (5 lines)

### Phase 2: Testing (Week 2)
- Enable in dev environment
- Test batch APIs for Anthropic/OpenAI/Gemini
- Validate fallback mechanisms
- Measure actual cost savings

**Deliverables**:
- Test results report
- Performance benchmarks
- Cost comparison vs predictions

### Phase 3: Caching (Week 3)
- Implement prompt caching for domain extraction
- Optimize cache breakpoints
- Measure cache hit rates
- A/B test TTL settings

**Deliverables**:
- Cache-optimized domain extraction
- Cache hit rate dashboard
- Optimization guide

### Phase 4: Integration (Week 4)
- Create batch processor for Kafka handler
- Add metrics collection
- Implement monitoring endpoints
- Load testing

**Deliverables**:
- Batch processing for indexing pipeline
- Monitoring API endpoints
- Load test results

### Phase 5: Rollout (Week 5+)
- Deploy to staging
- Gradual production rollout (10% → 50% → 100%)
- Monitor metrics
- Documentation and training

**Deliverables**:
- Production deployment
- Runbook
- Team training materials
- Cost savings report

---

## Critical Decisions Needed

Before implementation begins, decisions needed on:

1. **Batch Accumulation Strategy**
   - Recommendation: Hybrid (100 docs OR 30 seconds, whichever first)

2. **Default Cache TTL**
   - Recommendation: 5 minutes default, 1 hour for domain definitions

3. **Optimization Enabled by Default**
   - Recommendation: Opt-in for Phase 1, opt-out after validation

4. **Phase 1 Provider Support**
   - Recommendation: Anthropic only, expand to OpenAI/Gemini in Phase 2

5. **Monitoring Approach**
   - Recommendation: Built-in API endpoints + logs

6. **Partial Batch Failure Handling**
   - Recommendation: Retry failed items individually (up to 3 times)

**Decision Meeting**: Schedule with stakeholders to approve architecture and decisions

---

## Success Metrics

### Technical
- ✅ All unit tests pass (80%+ coverage)
- ✅ Zero breaking changes
- ✅ Graceful fallback works
- ✅ Batch API integration successful
- ✅ Cache hit rate >50%

### Business
- ✅ Cost reduction: Minimum 50% on batch workloads
- ✅ Cost reduction: Minimum 60% with caching
- ✅ No increase in error rates (<0.1% optimization failures)
- ✅ Acceptable latency (<24h batch turnaround)
- ✅ ROI achieved within first month

### Operational
- ✅ Monitoring dashboard operational
- ✅ Cost tracking accurate (±5%)
- ✅ Alerts functional
- ✅ Documentation complete
- ✅ Team trained

---

## Files in This Research

```
.prompts/005-llm-batch-caching-abstraction-research/
├── README.md (this file)
│   └── Quick navigation and overview
│
├── SUMMARY.md (15 min read)
│   ├── Executive summary
│   ├── Key findings
│   ├── Decisions needed
│   ├── Cost projections
│   └── Next steps
│
├── llm-batch-caching-abstraction-research.md (45 min read)
│   ├── 1. Provider Capability Matrix
│   ├── 2. Current Architecture Analysis
│   ├── 3. Recommended Architecture
│   ├── 4. Integration Plan
│   ├── 5. Code Examples
│   ├── 6. Testing Strategy
│   ├── 7. Monitoring & Metrics
│   ├── 8. Configuration Reference
│   ├── 9. Migration Checklist
│   ├── 10. Risk Assessment
│   ├── 11. Open Questions
│   ├── 12. Cost Projections
│   ├── 13. References
│   └── 14. Technical Appendix
│
└── architecture-diagram.md (10 min read)
    ├── Current vs Optimized Architecture
    ├── Request Flow Diagrams
    ├── Provider Decision Tree
    ├── Cost Comparison Charts
    ├── Fallback Strategy Flow
    ├── Data Flow - Indexing Pipeline
    ├── Monitoring Dashboard Layout
    └── Implementation Timeline
```

---

## Research Methodology

### Approach
1. **Codebase Analysis**: Examined PipesHub's LLM abstraction layer (`/app/utils/aimodels.py`, `/app/utils/llm.py`)
2. **Provider Research**: Reviewed official documentation for Anthropic, OpenAI, Google Gemini, AWS Bedrock
3. **Architecture Design**: Evaluated 3 design patterns (Decorator, Adapter, Strategy)
4. **Cost Modeling**: Calculated savings based on 1M documents/month baseline
5. **Integration Planning**: Identified minimal-change integration points in existing code

### Data Sources
- **PipesHub Codebase**: Python backend analysis
- **Provider Documentation**: Official API docs from Anthropic, OpenAI, Google
- **LangChain Documentation**: Batch processing and async support
- **Industry Analysis**: LLM pricing comparisons and optimization strategies

### Confidence Level
**High (95%)**

All major providers researched with official documentation. Codebase analyzed for integration points. Architecture patterns validated against LangChain best practices.

---

## Next Steps

### Immediate (This Week)
1. **Review Meeting**: Schedule with stakeholders
   - Present findings
   - Make critical decisions
   - Approve architecture

2. **Environment Setup**:
   - Configure API keys (Anthropic/OpenAI/Gemini)
   - Set up dev ArangoDB with optimization config
   - Create feature branch

3. **Ticket Creation**:
   - Break down Phase 1 into implementation tickets
   - Assign to developer
   - Set up cost monitoring baseline

### Week 1 (Phase 1)
- Implement optimization wrapper
- Write unit tests
- Deploy to dev (disabled)

### Week 2 (Phase 2)
- Enable in dev environment
- Test batch APIs
- Validate cost savings

### Week 3-5 (Phases 3-5)
- See [Implementation Roadmap](#implementation-roadmap) above

---

## Questions?

### Technical Questions
Contact: Development team lead
Topics: Architecture, implementation, testing

### Business Questions
Contact: Product/Business stakeholders
Topics: Cost savings, ROI, timeline

### Research Questions
Contact: Research author (Claude Code session owner)
Topics: Provider capabilities, design decisions, alternatives considered

---

## Changelog

**2025-11-28**: Initial research completed
- Comprehensive provider analysis
- Architecture design
- Integration plan
- Cost projections
- Implementation roadmap

---

## License & Usage

This research is proprietary to PipesHub and intended for internal use only.

**Usage**:
- Reference for implementation decisions
- Share with development team
- Present to stakeholders
- Basis for technical specifications

**Do Not**:
- Share externally
- Publish publicly
- Use for other projects without adaptation

---

**Research Complete**: 2025-11-28
**Prepared By**: Claude (Sonnet 4.5)
**Version**: 1.0
**Status**: Ready for Review & Implementation
