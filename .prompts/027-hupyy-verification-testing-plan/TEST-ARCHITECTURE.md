# Test Architecture for Hupyy SMT Verification Integration

**Date:** November 30, 2025
**Project:** PipesHub AI - Hupyy SMT Verification Integration
**Purpose:** Comprehensive test architecture defining test pyramid, structure, and execution strategy

---

## Executive Summary

This document defines the complete test architecture for the Hupyy SMT verification integration. The architecture follows the **testing pyramid principle**, with a solid foundation of unit tests (70%), supported by integration tests (20%), and capped by focused end-to-end tests (10%).

**Key Architectural Principles:**
1. **Fast Feedback** - Majority of tests run in <2 minutes
2. **Test Isolation** - Each test runs independently with clean state
3. **Realistic Testing** - Use real dependencies where valuable
4. **Maintainability** - Clear structure, naming conventions, and reusable components
5. **CI/CD Optimization** - Parallel execution and intelligent test splitting

---

## 1. Test Pyramid

### Visual Representation

```
                    /\
                   /  \
                  / E2E \           ~15-20 tests (10%)
                 /--------\          Playwright full workflows
                /          \         Docker Compose stack
               / Contract   \       ~10-15 tests (5%)
              /--------------\       Pact API contracts
             /                \
            /   Integration     \   ~20-30 tests (20%)
           /--------------------\   Testcontainers + VCR
          /                      \  Kafka, DB, External APIs
         /                        \
        /        Unit Tests         \  ~60-90 tests (70%)
       /------------------------------\ pytest + Jest/Vitest
      /   Mocks, Stubs, Pure Functions \
```

### Distribution Breakdown

| Layer | Test Count | % of Total | Execution Time | Scope |
|-------|-----------|------------|----------------|-------|
| **Unit Tests** | 60-90 | 70% | <2 min | Individual functions/classes |
| **Integration Tests** | 20-30 | 20% | <5 min | Service interactions, DB, Kafka |
| **Contract Tests** | 10-15 | 5% | <1 min | API compatibility |
| **E2E Tests** | 15-20 | 5% | <3 min | Complete user workflows |
| **Total** | 105-155 | 100% | <10 min | Full test suite |

### Layer Responsibilities

#### Unit Tests (70%)
**Purpose:** Validate individual components in isolation

**Characteristics:**
- Pure functions tested with various inputs
- External dependencies mocked or stubbed
- Fast execution (<100ms per test)
- No network calls, no database access
- Deterministic results

**Technologies:**
- Python: `pytest` with `unittest.mock`
- TypeScript: `Jest` or `Vitest` with mocks
- Frontend: `@testing-library/react`

**Examples:**
- `HupyyRequest` model validation
- `verify_chunk()` method with mocked HTTP client
- React component rendering and interactions
- Validator schema enforcement

---

#### Integration Tests (20%)
**Purpose:** Validate interactions between services and external systems

**Characteristics:**
- Real or realistic dependencies (Testcontainers)
- Tests cross-service communication
- Validates message flows and data persistence
- Medium execution time (1-5s per test)
- Isolated test data

**Technologies:**
- Python: `pytest` + `testcontainers-python`
- Kafka: Testcontainers Kafka module
- External APIs: `pytest-recording` (VCR pattern)
- Database: Testcontainers PostgreSQL

**Examples:**
- Kafka producer → consumer flow
- NodeJS API → Python FastAPI communication
- Hupyy API integration with recorded responses
- Database CRUD operations with verification results

---

#### Contract Tests (5%)
**Purpose:** Ensure API compatibility between consumer and provider

**Characteristics:**
- Consumer-driven contracts (Pact)
- Validates API shape and behavior
- Independent service deployment validation
- Fast execution (<500ms per test)
- Version-controlled contracts

**Technologies:**
- Consumer: `@pact-foundation/pact` (TypeScript)
- Provider: `pact-python` (Python)
- Pact Broker for contract storage (optional)

**Examples:**
- NodeJS → Python API contract
- Python → Hupyy API contract (consumer side)
- Request/response format validation

---

#### E2E Tests (5%)
**Purpose:** Validate complete user workflows from UI to backend

