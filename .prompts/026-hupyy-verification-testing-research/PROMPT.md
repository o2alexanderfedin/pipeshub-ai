<objective>
Research and document best practices, patterns, and strategies for testing SMT (Satisfiability Modulo Theories) verification systems integrated with full-stack applications. Provide comprehensive technical foundation for implementing automated test suites covering unit tests, integration tests, and UI automation.
</objective>

<context>
**Current System:**
- **Frontend**: React/TypeScript with verification checkbox UI component
- **Backend NodeJS**: Express API receiving verification requests
- **Backend Python**: FastAPI handling Hupyy API integration
- **Message Queue**: Kafka for async verification workflow
- **External Service**: Hupyy SMT verification API at Digital Ocean
- **UI Testing**: Playwright already installed and configured

**Verification Flow:**
1. User checks verification checkbox in chat interface
2. Frontend sends query with `verification_enabled: true`
3. NodeJS validates and forwards to Python backend
4. Python publishes chunks to Kafka `verify_chunks` topic
5. Orchestrator consumes messages and calls Hupyy API `/pipeline/process`
6. Hupyy returns `{check_sat_result, formalization_similarity, proof, ...}`
7. Python transforms response to internal `{verdict, confidence, metadata}`
8. Results stored and displayed in UI

**Testing Challenges:**
- External API dependency (Hupyy service)
- Async message processing (Kafka)
- Complex data transformations
- Multi-language stack (TypeScript + Python)
- End-to-end flow validation
- UI interaction testing

Read @CLAUDE.md for project conventions.
</context>

<requirements>

## Research Areas

### 1. Testing External API Integrations

Research best practices for testing systems that depend on external APIs:

**Topics to investigate:**
- Mock vs. stub vs. fake for external services
- Contract testing (Pact, Dredd, or similar)
- VCR/cassette patterns for recording API interactions
- Testing retry logic and circuit breakers
- Handling API rate limits in tests
- Environment-specific configuration (dev/test/prod)

**Specific questions to answer:**
- How to test Hupyy API integration without hitting rate limits?
- Should we mock the Hupyy service or use a test instance?
- How to validate request/response transformations?
- How to test timeout and error scenarios?

**Output:**
- Document pros/cons of each approach
- Recommend specific testing strategy for Hupyy integration
- Identify Python libraries for API testing (pytest plugins, etc.)
- Identify TypeScript/JavaScript libraries for API mocking

### 2. Testing Kafka Message Flows

Research testing strategies for Kafka-based asynchronous workflows:

**Topics to investigate:**
- Embedded Kafka for tests (testcontainers)
- Kafka mocking libraries
- Testing consumer offset management
- Testing message serialization/deserialization
- Testing idempotency and duplicate handling
- Integration test patterns for producers/consumers

**Specific questions to answer:**
- How to test Kafka publishing without running full Kafka cluster?
- How to verify messages are consumed and processed correctly?
- How to test consumer rebalancing scenarios?
- How to test message ordering and delivery guarantees?

**Output:**
- Document testing patterns for Kafka workflows
- Recommend specific approach (embedded vs. mock vs. real)
- Identify Python Kafka testing libraries
- Provide example test structure for producer/consumer tests

### 3. Full-Stack Integration Testing

Research strategies for testing across multiple services and languages:

**Topics to investigate:**
- Integration test frameworks for multi-language stacks
- Docker Compose for test environments
- API contract testing between services
- Database state management in tests
- Test data fixtures and factories
- Parallel test execution

**Specific questions to answer:**
- How to set up test environment with all dependencies?
- How to ensure tests are isolated and repeatable?
- How to manage test data across services?
- How to balance test speed vs. completeness?

**Output:**
- Document integration testing architecture
- Recommend test environment setup (Docker, testcontainers, etc.)
- Identify tools for cross-service testing
- Provide example integration test scenario

### 4. Playwright UI Testing Best Practices

Research advanced Playwright patterns for complex UI testing:

**Topics to investigate:**
- Page Object Model (POM) vs. other patterns
- Testing async operations and loading states
- Visual regression testing
- Accessibility testing with Playwright
- Cross-browser testing strategies
- CI/CD integration for Playwright tests
- Testing WebSocket connections and real-time updates

**Specific questions to answer:**
- How to structure Playwright tests for maintainability?
- How to test verification checkbox state and persistence?
- How to verify chat responses contain verification results?
- How to handle flaky tests and timing issues?
- How to test error states and edge cases in UI?

