<objective>
Design comprehensive test suite architecture and detailed specifications for Hupyy SMT verification integration testing. Create actionable test plan covering unit tests, integration tests, and Playwright UI automation based on research findings from prompt 026.
</objective>

<context>
**Research Foundation:**
Read `.prompts/026-hupyy-verification-testing-research/RESEARCH.md` and related research outputs to understand:
- Recommended testing tools and frameworks
- Best practices for API, Kafka, and UI testing
- Suggested architecture patterns
- Implementation priorities

**System Architecture:**
- **Frontend**: React/TypeScript with HupyyControls checkbox component
- **Backend NodeJS**: Express API (`es_controller.ts`, `es_validators.ts`)
- **Backend Python**: FastAPI with verification module (`hupyy_client.py`, `models.py`)
- **Message Queue**: Kafka topics (`verify_chunks`)
- **External API**: Hupyy service at `https://verticalslice-smt-service-gvav8.ondigitalocean.app`
- **Databases**: ArangoDB, MongoDB, Qdrant, Redis

**Existing Tests:**
- Python unit tests: `backend/python/tests/verification/test_hupyy_api_integration.py` (18 tests, 100% passing)
- No integration tests currently
- No UI automation tests currently
- No CI/CD workflows configured

**Testing Goals:**
1. Comprehensive coverage of verification flow
2. Fast, reliable, maintainable tests
3. CI/CD integration for automated quality gates
4. Clear test documentation and reporting
5. Minimal test flakiness

Read @CLAUDE.md for project conventions.
</context>

<requirements>

## Planning Outputs Required

### 1. Test Architecture Document

Create comprehensive test architecture covering:

**Test Pyramid:**
- Unit tests (70%): Fast, isolated, mocked dependencies
- Integration tests (20%): Service interactions, database operations
- E2E tests (10%): Full system verification, UI automation

**Test Layers:**
```
┌─────────────────────────────────────┐
│     E2E Tests (Playwright)          │ ← Full user workflows
├─────────────────────────────────────┤
│   Integration Tests (pytest + API)  │ ← Service boundaries
├─────────────────────────────────────┤
│   Unit Tests (pytest + Jest)        │ ← Individual functions
└─────────────────────────────────────┘
```

**Test Organization:**
- Directory structure for all test types
- Naming conventions for test files
- Test categorization (smoke, regression, etc.)
- Test execution order and dependencies

**Environment Strategy:**
- Local development testing
- CI/CD testing environment
- Mock vs. real dependencies per layer
- Test data management approach

### 2. Unit Test Specifications

Define unit tests for each component:

**Python Backend Tests:**

**File: `backend/python/tests/verification/test_models.py`**
- Test `HupyyRequest` model validation
  - Valid request construction
  - Field validation (informal_text required)
  - Default values (skip_formalization, enrich)
  - Invalid data handling
- Test `HupyyResponse` model
  - from_hupyy_process_response() transformation
  - check_sat_result → verdict mapping (SAT/UNSAT/UNKNOWN)
  - Confidence calculation from formalization_similarity
  - Metadata extraction (model, proof, smt_lib_code, formal_text)
  - Duration handling
- Test `VerificationResult` model
  - All field validations
  - Serialization/deserialization

**File: `backend/python/tests/verification/test_hupyy_client.py`**
- Test HupyyClient initialization
  - API URL configuration
  - Timeout settings
  - HTTP client setup
- Test verify_chunk() method
  - Request construction from VerificationChunk
  - HTTP request formatting
  - Response parsing success
  - Response parsing with missing fields
  - Timeout handling
  - Network error handling
  - HTTP error codes (404, 500, 503)
  - Retry logic (if implemented)
- Test API endpoint correctness
  - Verify calls to /pipeline/process not /verify
  - Verify request body format
  - Verify headers

**File: `backend/python/tests/verification/test_orchestrator.py`**
- Test Kafka message consumption
  - Message deserialization
  - Chunk extraction
  - Error handling for malformed messages
- Test verification workflow
  - Chunk verification orchestration
  - Result aggregation
  - Result storage
  - Error propagation

