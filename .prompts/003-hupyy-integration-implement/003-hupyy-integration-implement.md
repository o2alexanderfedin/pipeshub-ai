<objective>
Implement the Hupyy SMT verification integration into PipesHub following the approved implementation plan.

Execute each phase incrementally with TDD (Test-Driven Development), creating tests before implementation, and verifying success criteria at each stage.
</objective>

<context>
Research findings: @.prompts/001-hupyy-integration-research/hupyy-integration-research.md
Implementation plan: @.prompts/002-hupyy-integration-plan/hupyy-integration-plan.md

PipesHub codebase:
- Backend: @backend/python/app/, @backend/nodejs/apps/
- Deployment: @deployment/docker-compose/
- Frontend: @frontend/src/

Project conventions: @/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/CLAUDE.md
</context>

<implementation_requirements>
For each phase in the plan:

## 1. Test-Driven Development
**CRITICAL: Write tests FIRST, then minimal code to pass, then refactor.**

For each deliverable:
1. **Write failing unit test** - Test the interface/contract
2. **Write minimal implementation** - Just enough to pass
3. **Write integration test** - Test the component in context
4. **Refactor** - Improve while keeping tests green
5. **Code review** - Use a subtask to review changes
6. **Linting** - Run all applicable linters before committing

## 2. Type Safety
- **Explicit types everywhere** - No `any`, use `unknown` with type guards
- **Interface definitions** - For all request/response schemas
- **Enum usage** - For verification verdicts (SAT/UNSAT/UNKNOWN)
- **Strict TypeScript/Python typing** - Enable all strict flags
- **Runtime validation** - Use zod/pydantic for API boundaries

## 3. Phase-by-Phase Implementation
Execute phases in order from the plan:
- Create feature flags FIRST (before any code)
- Implement monitoring/metrics BEFORE activating features
- Follow TDD rigorously
- Test each phase independently
- Only proceed to next phase after current phase success criteria met

## 4. File Organization
Follow SOLID principles:
- **Single Responsibility**: Each file/class has one job
- **Dependency Injection**: Services receive dependencies, not create them
- **Interface Segregation**: Small, focused interfaces
- **Code location**: Place code logically per project structure

Example structure:
```
backend/python/app/
  verification/
    __init__.py
    orchestrator.py        # Verification Orchestrator
    hupyy_client.py        # Hupyy API client
    models.py              # Request/response models
    types.py               # Enums, type aliases
  feedback/
    __init__.py
    qdrant_updater.py      # Update vector DB
    arangodb_updater.py    # Update knowledge graph
    pagerank_calculator.py # Recalculate PageRank
  tests/
    verification/
      test_orchestrator.py
      test_hupyy_client.py
    feedback/
      test_qdrant_updater.py
```

## 5. Error Handling
- **Never ignore errors** - Handle all error cases explicitly
- **Fail fast** - Validate inputs early
- **Error context** - Include meaningful context in error messages
- **Retry strategies** - Exponential backoff for transient failures
- **Circuit breakers** - Protect against cascading failures
- **Graceful degradation** - Search works even if verification fails

## 6. Configuration
- **Environment variables** - For all external service URLs, credentials
- **Feature flags** - Store in MongoDB config collection
- **Type-safe config** - Validate on startup, fail fast if misconfigured
- **Secrets management** - Never hardcode credentials

## 7. Monitoring & Observability
For each phase, add:
- **Metrics**: Prometheus-style counters, histograms, gauges
  - Verification requests/sec
  - Verification latency (p50, p95, p99)
  - SAT/UNSAT/UNKNOWN distribution
  - Error rates by type
- **Logging**: Structured JSON logs with correlation IDs
- **Tracing**: OpenTelemetry spans for distributed tracing
- **Alerts**: Thresholds for error rates, latency, throughput

## 8. Documentation
Update as you go:
- **API documentation**: OpenAPI specs for new endpoints
- **Architecture diagrams**: Mermaid diagrams for new components
- **README files**: In each new module directory
- **Migration guides**: How to enable/disable features
</implementation_requirements>

<constraints>
From CLAUDE.md:
- **SOLID, KISS, DRY, YAGNI, TRIZ principles**
- **TDD mandatory**: Tests before code
- **Strong typing**: No `any`, explicit types everywhere
- **Linting before commit**: Run all linters
- **Code review**: Separate subtask reviews changes
- **Git flow**: Commit and push after each phase
- **No database changes**: If schema exists, verify before touching
</constraints>

<execution_strategy>
**Use parallel subtasks extensively:**

1. **Phase setup** (parallel subtasks):
   - Create feature flag config
   - Set up monitoring metrics
   - Create test fixtures

2. **Phase implementation** (sequential within phase, but parallel where possible):
   - Write tests (can parallelize by component)
   - Implement code (sequential if dependencies exist)
   - Integration tests
   - Code review
   - Linting

3. **Phase verification**:
   - Run all tests
   - Verify success criteria
   - Document in SUMMARY.md
   - Git commit and push

**For maximum efficiency:**
- Spawn parallel subtasks when implementing independent components
- Use map-reduce approach for repetitive tasks
- Each subtask reports back briefly on what was done
- If any subtask encounters problems, spawn additional subtasks for research/experimentation
</execution_strategy>

<output_specification>
Create implementation artifacts:

1. **Code files** - Following project structure conventions
2. **Test files** - Unit and integration tests (TDD)
3. **Configuration files** - Feature flags, env vars, docker-compose updates
4. **Documentation** - README updates, API docs, migration guides

5. **SUMMARY.md** - Track progress:
   - **One-liner**: Current implementation status (e.g., "Phase 2 of 6 complete: Verification Orchestrator operational")
   - **Version**: Update per phase (v1, v2, etc.)
   - **Key Findings**: What worked, what didn't, lessons learned
   - **Files Created**: List all new files with brief descriptions
   - **Decisions Needed**: User input required to continue
   - **Blockers**: External impediments
   - **Next Step**: Next phase or final verification

Save all to appropriate locations per project structure.
Update SUMMARY.md in: `.prompts/003-hupyy-integration-implement/SUMMARY.md`
</output_specification>

<verification_per_phase>
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
</verification_per_phase>

<final_verification>
After all phases complete, verify:

□ Full integration tests passing
□ Load tests meet performance targets
□ Shadow mode validation shows Precision@5 improvement
□ All monitoring dashboards operational
□ All documentation complete
□ Rollback procedures tested
□ User acceptance criteria met
□ SUMMARY.md shows final status with next steps

Present final report to user with:
- What was implemented
- Test results and metrics
- Known limitations
- Recommended next steps (e.g., canary deployment)
</final_verification>

<success_criteria>
- All phases from plan implemented with TDD
- All tests passing (unit, integration, load)
- Type safety enforced throughout
- Monitoring and observability complete
- Feature flags working (can enable/disable at will)
- Documentation comprehensive
- Code reviewed and linted
- Git commits follow conventions
- SUMMARY.md provides clear implementation status
- System meets Precision@5 = 98% target (validated in shadow mode)
</success_criteria>