**Characteristics:**
- Full application stack running
- Real browser automation (Playwright)
- Tests critical user journeys
- Slower execution (5-30s per test)
- Screenshots and video capture on failure

**Technologies:**
- `@playwright/test` with TypeScript
- Page Object Model pattern
- Docker Compose for full stack
- Visual regression testing (optional)

**Examples:**
- Enable verification → send query → view results
- Checkbox state persistence across page refresh
- Error handling for failed verification
- Accessibility validation

---

## 2. Directory Structure

### Complete Test Organization

```
pipeshub-ai-orig/
├── backend/
│   ├── nodejs/
│   │   └── apps/
│   │       └── src/
│   │           └── modules/
│   │               └── enterprise_search/
│   │                   ├── controller/
│   │                   │   ├── es_controller.ts
│   │                   │   └── __tests__/
│   │                   │       └── es_controller.spec.ts
│   │                   └── validators/
│   │                       ├── es_validators.ts
│   │                       └── __tests__/
│   │                           └── es_validators.spec.ts
│   │
│   └── python/
│       ├── src/
│       │   └── verification/
│       │       ├── models.py
│       │       ├── hupyy_client.py
│       │       └── orchestrator.py
│       │
│       └── tests/
│           ├── __init__.py
│           ├── conftest.py                    # Shared fixtures
│           │
│           ├── unit/                          # Unit tests (70%)
│           │   ├── __init__.py
│           │   └── verification/
│           │       ├── __init__.py
│           │       ├── test_models.py         # ~15 tests
│           │       ├── test_hupyy_client.py   # ~20 tests
│           │       └── test_orchestrator.py   # ~15 tests
│           │
│           ├── integration/                   # Integration tests (20%)
│           │   ├── __init__.py
│           │   ├── test_kafka_flow.py         # ~10 tests
│           │   ├── test_api_integration.py    # ~8 tests
│           │   ├── test_database.py           # ~5 tests
│           │   └── test_hupyy_external.py     # ~7 tests (VCR)
│           │
│           ├── contract/                      # Contract tests (5%)
│           │   ├── __init__.py
│           │   ├── test_nodejs_contract.py    # ~5 tests (provider)
│           │   └── test_hupyy_contract.py     # ~5 tests (consumer)
│           │
│           ├── fixtures/                      # Test data
│           │   ├── __init__.py
│           │   ├── verification_fixtures.py   # pytest fixtures
│           │   ├── factories.py               # factory_boy factories
│           │   ├── cassettes/                 # VCR cassettes
│           │   │   ├── hupyy_sat_response.yaml
│           │   │   ├── hupyy_unsat_response.yaml
│           │   │   └── hupyy_timeout.yaml
│           │   └── mock_data/
│           │       ├── test_queries.json
│           │       ├── expected_results.json
│           │       └── proof_examples.json
│           │
│           └── utils/                         # Test utilities
│               ├── __init__.py
│               ├── assertions.py              # Custom assertions
│               └── helpers.py                 # Test helpers
│
├── frontend/
│   └── src/
│       └── sections/
│           └── qna/
│               └── chatbot/
│                   └── components/
│                       ├── HupyyControls.tsx
│                       └── __tests__/
│                           └── HupyyControls.spec.tsx
│
└── tests/                                     # E2E & cross-cutting tests
    ├── e2e/                                   # E2E tests (5%)
    │   ├── playwright.config.ts
    │   ├── fixtures/
    │   │   ├── auth.fixture.ts
    │   │   └── chat.fixture.ts
    │   │
    │   ├── pages/                             # Page Object Model
    │   │   ├── BasePage.ts
    │   │   ├── ChatPage.ts
    │   │   ├── SettingsPage.ts
    │   │   └── ResultsPage.ts
    │   │
    │   └── verification/
    │       ├── verification-checkbox.spec.ts  # ~8 tests
    │       ├── verification-flow.spec.ts      # ~7 tests
    │       └── verification-errors.spec.ts    # ~5 tests
    │
    ├── contract/                              # Cross-service contracts
    │   └── nodejs-python/
    │       └── verification-api.pact.ts       # ~10 tests (consumer)
    │
    └── shared/                                # Shared test utilities
        ├── test-data.ts
        └── factories.ts
```

### Naming Conventions