**TypeScript Backend Tests:**

**File: `backend/nodejs/apps/src/modules/enterprise_search/validators/es_validators.spec.ts`**
- Test validation schemas
  - verificationEnabled field validation
  - Default value (false)
  - Boolean type enforcement
  - Optional field handling

**File: `backend/nodejs/apps/src/modules/enterprise_search/controller/es_controller.spec.ts`**
- Test controller methods
  - verification_enabled extraction from request
  - Payload forwarding to Python backend
  - Response handling with verification results
  - Error handling when verification fails

**Frontend Tests:**

**File: `frontend/src/sections/qna/chatbot/components/HupyyControls.spec.tsx`**
- Test component rendering
  - Checkbox visibility
  - Tooltip content
  - Disabled state
- Test user interactions
  - Click toggles state
  - State persistence
  - Callback invocation (onToggle)
- Test accessibility
  - ARIA labels
  - Keyboard navigation

**Total Unit Tests Expected:** 50-80 tests across all files

### 3. Integration Test Specifications

Define integration tests for service interactions:

**File: `tests/integration/test_verification_flow.py`**

**Test Suite: End-to-End Verification Pipeline**

**Test: test_verification_request_through_nodejs_to_python**
- Setup: Start mock Hupyy API server
- Action: Send POST request to NodeJS API with verification_enabled=true
- Verify: Request forwarded to Python backend with correct payload
- Cleanup: Stop mock server

**Test: test_kafka_message_publishing**
- Setup: Embedded Kafka or mock Kafka consumer
- Action: Trigger verification through Python API
- Verify: Message published to verify_chunks topic with correct format
- Cleanup: Clear Kafka topics

**Test: test_hupyy_api_integration_with_mocked_responses**
- Setup: Mock Hupyy API with realistic responses
- Action: Call HupyyClient.verify_chunk() with test data
- Verify: Request format matches Hupyy spec, response parsed correctly
- Cleanup: Reset mocks

**Test: test_verification_result_storage**
- Setup: Test database instances
- Action: Complete verification workflow
- Verify: Results stored in correct database tables/collections
- Cleanup: Clear test data

**Test: test_verification_with_timeout**
- Setup: Mock Hupyy API with delayed response
- Action: Trigger verification with short timeout
- Verify: Timeout handled gracefully, error logged
- Cleanup: Reset mocks

**Test: test_verification_error_handling**
- Setup: Mock Hupyy API returning errors (404, 500, invalid JSON)
- Action: Trigger verification
- Verify: Errors handled, fallback behavior works, no crashes
- Cleanup: Reset mocks

**Test: test_concurrent_verification_requests**
- Setup: Mock Hupyy API, Kafka
- Action: Send multiple verification requests in parallel
- Verify: All requests processed, no race conditions, correct results
- Cleanup: Clear all test data

**File: `tests/integration/test_api_contracts.py`**

**Test Suite: API Contract Validation**

**Test: test_hupyy_api_contract_compliance**
- Setup: Load Hupyy OpenAPI spec from URL
- Action: Generate test requests based on spec
- Verify: All requests match spec, responses validate against spec
- Uses: Schemathesis or Dredd for contract testing

**Total Integration Tests Expected:** 15-25 tests

### 4. Playwright E2E Test Specifications

Define comprehensive UI automation tests:

**File: `tests/e2e/verification/verification-ui.spec.ts`**

**Test Suite: Verification Checkbox**

**Test: should display verification checkbox in active conversation**
- Navigate to chat page
- Login
- Click existing conversation or create new one
- Verify checkbox visible
- Screenshot: `test-results/verification-checkbox-visible.png`

**Test: should hide verification checkbox on welcome screen**
- Navigate to chat page
- Verify checkbox NOT visible
- Navigate to conversation
- Verify checkbox visible

**Test: should toggle verification checkbox**
- Navigate to conversation
- Click checkbox → verify checked state
- Click checkbox → verify unchecked state
- Verify state persistence (refresh page, check state)