**Output:**
- Document Playwright testing patterns and anti-patterns
- Recommend project structure for Playwright tests
- Identify useful Playwright plugins and utilities
- Provide example test scenarios for verification UI

### 5. Test Data and Fixture Management

Research strategies for managing test data in complex systems:

**Topics to investigate:**
- Factory patterns for test data generation
- Database seeding and teardown
- Fixture management across multiple databases
- Test data versioning
- Synthetic data generation for SMT queries
- Deterministic vs. random test data

**Specific questions to answer:**
- How to create realistic test queries for verification?
- How to generate valid SMT responses for testing?
- How to manage test data lifecycle (setup/teardown)?
- How to ensure tests don't interfere with each other?

**Output:**
- Document test data management strategy
- Recommend libraries for fixture management (Python + TypeScript)
- Provide examples of test data factories
- Define test data requirements for verification testing

### 6. CI/CD Integration and Test Automation

Research CI/CD best practices for comprehensive test automation:

**Topics to investigate:**
- GitHub Actions for multi-language projects
- Test parallelization and matrix builds
- Test reporting and coverage visualization
- Playwright in CI (headed vs. headless)
- Artifact retention (screenshots, videos)
- Flaky test detection and retry strategies
- Performance benchmarking in CI

**Specific questions to answer:**
- How to run Python + TypeScript tests in single workflow?
- How to configure Playwright for CI environment?
- How to report test failures with useful debugging info?
- How to handle secrets and environment variables?
- How to enforce test coverage thresholds?

**Output:**
- Document CI/CD pipeline architecture
- Provide GitHub Actions workflow examples
- Recommend test coverage and reporting tools
- Define quality gates for PR merges

### 7. SMT-Specific Testing Considerations

Research testing strategies specific to SMT verification systems:

**Topics to investigate:**
- Testing formal logic transformations
- Validating SAT/UNSAT/UNKNOWN results
- Testing proof generation and validation
- Formalization similarity scoring
- Error handling for malformed inputs
- Testing with various SMT theories (QF_LIA, QF_LRA, etc.)

**Specific questions to answer:**
- How to validate that SMT results are correct?
- How to test edge cases in natural language → formal logic?
- How to verify proof soundness and completeness?
- How to test against known valid/invalid queries?

**Output:**
- Document SMT-specific test requirements
- Provide examples of SMT test cases
- Recommend validation strategies
- Define correctness criteria for SMT verification

</requirements>

<research_methodology>

## Research Sources

1. **Official Documentation**
   - Playwright documentation (testing patterns, best practices)
   - pytest documentation (fixtures, plugins, parametrization)
   - Kafka testing documentation
   - Pydantic validation testing
   - FastAPI testing guides

2. **Industry Best Practices**
   - Martin Fowler's testing articles (test pyramid, integration testing)
   - Google Testing Blog (test patterns at scale)
   - Thoughtworks Technology Radar (testing tools and techniques)
   - Test Automation University courses

3. **Open Source Examples**
   - Search GitHub for similar SMT/formal verification projects
   - Find exemplary Playwright test suites
   - Study Kafka testing in popular projects
   - Review multi-language test automation setups

4. **Technical Blogs and Articles**
   - Search for "testing external API integrations"
   - Search for "Playwright best practices 2025"
   - Search for "testing Kafka consumers pytest"
   - Search for "integration testing microservices"

## Research Process

For each research area:

1. **Web Search** - Use WebSearch tool to find recent articles and documentation
2. **Code Examples** - Search GitHub for real-world implementations
3. **Documentation Review** - Read official docs for recommended patterns
4. **Synthesis** - Combine findings into actionable recommendations
5. **Validation** - Cross-reference multiple sources for consistency

## Output Format

For each research area, create a section in RESEARCH.md with:

```markdown
## [Research Area Name]

### Summary
[1-2 paragraph overview of findings]

### Key Findings
- [Bullet point finding 1]
- [Bullet point finding 2]
- [...]

### Recommended Approach
[Specific recommendation for our use case]

### Tools and Libraries
- **[Tool Name]**: [Purpose and why recommended]
- [...]

### Example Code
```language
[Code snippet demonstrating recommended pattern]
```

### References
- [Link to documentation/article 1]
- [Link to documentation/article 2]
- [...]
```

</research_methodology>

<output>

Create the following files in `.prompts/026-hupyy-verification-testing-research/`:

### 1. RESEARCH.md

Comprehensive research findings covering all 7 research areas:

1. Testing External API Integrations
2. Testing Kafka Message Flows
3. Full-Stack Integration Testing
4. Playwright UI Testing Best Practices
5. Test Data and Fixture Management
6. CI/CD Integration and Test Automation
7. SMT-Specific Testing Considerations

Each section should include:
- Summary of findings
- Key insights and best practices
- Recommended approach for PipesHub
- Tools and libraries to use
- Code examples
- References to sources

### 2. RECOMMENDATIONS.md

Executive summary with concrete recommendations:

**Testing Strategy:**
- Overall testing approach (test pyramid, layers)
- Unit test strategy (coverage targets, frameworks)
- Integration test strategy (scope, fixtures)
- E2E test strategy (critical paths)
- UI test strategy (Playwright patterns)

**Tooling Decisions:**
- Python testing: pytest + recommended plugins
- TypeScript testing: Jest/Vitest + recommended libraries
- API mocking: Recommended tools for Hupyy
- Kafka testing: Recommended approach
- CI/CD: GitHub Actions configuration

**Architecture Decisions:**
- Test environment setup (Docker, testcontainers, etc.)
- Test data management strategy
- Fixture patterns
- Test isolation approach
- Parallel execution strategy

**Implementation Priorities:**
- Phase 1: Essential tests (what to build first)
- Phase 2: Enhanced coverage (what to add next)
- Phase 3: Advanced features (nice-to-have tests)

### 3. TOOLS-AND-LIBRARIES.md

Comprehensive list of recommended testing tools:

**Python Testing:**
- pytest plugins (pytest-asyncio, pytest-kafka, pytest-mock, etc.)
- API testing libraries (httpx, respx, vcr.py, etc.)
- Data generation libraries (Faker, factory_boy, etc.)

**TypeScript Testing:**
- Testing frameworks (Jest, Vitest)
- Mocking libraries (MSW, nock, etc.)
- Assertion libraries
- Test utilities

**Playwright:**
- Useful plugins and extensions
- Reporting tools
- Visual testing addons

**CI/CD:**
- GitHub Actions workflows
- Test reporters
- Coverage tools

**Infrastructure:**
- Docker for test environments
- testcontainers
- Database utilities

### 4. EXAMPLES.md

Concrete code examples demonstrating recommended patterns:

1. **Mocking Hupyy API in Python**
   - Using pytest fixtures
   - Using respx for HTTP mocking
   - Using VCR for recording/replaying

2. **Testing Kafka Publishing/Consuming**
   - Embedded Kafka example
   - Mock Kafka example
   - Integration test with real Kafka

3. **Playwright Test Structure**
   - Page Object Model example
   - Testing verification checkbox
   - Testing chat with verification enabled
   - Handling async operations

4. **Integration Test Setup**
   - Docker Compose for test environment
   - Fixture management
   - Test data factories

5. **CI/CD Workflow**
   - GitHub Actions YAML example
   - Running all test types
   - Artifact collection

</output>

<success_criteria>

Research is complete when:

- ✅ All 7 research areas thoroughly investigated
- ✅ Multiple sources consulted per area (3+ sources minimum)
- ✅ Specific tools and libraries identified with justification
- ✅ Code examples provided for each major pattern
- ✅ Concrete recommendations with rationale documented
- ✅ Trade-offs and alternatives discussed
- ✅ All outputs created (RESEARCH.md, RECOMMENDATIONS.md, TOOLS-AND-LIBRARIES.md, EXAMPLES.md)
- ✅ References properly cited for future verification
- ✅ Ready to proceed to planning phase with solid technical foundation

</success_criteria>

<notes>

## Why Research Phase Matters

Before diving into implementation, we need to:

1. **Avoid costly mistakes** - Choose right tools upfront
2. **Learn from others** - Don't reinvent solved problems
3. **Build consensus** - Document technical decisions
4. **Ensure completeness** - Cover all testing dimensions
5. **Enable planning** - Research informs architecture

## Focus Areas

Pay special attention to:

- **Playwright patterns** - User specifically requested UI automation
- **API mocking** - Critical for testing Hupyy integration without rate limits
- **Kafka testing** - Async messaging is core to verification flow
- **CI/CD integration** - Tests must run automatically

## Time Investment

Thorough research now saves implementation time later. Expect:

- 2-3 hours for comprehensive web research
- 1-2 hours reviewing code examples
- 1 hour synthesizing findings
- Total: 4-6 hours for high-quality research output

This investment prevents weeks of rework from poor initial choices.

</notes>