#### Python Test Files
- **Pattern:** `test_<module_name>.py`
- **Location:** Mirror source structure under `tests/unit/` or `tests/integration/`
- **Examples:**
  - `test_models.py` for `models.py`
  - `test_hupyy_client.py` for `hupyy_client.py`

#### TypeScript Test Files
- **Pattern:** `<ComponentName>.spec.ts` or `<module-name>.spec.ts`
- **Location:** `__tests__/` directory next to source
- **Examples:**
  - `HupyyControls.spec.tsx` for React components
  - `es_controller.spec.ts` for controllers

#### E2E Test Files
- **Pattern:** `<feature>-<aspect>.spec.ts`
- **Location:** `tests/e2e/<feature>/`
- **Examples:**
  - `verification-checkbox.spec.ts`
  - `verification-flow.spec.ts`

#### Test Function Names
- **Python:** `test_<what>_<condition>_<expected>`
  - `test_verify_chunk_with_valid_data_returns_sat`
  - `test_hupyy_client_timeout_raises_exception`

- **TypeScript:** `should <expected> when <condition>`
  - `should return SAT when formula is satisfiable`
  - `should handle timeout gracefully`

---

## 3. Test Execution Strategy

### Local Development

#### Quick Feedback Loop (Unit Tests Only)
```bash
# Python unit tests only (fast)
cd backend/python
pytest tests/unit/ -v

# TypeScript unit tests only (fast)
cd backend/nodejs
npm run test:unit

# Frontend component tests
cd frontend
npm run test
```

**Expected Time:** <30 seconds total

---

#### Integration Tests (Requires Docker)
```bash
# Start dependencies
docker-compose -f docker-compose.test.yml up -d

# Python integration tests
cd backend/python
pytest tests/integration/ -v

# Shutdown dependencies
docker-compose -f docker-compose.test.yml down
```

**Expected Time:** 2-5 minutes

---

#### E2E Tests (Full Stack)
```bash
# Start full application stack
docker-compose up -d

# Wait for services to be ready
./scripts/wait-for-services.sh

# Run Playwright tests
cd tests/e2e
npx playwright test

# Shutdown stack
docker-compose down
```

**Expected Time:** 3-5 minutes

---

#### All Tests
```bash
# Comprehensive test suite
npm run test:all

# Or with coverage
npm run test:coverage
```

**Expected Time:** 8-10 minutes

---

### CI/CD Execution

#### GitHub Actions Workflow Stages

```yaml
# .github/workflows/test-verification.yml

name: Verification Tests

on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [develop, main]

jobs:
  # Stage 1: Fast unit tests (parallel)
  unit-tests-python:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        split: [1, 2, 3, 4]  # Parallel execution
    steps:
      - pytest tests/unit/ --splits 4 --group ${{ matrix.split }}
    # Time: ~1 minute per split

  unit-tests-typescript:
    runs-on: ubuntu-latest
    steps:
      - npm run test:unit -- --maxWorkers=4
    # Time: ~1 minute

  # Stage 2: Integration tests (sequential due to resource constraints)
  integration-tests:
    needs: [unit-tests-python, unit-tests-typescript]
    runs-on: ubuntu-latest
    services:
      kafka:
        image: confluentinc/cp-kafka:7.9.0
      postgres:
        image: postgres:15
    steps:
      - pytest tests/integration/ -v
    # Time: ~3 minutes

  # Stage 3: Contract tests (fast)
  contract-tests:
    needs: [unit-tests-python, unit-tests-typescript]
    runs-on: ubuntu-latest
    steps:
      - npm run test:contract
      - pytest tests/contract/ -v
    # Time: ~1 minute

  # Stage 4: E2E tests (parallel sharding)
  e2e-tests:
    needs: [integration-tests, contract-tests]
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shardIndex: [1, 2]
        shardTotal: [2]
    steps:
      - npx playwright test --shard=${{ matrix.shardIndex }}/${{ matrix.shardTotal }}
    # Time: ~2 minutes per shard

  # Stage 5: Coverage aggregation
  coverage-report:
    needs: [e2e-tests]
    runs-on: ubuntu-latest
    steps:
      - Upload to codecov
      - Comment on PR with coverage delta
```