**Test: should show tooltip on checkbox hover**
- Navigate to conversation
- Hover over checkbox
- Verify tooltip: "SMT verification uses formal logic to verify search results"

**Test: should disable checkbox when conversation loading**
- Navigate to conversation
- Trigger loading state (send message)
- Verify checkbox disabled during loading
- Verify checkbox enabled after loading

**Test Suite: Chat with Verification**

**Test: should send query without verification when checkbox unchecked**
- Navigate to conversation
- Ensure checkbox unchecked
- Type query: "What is the LLM optimization module?"
- Send query
- Intercept network request
- Verify: verification_enabled=false in payload
- Verify: Response received and displayed
- Screenshot: `test-results/chat-without-verification.png`

**Test: should send query with verification when checkbox checked**
- Navigate to conversation
- Check verification checkbox
- Type query: "What is the LLM optimization module?"
- Send query
- Intercept network request
- Verify: verification_enabled=true in payload
- Verify: Response received
- Screenshot: `test-results/chat-with-verification.png`

**Test: should display verification results in chat**
- Setup: Mock API with verification results
- Navigate to conversation
- Enable verification
- Send query
- Wait for response
- Verify: Verification badges/indicators visible (if UI implemented)
- Verify: Proof details accessible (if UI implemented)
- Screenshot: `test-results/verification-results-displayed.png`

**Test: should handle verification errors gracefully**
- Setup: Mock API to return verification error
- Navigate to conversation
- Enable verification
- Send query
- Verify: Error message displayed (or graceful degradation)
- Verify: Chat still functional
- Screenshot: `test-results/verification-error-handling.png`

**Test Suite: Verification State Persistence**

**Test: should persist checkbox state across page refreshes**
- Navigate to conversation
- Check checkbox
- Refresh page
- Verify: Checkbox still checked

**Test: should reset checkbox state on new conversation**
- Navigate to conversation
- Check checkbox
- Create new conversation
- Verify: Checkbox unchecked (or follows default)

**Test Suite: Accessibility**

**Test: should be keyboard accessible**
- Navigate to conversation
- Tab to checkbox
- Press Space to toggle
- Verify: State changes

**Test: should have proper ARIA labels**
- Navigate to conversation
- Verify: Checkbox has aria-label or aria-labelledby
- Verify: Tooltip has aria-describedby

**File: `tests/e2e/verification/verification-integration.spec.ts`**

**Test Suite: Full Verification Flow**

**Test: should complete full verification workflow**
- Setup: Start all services (Docker Compose)
- Navigate to chat
- Enable verification
- Send query
- Wait for response
- Check backend logs for:
  - "Published X chunks for verification"
  - "Calling Hupyy API"
  - "Hupyy API response received"
- Verify: No errors in logs
- Verify: Response contains expected data

**Test: should handle Hupyy API timeout**
- Setup: Mock Hupyy API with 30s delay
- Navigate to chat
- Enable verification
- Send query
- Verify: Timeout handled, user sees fallback
- Verify: Chat remains functional

**Total E2E Tests Expected:** 15-20 tests

### 5. Test Data Management Plan

**Fixtures Strategy:**

**Python Fixtures (`tests/fixtures/verification_fixtures.py`):**
```python
@pytest.fixture
def sample_verification_chunk():
    return VerificationChunk(...)

@pytest.fixture
def mock_hupyy_response():
    return {
        "check_sat_result": "SAT",
        "formalization_similarity": 0.92,
        "proof": {...},
        ...
    }

@pytest.fixture
def hupyy_client(mocker):
    return HupyyClient(api_url="http://mock-hupyy")
```

**Playwright Fixtures (`tests/e2e/fixtures/auth.fixture.ts`):**
```typescript
export const authenticatedPage = async ({ page }) => {
  await page.goto('http://localhost:3000');
  await login(page, 'af@o2.services', 'Vilisaped1!');
  return page;
};
```

**Test Data Factories:**

**Python Factory (`tests/factories/verification_factory.py`):**
```python
class VerificationChunkFactory:
    @staticmethod
    def create(informal_text: str = "Test query", **kwargs):
        return VerificationChunk(
            informal_text=informal_text,
            **kwargs
        )
```

