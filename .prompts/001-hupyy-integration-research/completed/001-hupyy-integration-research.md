<objective>
Research and analyze all technical, architectural, and risk aspects of integrating Hupyy's SMT verification service into PipesHub's search pipeline.

This research will inform the implementation plan and ensure we identify all integration points, potential issues, and optimal architecture before development begins.
</objective>

<context>
PipesHub is a RAG (Retrieval-Augmented Generation) system with:
- Qdrant for vector search
- ArangoDB for knowledge graph and PageRank
- MongoDB for user configuration
- Kafka for event messaging
- Node.js API layer + Python backend connectors

Hupyy is an SMT verification service that:
- Converts natural language to formal logic (SMT-LIB)
- Verifies constraints with Z3/cvc5 solvers
- Returns SAT/UNSAT/UNKNOWN verdicts with confidence scores
- API: https://verticalslice-smt-service-gvav8.ondigitalocean.app/openapi.json

Architecture reference: @/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/docs/hupyy-pipeshub-integration-architecture.md
</context>

<research_requirements>
Thoroughly analyze and document:

## 1. Technical Integration Details
- Hupyy API contract: endpoints, request/response schemas, rate limits
- Error handling requirements: timeout strategies, retry logic, circuit breakers
- Authentication and security considerations
- Data serialization/deserialization requirements
- Performance characteristics: typical response times, throughput limits

## 2. Architecture Decisions
- Where to place the Verification Orchestrator service (new microservice vs. existing service)
- Hupyy Integration Service architecture (Python/Node.js, async/sync, worker pool size)
- Kafka topic design for verification events
- Database schema changes needed (Qdrant payload, ArangoDB metadata)
- Event flow design: when to trigger verification, batching strategy

## 3. Implementation Risks & Dependencies
- Breaking changes to existing search pipeline
- Migration path for existing data (re-indexing strategy)
- Backward compatibility requirements (can old and new coexist?)
- Testing strategy: unit tests, integration tests, load tests
- Deployment dependencies: infrastructure requirements, config management
- Monitoring and observability: metrics, logs, traces, alerts

## 4. Data Flow Analysis
- How search results flow through the verification pipeline
- How verification results feed back into ranking
- Cold start problem: what happens before verification data exists?
- Failure modes: how to handle UNKNOWN verdicts, timeouts, service unavailability

## 5. Quality & Performance Targets
- From architecture: Target Precision@5 = 98%
- Ranking formula weights: Semantic (45%) + PageRank (30%) + Verification (15%) + Historical (10%)
- Acceptable latency impact on search queries
- Verification throughput requirements
</research_requirements>

<research_sources>
Primary sources:
- Architecture document (already provided)
- Hupyy OpenAPI spec (fetch and analyze)
- PipesHub codebase:
  - @backend/python/app/ - Python services structure
  - @backend/nodejs/apps/ - Node.js API layer
  - @deployment/docker-compose/ - Infrastructure setup

Use WebSearch for:
- Best practices for SMT solver integration
- Kafka event-driven architecture patterns
- Circuit breaker and retry strategies for external services
- Vector database metadata update strategies
</research_sources>

<output_specification>
Create two files:

1. **hupyy-integration-research.md** - Full research with XML metadata:
   ```xml
   <confidence>High/Medium/Low - based on source quality</confidence>
   <dependencies>
   - List technical dependencies identified
   - List blocking decisions needed before proceeding
   </dependencies>
   <open_questions>
   - Unanswered questions requiring user input or further investigation
   </open_questions>
   <assumptions>
   - Assumptions made during research
   - Things presumed about the existing system or requirements
   </assumptions>
   ```

   Content structure:
   - Executive Summary
   - Technical Integration Analysis
   - Architecture Recommendations
   - Risk Assessment
   - Data Flow Design
   - Performance & Quality Targets
   - Implementation Checklist
   - References (all sources with URLs)

2. **SUMMARY.md** - Executive summary for quick scanning:
   - **One-liner**: Substantive description of findings (not "Research completed")
   - **Version**: v1
   - **Key Findings**: Top 3-5 actionable insights
   - **Decisions Needed**: User decisions required before planning
   - **Blockers**: External impediments (if any)
   - **Next Step**: Concrete action to move forward

Save to: `.prompts/001-hupyy-integration-research/`
</output_specification>

<verification_checklist>
Before declaring research complete, verify:

□ Hupyy API fully analyzed (all endpoints, schemas, error cases)
□ Integration points in PipesHub identified with file references
□ Database schema changes specified (Qdrant, ArangoDB, MongoDB if needed)
□ Kafka event flow designed (topics, producers, consumers)
□ Error handling strategy defined (retries, timeouts, fallbacks)
□ Testing strategy outlined (unit, integration, load)
□ Migration path documented (backward compatibility, rollback)
□ Monitoring requirements specified (metrics, logs, alerts)
□ All assumptions explicitly stated
□ All open questions documented
□ Sources cited with URLs
□ Confidence level assigned with justification
</verification_checklist>

<quality_requirements>
Research must meet these standards:

1. **Verification**: Critical claims verified with official documentation or codebase
2. **Specificity**: File paths, function names, API endpoints - not vague descriptions
3. **Actionability**: Findings directly inform planning decisions
4. **Completeness**: All required sections covered with substantive content
5. **Traceability**: Every recommendation traceable to a source or analysis

Create a quality report section distinguishing:
- ✓ Verified claims (with source)
- ⚠ Inferred from architecture doc (assumption)
- ? Requires user confirmation
</quality_requirements>

<success_criteria>
- All 5 research areas thoroughly analyzed
- Specific integration points identified with file references
- Clear architecture recommendations with trade-offs
- Risk assessment with mitigation strategies
- Open questions documented for user decisions
- Quality checklist completed
- SUMMARY.md provides actionable executive view
- Next step clearly defined (create plan)
</success_criteria>