**Total CI/CD Time:** ~8-10 minutes

---

### Execution Triggers

| Trigger | Tests Run | Max Time |
|---------|-----------|----------|
| **On Save (Local)** | Affected unit tests only | <10s |
| **Pre-commit Hook** | Linting + affected unit tests | <30s |
| **On Push (Feature Branch)** | All unit tests | <2 min |
| **On PR Creation** | Unit + Integration tests | <7 min |
| **Before Merge** | All tests (unit + integration + contract + E2E) | <10 min |
| **Nightly Build** | All tests + performance tests | <20 min |
| **On Release** | All tests + manual validation | <30 min |

---

## 4. Environment Strategy

### Test Environments

#### Local Development Environment
- **Purpose:** Fast feedback during development
- **Characteristics:**
  - Minimal external dependencies
  - Mocks for external APIs
  - Optional Docker for integration tests
  - Uses test fixtures and factories
- **Configuration:** `.env.test.local`

#### CI/CD Environment
- **Purpose:** Automated testing on every commit/PR
- **Characteristics:**
  - Clean state for every run
  - Ephemeral services (Testcontainers)
  - Parallel execution
  - Artifact collection (reports, screenshots)
- **Configuration:** GitHub Actions secrets + environment variables

#### Staging Environment (Optional)
- **Purpose:** Pre-production validation with real services
- **Characteristics:**
  - Real external APIs (Hupyy staging)
  - Real databases (isolated staging DB)
  - Real message queues
  - Nightly E2E test runs
- **Configuration:** `.env.staging`

---

### Dependency Management

#### Mock vs. Real Dependencies Decision Matrix

| Dependency | Unit Tests | Integration Tests | Contract Tests | E2E Tests |
|------------|-----------|-------------------|----------------|-----------|
| **Hupyy API** | Mock (unittest.mock) | VCR cassettes | Pact contract | Real (staging) OR Mock |
| **Kafka** | MockProducer/Consumer | Testcontainers | N/A | Testcontainers |
| **PostgreSQL** | Mock repository | Testcontainers | N/A | Testcontainers |
| **ArangoDB** | Mock repository | Testcontainers | N/A | Testcontainers |
| **MongoDB** | Mock repository | Testcontainers | N/A | Testcontainers |
| **Qdrant** | Mock client | Testcontainers | N/A | Testcontainers |
| **Redis** | Mock client | Testcontainers | N/A | Testcontainers |
| **NodeJS API** | Mock (msw) | Real (test server) | Pact provider | Real (Docker) |
| **Python API** | Mock (responses) | Real (test server) | Pact provider | Real (Docker) |
| **Frontend** | Mock responses | N/A | N/A | Real (Playwright) |

#### Rationale for Decisions

**Hupyy API:**
- **Unit:** Mock for speed and isolation
- **Integration:** VCR cassettes for realistic responses without network dependency
- **E2E:** Real staging API for production-like testing (with fallback to mocks)

**Kafka:**
- **Unit:** MockProducer/Consumer for testing producer/consumer logic
- **Integration:** Testcontainers for real Kafka behavior
- **E2E:** Testcontainers for full message flow

**Databases:**
- **Unit:** Mock repositories (no actual database)
- **Integration:** Testcontainers for real database operations
- **E2E:** Testcontainers for full stack persistence

**Internal APIs:**
- **Unit:** Mocks (msw for TypeScript, responses for Python)
- **Integration:** Real test servers with test data
- **Contract:** Pact contracts validated against real implementations
- **E2E:** Real services in Docker Compose

---

### Environment Configuration Files

```
pipeshub-ai-orig/
├── .env.example                 # Template for all environments
├── .env.test                    # CI/CD test environment
├── .env.test.local             # Local development testing
├── .env.staging                # Staging environment (optional)
│
├── backend/python/
│   ├── pytest.ini              # pytest configuration
│   └── .env.test               # Python-specific test config
│
├── backend/nodejs/
│   ├── jest.config.js          # Jest configuration
│   └── .env.test               # NodeJS-specific test config
│
├── tests/e2e/
│   ├── playwright.config.ts   # Playwright configuration
│   └── .env.e2e               # E2E-specific config
│
└── docker-compose.test.yml    # Test-specific services
```

---