**Mock Data:**
- Store mock Hupyy responses in `tests/fixtures/mock_hupyy_responses.json`
- Store test queries in `tests/fixtures/test_queries.json`
- Store expected results in `tests/fixtures/expected_results.json`

### 6. CI/CD Integration Plan

**GitHub Actions Workflow** (`.github/workflows/test-verification.yml`):

```yaml
name: Verification Tests

on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [develop, main]

jobs:
  unit-tests-python:
    runs-on: ubuntu-latest
    steps:
      - Checkout code
      - Setup Python 3.11
      - Install dependencies
      - Run pytest with coverage
      - Upload coverage to Codecov

  unit-tests-typescript:
    runs-on: ubuntu-latest
    steps:
      - Checkout code
      - Setup Node.js 18
      - Install dependencies
      - Run Jest/Vitest with coverage
      - Upload coverage to Codecov

  integration-tests:
    runs-on: ubuntu-latest
    services:
      kafka:
        image: confluentinc/cp-kafka:7.9.0
      ...
    steps:
      - Checkout code
      - Setup Python + Node.js
      - Start test services
      - Run integration tests
      - Collect logs on failure

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - Checkout code
      - Setup Node.js
      - Install Playwright browsers
      - Start application (Docker Compose)
      - Run Playwright tests
      - Upload screenshots/videos on failure
      - Upload Playwright report

  coverage-report:
    needs: [unit-tests-python, unit-tests-typescript, integration-tests, e2e-tests]
    runs-on: ubuntu-latest
    steps:
      - Merge coverage reports
      - Comment on PR with coverage stats
      - Enforce coverage threshold (80%)
```

**Quality Gates:**
- Unit test coverage: ≥80%
- Integration test coverage: ≥60%
- All tests must pass before merge
- No flaky tests (retry limit: 2)
- Performance: E2E tests complete in <10 minutes

### 7. Test Execution Plan

**Local Development:**
```bash
# Unit tests only (fast feedback)
npm run test:unit

# Integration tests (requires Docker)
npm run test:integration

# E2E tests (requires full stack)
npm run test:e2e

# All tests
npm run test:all
```

**CI/CD Execution:**
- Every commit: Unit tests
- Every PR: Unit + Integration tests
- Before merge: All tests including E2E
- Nightly: Full test suite + performance tests

**Test Reporting:**
- JUnit XML for test results
- HTML reports for Playwright
- Coverage reports (Codecov)
- Test trend tracking (GitHub Actions artifacts)

</requirements>

<output>

Create the following files in `.prompts/027-hupyy-verification-testing-plan/`:

### 1. TEST-ARCHITECTURE.md

Comprehensive architecture document covering:
- Test pyramid and layer breakdown
- Directory structure for all test types
- Test organization and naming conventions
- Environment strategy (local, CI, production)
- Mock vs. real dependencies per layer
- Test data management approach
- Parallel execution strategy

### 2. UNIT-TEST-SPECS.md

Detailed specifications for all unit tests:
- Python backend tests (models, client, orchestrator)
- TypeScript backend tests (validators, controllers)
- Frontend tests (components, hooks)
- Expected test count per file
- Test naming conventions
- Mock/stub requirements
- Coverage targets

### 3. INTEGRATION-TEST-SPECS.md

Detailed specifications for integration tests:
- API integration tests
- Kafka message flow tests
- Database interaction tests
- Error handling scenarios
- Contract testing approach
- Test environment setup
- Expected test count
- Data isolation strategy

### 4. E2E-TEST-SPECS.md

Detailed Playwright test specifications:
- Verification checkbox tests
- Chat interaction tests
- State persistence tests
- Error handling tests
- Accessibility tests
- Full workflow tests
- Screenshot/video capture strategy
- Expected test count
- Page Object Model structure

### 5. TEST-DATA-PLAN.md

Test data management strategy:
- Fixture organization
- Factory patterns
- Mock data storage
- Test database seeding
- Data cleanup strategy
- Realistic test query examples
- Mock Hupyy response examples

