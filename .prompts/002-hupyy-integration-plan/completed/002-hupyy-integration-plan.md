<objective>
Create a detailed, phase-by-phase implementation plan for integrating Hupyy's SMT verification service into PipesHub's search pipeline.

This plan will break down the integration into incremental, testable phases with feature flags, enabling safe rollout and rollback at each stage.
</objective>

<context>
Research findings: @.prompts/001-hupyy-integration-research/hupyy-integration-research.md

PipesHub architecture:
- Qdrant (vector search) + ArangoDB (knowledge graph) + MongoDB (config)
- Kafka event messaging
- Node.js API + Python backend
- Current search flow: Query → Retrieval → Reranking → Results

Hupyy integration adds:
- Verification Orchestrator (coordinates SMT verification)
- Hupyy Integration Service (API client, solver management)
- Feedback processors (update Qdrant/ArangoDB with verification scores)
- Enhanced ranking with verification weights

Target: Precision@5 = 98%
</context>

<planning_requirements>
Create a phase-by-phase rollout plan addressing:

## 1. Phase Breakdown
For each phase, specify:
- **Phase name and objectives**
- **Deliverables**: What gets built/changed
- **Database changes**: Schema migrations, data backups
- **Feature flags**: How to enable/disable the phase
- **Testing strategy**: Unit, integration, load tests
- **Rollback plan**: How to safely revert if issues arise
- **Success criteria**: Metrics proving the phase works
- **Estimated effort**: Rough sizing (S/M/L)

## 2. Recommended Phase Structure
Suggest phases like:
- **Phase 0**: Infrastructure setup (Kafka topics, monitoring, feature flags)
- **Phase 1**: Hupyy Integration Service (API client, basic verification)
- **Phase 2**: Verification Orchestrator (event-driven coordination)
- **Phase 3**: Feedback processors (update vector DB and graph)
- **Phase 4**: Enhanced ranking (integrate verification scores)
- **Phase 5**: Monitoring dashboard & optimization

## 3. Dependencies & Critical Path
- Identify dependencies between phases
- Highlight the critical path
- Call out decisions needed before each phase
- Note external dependencies (Hupyy service availability, infrastructure)

## 4. Risk Mitigation
For each phase:
- **Risks**: What could go wrong?
- **Mitigation**: How to prevent or minimize impact?
- **Monitoring**: What metrics indicate problems?
- **Rollback triggers**: When to abort and revert?

## 5. Testing Strategy
- **Unit tests**: Component-level testing
- **Integration tests**: End-to-end verification flow
- **Load tests**: Performance under realistic query volume
- **Shadow mode**: Run verification without affecting ranking (validate accuracy)
- **Canary deployment**: Gradual rollout to percentage of users

## 6. Data Migration
- How to handle existing search results (re-index? backfill verification scores?)
- Backward compatibility during transition
- Rollback data strategy
</planning_requirements>

<constraints>
- **No breaking changes**: Existing search must continue working during rollout
- **Feature flags**: Every phase must be independently toggleable
- **Observability first**: Metrics and logs before feature activation
- **Incremental delivery**: Each phase delivers value, testable independently
- **Rollback safety**: Must be able to revert any phase within 5 minutes
</constraints>

<output_specification>
Create two files:

1. **hupyy-integration-plan.md** - Full implementation plan with XML metadata:
   ```xml
   <confidence>High/Medium/Low - based on research quality and decisions made</confidence>
   <dependencies>
   - Research findings (from 001)
   - User decisions on phase order, infrastructure choices, etc.
   - External dependencies (Hupyy SLA, infrastructure capacity)
   </dependencies>
   <open_questions>
   - Decisions still needed (e.g., "Use existing Python service or new microservice?")
   - Clarifications required from user
   </open_questions>
   <assumptions>
   - Assumptions about system capacity, Hupyy availability, team velocity
   - Assumptions carried forward from research
   </assumptions>
   ```

   Content structure:
   - Executive Summary (plan overview, timeline, risks)
   - Phase-by-Phase Breakdown (detailed specs for each phase)
   - Critical Path & Dependencies
   - Testing Strategy
   - Data Migration Plan
   - Monitoring & Observability
   - Rollback Procedures
   - Success Metrics (per phase and overall)
   - Appendices (file structure, code organization, config examples)

2. **SUMMARY.md** - Executive summary:
   - **One-liner**: Plan description (e.g., "6-phase rollout with shadow mode validation")
   - **Version**: v1
   - **Key Findings**: Top planning decisions and trade-offs
   - **Decisions Needed**: Approval on phase order, infrastructure choices, timeline
   - **Blockers**: Impediments to starting implementation
   - **Next Step**: User approval required before implementation

Save to: `.prompts/002-hupyy-integration-plan/`
</output_specification>

<verification_checklist>
Before declaring plan complete, verify:

□ All phases have clear deliverables and success criteria
□ Dependencies between phases identified
□ Feature flags specified for each phase
□ Rollback plan exists for every phase
□ Testing strategy covers unit, integration, and load tests
□ Data migration path documented
□ Monitoring metrics defined per phase
□ Risk mitigation strategies included
□ No breaking changes to existing functionality
□ Research findings incorporated into plan
□ Open questions documented for user decisions
□ Confidence level assigned with justification
</verification_checklist>

<decision_points>
Plan should present options for user to decide:

1. **Service architecture**: New microservice vs. extend existing Python service?
2. **Programming language**: Python (consistency) vs. Node.js (API layer proximity)?
3. **Verification timing**: Async (eventual consistency) vs. sync (immediate ranking update)?
4. **Phase order**: Can phases 3 and 4 be combined? Should monitoring come earlier?
5. **Shadow mode duration**: How long to validate before production ranking?
6. **Rollout strategy**: Canary percentage, duration per stage?

For each decision point:
- Present options with pros/cons
- Recommend default based on research
- Flag as "User decision required" in metadata
</decision_points>

<success_criteria>
- Complete phase breakdown with 5-7 phases
- Each phase independently testable and rollback-safe
- Feature flags specified for progressive enablement
- Testing strategy comprehensive (unit, integration, load, shadow)
- Data migration path clear and safe
- Risk mitigation for all major risks
- Decision points presented with recommendations
- SUMMARY.md provides executive view of plan
- Next step: User approval to proceed with implementation
</success_criteria>