## 5. Mock vs. Real Dependencies Guidelines

### When to Mock

**Use Mocks When:**
1. **Speed is critical** (unit tests must be fast)
2. **External dependency is unreliable** (network issues, rate limits)
3. **Testing error conditions** (simulate timeouts, failures)
4. **External service is expensive** (paid API calls)
5. **Dependency is not available** (third-party service down)

**Mocking Strategies:**
- `unittest.mock` for Python
- `jest.mock()` for TypeScript/JavaScript
- `msw` (Mock Service Worker) for HTTP mocking
- `responses` / `respx` for Python HTTP mocking

---

### When to Use Real Dependencies

**Use Real Dependencies When:**
1. **Testing integration points** (service boundaries)
2. **Validating actual behavior** (database transactions, Kafka offsets)
3. **Contracts must be verified** (API compatibility)
4. **Mocks would be too complex** (simpler to use real thing)
5. **Realistic performance testing** (latency, throughput)

**Real Dependency Strategies:**
- Testcontainers for databases and Kafka
- VCR.py for external APIs (record once, replay many times)
- Test servers for internal APIs
- Docker Compose for full stack

---

### Hybrid Approach: VCR Pattern

**Best of Both Worlds:**
- Record real HTTP interactions on first run
- Replay recorded responses on subsequent runs
- No network dependency after initial recording
- Realistic responses without mocking complexity