### 6. CI-CD-PLAN.md

CI/CD integration plan:
- GitHub Actions workflow YAML
- Test execution matrix
- Environment variable configuration
- Secret management
- Test parallelization
- Artifact collection
- Coverage reporting
- Quality gates
- Flaky test handling

### 7. IMPLEMENTATION-CHECKLIST.md

Step-by-step implementation checklist:

**Phase 1: Foundation (Week 1)**
- [ ] Set up test directory structure
- [ ] Configure pytest and Jest
- [ ] Create base fixtures
- [ ] Implement test data factories
- [ ] Configure coverage reporting

**Phase 2: Unit Tests (Week 2)**
- [ ] Python verification module tests
- [ ] TypeScript controller tests
- [ ] Frontend component tests
- [ ] Achieve 80% coverage

**Phase 3: Integration Tests (Week 3)**
- [ ] Mock Hupyy API server
- [ ] Kafka integration tests
- [ ] API contract tests
- [ ] Database integration tests

**Phase 4: E2E Tests (Week 4)**
- [ ] Playwright setup and configuration
- [ ] Page Object Models
- [ ] Verification checkbox tests
- [ ] Full workflow tests
- [ ] Accessibility tests

**Phase 5: CI/CD (Week 5)**
- [ ] GitHub Actions workflow
- [ ] Test parallelization
- [ ] Coverage reporting
- [ ] Quality gates
- [ ] Documentation

### 8. TEST-SCENARIOS.md

Concrete test scenarios with example data:

**Scenario 1: Successful Verification**
- Input query: "All prime numbers greater than 2 are odd"
- Expected Hupyy response: SAT
- Expected UI: Verification badge, proof summary

**Scenario 2: Failed Verification**
- Input query: "2 + 2 = 5"
- Expected Hupyy response: UNSAT
- Expected UI: Verification failed badge

**Scenario 3: Unknown Verification**
- Input query: "Complex undecidable statement"
- Expected Hupyy response: UNKNOWN
- Expected UI: Verification inconclusive

**Scenario 4: Timeout**
- Input query: "Very complex query"
- Mock: Hupyy API delay 30s
- Expected: Timeout after configured interval
- Expected UI: Graceful degradation

**Scenario 5: Hupyy API Error**
- Input query: "Any query"
- Mock: Hupyy API returns 500
- Expected: Error logged, user sees fallback
- Expected UI: Chat continues without verification

</output>

<success_criteria>

Planning is complete when:

- ✅ Test architecture clearly defined with diagrams
- ✅ All test specifications written with expected counts
- ✅ Test data strategy documented with examples
- ✅ CI/CD plan includes complete workflow YAML
- ✅ Implementation checklist provides clear roadmap
- ✅ Test scenarios cover all critical paths
- ✅ Coverage targets defined per test type
- ✅ Quality gates and enforcement mechanisms specified
- ✅ Research findings from prompt 026 incorporated
- ✅ Ready to proceed to implementation phase with clear blueprint

</success_criteria>

<notes>

## Planning Principles

1. **Testability First** - Design tests to be fast, isolated, deterministic
2. **Maintainability** - Clear naming, good organization, reusable fixtures
3. **Coverage Balance** - More unit tests, fewer E2E tests (test pyramid)
4. **Realistic Scenarios** - Test real-world use cases, not just happy paths
5. **CI-Ready** - All tests must run in CI without manual intervention

## Common Pitfalls to Avoid

- **Too many E2E tests** - Slow, flaky, expensive to maintain
- **Insufficient unit tests** - Miss edge cases, harder debugging
- **Hard-coded test data** - Use factories and fixtures instead
- **No test isolation** - Tests interfere with each other
- **Ignoring flaky tests** - Address root cause immediately
- **No negative testing** - Test error paths and edge cases

## Key Decisions to Document

- Mock vs. real Hupyy API (recommend mock for CI, optional real for nightly)
- Embedded vs. real Kafka (recommend embedded for integration tests)
- Test database strategy (recommend Docker containers with test data)
- Playwright headed vs. headless (headless for CI, headed for debugging)

</notes>