**Use Cases:**
- External API testing (Hupyy API)
- Third-party service integration
- Regression testing (ensure API behavior hasn't changed)

**Implementation:**
```python
import vcr

@vcr.use_cassette('fixtures/cassettes/hupyy_sat_response.yaml')
def test_hupyy_verify_sat():
    # First run: records HTTP interaction
    # Subsequent runs: replays from cassette
    response = hupyy_client.verify_chunk(sat_chunk)
    assert response.check_sat_result == "SAT"
```

---

## 6. Test Data Management

### Test Data Principles

1. **Isolation:** Each test uses independent data (no shared state)
2. **Repeatability:** Same test data produces same results
3. **Realistic:** Data resembles production scenarios
4. **Maintainable:** Easy to update and understand
5. **Minimal:** Only create data necessary for the test

### Data Generation Strategies

#### Factory Pattern (Recommended)
- **Python:** `factory_boy` + `pytest-factoryboy`
- **TypeScript:** `fishery`
- **Benefits:** Flexible, reusable, reduces duplication

#### Fixture Files
- **Format:** JSON, YAML, or Python/TypeScript files
- **Location:** `tests/fixtures/`
- **Use Case:** Complex, static test data (proofs, expected results)

#### Synthetic Data Generation
- **Python:** `Faker`
- **TypeScript:** `@faker-js/faker`
- **Use Case:** Realistic data (names, emails, queries)

#### Database Seeding
- **Strategy:** Testcontainers with seeded data
- **Use Case:** Integration tests requiring pre-populated database

---

### Data Cleanup Strategy

#### Unit Tests
- **Cleanup:** Not needed (no persistent state)
- **Strategy:** Pure functions, mocked dependencies

#### Integration Tests
- **Cleanup:** Automatic (Testcontainers destroyed after test)
- **Strategy:** Ephemeral containers, transaction rollback

#### E2E Tests
- **Cleanup:** Docker Compose down + volume removal
- **Strategy:** Fresh stack for each test run

---

## 7. Parallel Execution Strategy

### Unit Tests Parallelization

#### Python (pytest-xdist)
```bash
# Use all CPU cores
pytest tests/unit/ -n auto

# Use specific number of workers
pytest tests/unit/ -n 4
```

**Expected Speedup:** 3-4x on 4-core machine

---

#### TypeScript (Jest/Vitest)
```bash
# Jest default parallelization
jest --maxWorkers=4

# Vitest default parallelization
vitest --threads
```

**Expected Speedup:** 2-3x on 4-core machine

---

### Integration Tests (Limited Parallelization)

**Challenge:** Shared resources (Kafka, databases) can conflict

**Solution:**
- Run sequentially by default
- Use test isolation (separate Kafka topics, database schemas)
- Limit parallelization to 2-4 workers max

```bash
pytest tests/integration/ -n 2
```

---

### E2E Tests (Playwright Sharding)

**Built-in Sharding:**
```bash
# Split tests across 2 workers
npx playwright test --shard=1/2  # Worker 1
npx playwright test --shard=2/2  # Worker 2
```

**CI/CD Sharding:**
```yaml
strategy:
  matrix:
    shardIndex: [1, 2, 3, 4]
    shardTotal: [4]
steps:
  - npx playwright test --shard=${{ matrix.shardIndex }}/${{ matrix.shardTotal }}
```

**Expected Speedup:** Near-linear (4 shards ≈ 4x faster)

---

### CI/CD Parallelization Limits

**Maximum Parallel Jobs:** Based on CPU cores on machine
- **Current System:** Check `sysctl -n hw.ncpu` or `nproc`
- **Recommended:** Do not exceed available cores
- **GitHub Actions:** ubuntu-latest provides 2-core runners

**Optimal Configuration:**
- **Unit Tests:** 4 parallel workers (pytest-split)
- **Integration Tests:** Sequential or 2 workers
- **E2E Tests:** 2 shards
- **Contract Tests:** Sequential (fast anyway)

---

## 8. Test Categorization

### Test Markers (pytest)

```python
# pytest.ini
[pytest]
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (slower, dependencies)
    contract: Contract tests (API compatibility)
    slow: Slow-running tests (>5s)
    smoke: Smoke tests (critical paths)
    regression: Regression tests (bug fixes)
    kafka: Tests requiring Kafka
    database: Tests requiring database
    external_api: Tests requiring external API
    flaky: Known flaky tests (quarantine)
```

**Usage:**
```bash
# Run only unit tests
pytest -m unit

# Run unit + integration
pytest -m "unit or integration"

# Skip slow tests
pytest -m "not slow"

# Run smoke tests only
pytest -m smoke
```

---

### Test Tagging (Playwright)

```typescript
// verification-checkbox.spec.ts
test.describe('Verification Checkbox', () => {
  test('should display checkbox @smoke @critical', async ({ page }) => {
    // Test implementation
  })

  test('should persist state @regression', async ({ page }) => {
    // Test implementation
  })
})
```

**Usage:**
```bash
# Run smoke tests only
npx playwright test --grep @smoke

# Skip flaky tests
npx playwright test --grep-invert @flaky
```

---

## 9. Test Quality Metrics

### Coverage Targets

| Layer | Line Coverage | Branch Coverage | Function Coverage |
|-------|--------------|-----------------|-------------------|
| **Overall** | ≥80% | ≥75% | ≥85% |
| **Unit Tests** | ≥90% | ≥85% | ≥95% |
| **Integration Tests** | ≥70% | ≥65% | ≥75% |
| **E2E Tests** | N/A (critical paths) | N/A | N/A |

### Execution Time Targets

| Test Suite | Target Time | Max Allowed |
|-----------|-------------|-------------|
| **Unit (Python)** | 30s | 1 min |
| **Unit (TypeScript)** | 30s | 1 min |
| **Integration** | 3 min | 5 min |
| **Contract** | 30s | 1 min |
| **E2E** | 2 min | 3 min |
| **Total Pipeline** | 8 min | 10 min |

### Flaky Test Targets

- **Acceptable Rate:** <5% of tests
- **Detection:** BuildPulse or manual tracking
- **Resolution:** Within 2 weeks of detection
- **Quarantine:** Mark with `@flaky`, don't block CI

---

## 10. Architecture Diagrams

### Test Flow Diagram

```
Developer Workflow:
┌─────────────┐
│ Code Change │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Pre-commit Hook │  ← Linting + affected unit tests (<30s)
└────────┬────────┘
         │
         ▼
    ┌────────┐
    │ Push   │
    └───┬────┘
        │
        ▼
┌───────────────────┐
│ GitHub Actions CI │
└────────┬──────────┘
         │
         ├─── Stage 1: Unit Tests (parallel, ~1 min)
         │    ├─ Python (pytest-split, 4 workers)
         │    └─ TypeScript (Jest, 4 workers)
         │
         ├─── Stage 2: Integration Tests (~3 min)
         │    ├─ Kafka flow tests
         │    ├─ Database tests
         │    └─ External API tests (VCR)
         │
         ├─── Stage 3: Contract Tests (~1 min)
         │    ├─ Consumer contracts (TypeScript)
         │    └─ Provider verification (Python)
         │
         ├─── Stage 4: E2E Tests (parallel, ~2 min)
         │    └─ Playwright (2 shards)
         │
         └─── Stage 5: Coverage Report
              ├─ Aggregate coverage
              ├─ Upload to codecov
              └─ Comment on PR

Total Time: ~8-10 minutes
```

---

### Test Data Flow

```
Test Execution:
┌──────────────┐
│  Test Suite  │
└──────┬───────┘
       │
       ├─── Unit Tests
       │    ├─ Mock Data (in-memory)
       │    ├─ Factories (factory_boy, fishery)
       │    └─ Faker (synthetic data)
       │
       ├─── Integration Tests
       │    ├─ Testcontainers (ephemeral DB/Kafka)
       │    ├─ VCR Cassettes (recorded API responses)
       │    ├─ Factories (realistic objects)
       │    └─ Seeded Data (migrations + seeds)
       │
       ├─── Contract Tests
       │    ├─ Pact Contracts (JSON specifications)
       │    └─ Provider States (test data scenarios)
       │
       └─── E2E Tests
            ├─ Docker Compose (full stack)
            ├─ Seeded Database (realistic data)
            ├─ Fixtures (authentication, chat sessions)
            └─ Page Object Model (reusable interactions)

Cleanup:
├─ Unit: None needed (no persistent state)
├─ Integration: Automatic (containers destroyed)
├─ Contract: None needed (stateless)
└─ E2E: docker-compose down + volume removal
```

---

## 11. Best Practices Summary

### Do's

✅ **Write tests before code** (TDD approach)
✅ **Keep unit tests fast** (<100ms per test)
✅ **Use factories for test data** (DRY principle)
✅ **Isolate tests** (no shared state)
✅ **Use descriptive test names** (clear intent)
✅ **Mock external dependencies in unit tests**
✅ **Use real dependencies in integration tests**
✅ **Run tests in CI/CD on every commit**
✅ **Track and fix flaky tests immediately**
✅ **Maintain high coverage** (≥80%)
✅ **Use Page Object Model for E2E tests**
✅ **Tag tests with markers** (smoke, slow, etc.)

---

### Don'ts

❌ **Don't skip tests** (even if they seem redundant)
❌ **Don't use sleep/wait** (use proper async/await)
❌ **Don't share test data** (each test independent)
❌ **Don't test implementation details** (test behavior)
❌ **Don't ignore flaky tests** (fix or remove)
❌ **Don't write too many E2E tests** (follow pyramid)
❌ **Don't hardcode test data** (use factories/faker)
❌ **Don't mock everything** (balance with real dependencies)
❌ **Don't commit failing tests** (fix or skip explicitly)
❌ **Don't neglect test maintenance** (refactor with code)

---

## 12. Success Criteria

This test architecture is successful when:

- ✅ **Fast Feedback:** Unit tests complete in <2 minutes
- ✅ **Comprehensive Coverage:** ≥80% line coverage across all services
- ✅ **Reliable:** <5% flaky test rate
- ✅ **Maintainable:** Clear structure, DRY test code
- ✅ **Scalable:** Adding new tests is straightforward
- ✅ **CI/CD Integrated:** All tests run on every PR
- ✅ **Documented:** Clear guidelines for adding new tests
- ✅ **Effective:** Catches bugs before production

---

## Conclusion

This test architecture provides a **comprehensive, pragmatic foundation** for ensuring the quality of the Hupyy SMT verification integration. By following the testing pyramid, using appropriate mocking strategies, and optimizing for fast feedback, the architecture enables rapid development without sacrificing quality.

**Key Takeaways:**
1. **70% unit tests** for speed and coverage
2. **20% integration tests** for realistic validation
3. **10% contract + E2E tests** for critical flows
4. **Mock in unit tests, use real dependencies in integration tests**
5. **Parallel execution for speed** (pytest-split, Playwright sharding)
6. **Clear directory structure** (easy to navigate and maintain)
7. **Strong conventions** (naming, markers, organization)

This architecture is ready for implementation and will scale as the project grows.
