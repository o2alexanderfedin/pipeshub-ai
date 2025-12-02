# Tools and Libraries for Hupyy SMT Verification Testing

**Date:** November 30, 2025
**Project:** PipesHub AI - Hupyy SMT Verification Integration
**Purpose:** Comprehensive catalog of recommended testing tools and libraries

---

## Python Testing Tools

### Core Testing Framework

#### pytest (7.4+)
**Purpose:** Primary test framework for Python
**Website:** https://pytest.org
**Installation:** `pip install pytest`

**Key Features:**
- Simple, Pythonic test writing
- Extensive plugin ecosystem
- Powerful fixture system
- Parallel execution support
- Excellent asyncio support

**Recommended Plugins:**
- pytest-asyncio
- pytest-cov
- pytest-xdist
- pytest-recording
- pytest-factoryboy
- pytest-split

---

### External API Testing

#### vcrpy
**Purpose:** Record and replay HTTP interactions (VCR pattern)
**Website:** https://github.com/kevin1024/vcrpy
**Installation:** `pip install vcrpy`

**Features:**
- Records HTTP interactions as YAML cassettes
- Replays recorded responses in tests
- Eliminates flaky tests from network issues
- Supports all major HTTP libraries (requests, urllib3, httpx)

**Example:**
```python
import vcr

@vcr.use_cassette('fixtures/hupyy_api.yaml')
def test_hupyy_verification():
    response = hupyy_client.verify(chunk)
    assert response.status_code == 200
```

---

#### pytest-recording
**Purpose:** Pytest plugin for VCR.py
**Website:** https://pypi.org/project/pytest-recording/
**Installation:** `pip install pytest-recording`

**Features:**
- Seamless pytest integration
- Automatic cassette management
- Recording modes (once, new_episodes, all)
- CLI options for re-recording

**Example:**
```python
@pytest.mark.vcr
def test_external_api():
    response = requests.get('https://api.hupyy.com/verify')
    assert response.ok
```

---

#### pact-python
**Purpose:** Consumer-driven contract testing
**Website:** https://github.com/pact-foundation/pact-python
**Installation:** `pip install pact-python`

**Features:**
- Define consumer expectations
- Provider verification
- Pact Broker integration
- Multi-language support

**Example:**
```python
from pact import Consumer, Provider

pact = Consumer('NodeJS Backend').has_pact_with(
    Provider('Python FastAPI')
)

pact.given('user exists').upon_receiving(
    'verification request'
).with_request(
    method='POST',
    path='/api/verify'
).will_respond_with(200)
```

---

#### responses
**Purpose:** Mock HTTP responses for requests library
**Website:** https://github.com/getsentry/responses
**Installation:** `pip install responses`

**Features:**
- Mock responses for requests library
- Pattern matching for URLs
- Callback support for dynamic responses
- Assertion helpers

**Example:**
```python
import responses

@responses.activate
def test_api():
    responses.add(
        responses.POST,
        'https://api.hupyy.com/verify',
        json={'verdict': 'SAT'},
        status=200
    )
    result = hupyy_client.verify(chunk)
    assert result.verdict == 'SAT'
```

---

#### respx
**Purpose:** Mock HTTP responses for httpx library
**Website:** https://github.com/lundberg/respx
**Installation:** `pip install respx`

**Features:**
- Modern async HTTP mocking
- httpx integration
- Pattern matching
- Request history inspection

**Example:**
```python
import respx
import httpx

@respx.mock
async def test_async_api():
    respx.post('https://api.hupyy.com/verify').mock(
        return_value=httpx.Response(200, json={'verdict': 'SAT'})
    )
    result = await hupyy_client.verify_async(chunk)
    assert result.verdict == 'SAT'
```

---

### Kafka Testing

#### testcontainers-python
**Purpose:** Docker containers for integration testing
**Website:** https://testcontainers-python.readthedocs.io
**Installation:** `pip install testcontainers[kafka]`

**Features:**
- Kafka, PostgreSQL, MongoDB containers
- Automatic port mapping
- Health checks and wait strategies
- Cleanup after tests

**Example:**
```python
from testcontainers.kafka import KafkaContainer

def test_kafka_flow():
    with KafkaContainer() as kafka:
        producer = KafkaProducer(
            bootstrap_servers=kafka.get_bootstrap_server()
        )
        producer.send('test-topic', b'message')
        # Test producer/consumer logic
```

---

#### pytest-kafka
**Purpose:** Pytest fixtures for Kafka testing
**Website:** https://pypi.org/project/pytest-kafka/
**Installation:** `pip install pytest-kafka`

**Features:**
- Zookeeper, Kafka server, consumer fixtures
- Python 3.12+ support (kafka-python-ng)
- Easy pytest integration

**Example:**
```python
def test_kafka_consumer(kafka_consumer):
    # kafka_consumer fixture provided by plugin
    messages = list(kafka_consumer)
    assert len(messages) > 0
```

---

#### confluent-kafka
**Purpose:** High-performance Kafka client with idempotency support
**Website:** https://github.com/confluentinc/confluent-kafka-python
**Installation:** `pip install confluent-kafka`

**Features:**
- C librdkafka bindings (high performance)
- Idempotent producer support
- Exactly-once semantics
- Schema registry integration

**Example:**
```python
from confluent_kafka import Producer

producer = Producer({
    'bootstrap.servers': 'localhost:9092',
    'enable.idempotence': True
})
producer.produce('topic', 'message')
producer.flush()
```

---

### Test Data and Fixtures

#### factory_boy
**Purpose:** Test data factories for Python objects
**Website:** https://factoryboy.readthedocs.io
**Installation:** `pip install factory_boy`

**Features:**
- Flexible factory definitions
- SQLAlchemy, Django ORM support
- Pydantic model support (2025)
- SubFactory for relationships
- Faker integration

**Example:**
```python
import factory
from factory.alchemy import SQLAlchemyModelFactory

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db_session

    email = factory.Faker('email')
    name = factory.Faker('name')

user = UserFactory(email='custom@example.com')
```

---

#### pytest-factoryboy
**Purpose:** Pytest integration for factory_boy
**Website:** https://pytest-factoryboy.readthedocs.io
**Installation:** `pip install pytest-factoryboy`

**Features:**
- Automatic fixture generation from factories
- Lazy evaluation
- Fixture dependencies
- No manual fixture implementation needed

**Example:**
```python
from pytest_factoryboy import register

register(UserFactory)

def test_user_creation(user):
    # user fixture automatically created
    assert user.email.endswith('@example.com')
```

---

#### Faker
**Purpose:** Generate synthetic test data
**Website:** https://faker.readthedocs.io
**Installation:** `pip install Faker`

**Features:**
- Realistic fake data (names, emails, addresses, etc.)
- Localization support
- Reproducible via seeds
- Extensive data providers

**Example:**
```python
from faker import Faker

fake = Faker()
fake.seed_instance(12345)  # Reproducible

email = fake.email()
name = fake.name()
text = fake.text()
```

---

### Code Coverage

#### pytest-cov
**Purpose:** Coverage reporting for pytest
**Website:** https://pytest-cov.readthedocs.io
**Installation:** `pip install pytest-cov`

**Features:**
- Line and branch coverage
- HTML, XML, JSON reports
- Coverage thresholds
- CI/CD integration

**Usage:**
```bash
pytest --cov=src --cov-report=html --cov-report=term
```

---

#### coverage.py
**Purpose:** Core coverage measurement tool
**Website:** https://coverage.readthedocs.io
**Installation:** `pip install coverage` (installed with pytest-cov)

**Features:**
- Detailed coverage analysis
- Branch coverage
- Context tracking
- Multiple report formats

---

### Parallel Execution

#### pytest-xdist
**Purpose:** Parallel and distributed testing
**Website:** https://pytest-xdist.readthedocs.io
**Installation:** `pip install pytest-xdist`

**Features:**
- Multi-process execution
- Load balancing
- Loop-on-failing mode
- Remote execution

**Usage:**
```bash
pytest -n auto  # Use all CPU cores
pytest -n 4     # Use 4 workers
```

---

#### pytest-split
**Purpose:** Intelligent test splitting for CI/CD
**Website:** https://pypi.org/project/pytest-split/
**Installation:** `pip install pytest-split`

**Features:**
- Duration-based test splitting
- GitHub Actions matrix integration
- Optimal load distribution
- Test timing storage

**Usage:**
```bash
pytest --splits 4 --group 1  # Run group 1 of 4 splits
```

---

### Async Testing

#### pytest-asyncio
**Purpose:** Async test support for pytest
**Website:** https://pytest-asyncio.readthedocs.io
**Installation:** `pip install pytest-asyncio`

**Features:**
- Async test functions
- Async fixtures
- Event loop management
- Auto mode for async tests

**Example:**
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result == expected
```

---

### Flaky Test Management

#### pytest-rerunfailures
**Purpose:** Retry flaky tests automatically
**Website:** https://pypi.org/project/pytest-rerunfailures/
**Installation:** `pip install pytest-rerunfailures`

**Features:**
- Automatic test retries
- Configurable retry count and delay
- Per-test or global configuration
- Detailed retry reporting

**Example:**
```python
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_flaky_operation():
    # Test that might fail intermittently
    pass
```

---

### SMT Solver Testing

#### z3-solver
**Purpose:** Z3 SMT solver Python bindings
**Website:** https://github.com/Z3Prover/z3
**Installation:** `pip install z3-solver`

**Features:**
- Full Z3 SMT solver API
- SAT/UNSAT checking
- Model generation
- Proof extraction

**Example:**
```python
from z3 import *

x = Int('x')
y = Int('y')
solver = Solver()
solver.add(x + y == 10)
solver.add(x == 3)

if solver.check() == sat:
    model = solver.model()
    print(f"x={model[x]}, y={model[y]}")
```

---

#### pysmt
**Purpose:** Unified Python API for SMT solvers
**Website:** https://pysmt.readthedocs.io
**Installation:** `pip install pysmt`

**Features:**
- Solver-agnostic API
- Support for Z3, cvc5, MathSAT, etc.
- Formula manipulation
- Solver comparison

**Example:**
```python
from pysmt.shortcuts import *

x, y = Symbol('x'), Symbol('y')
formula = And(Equals(Plus(x, y), Int(10)), Equals(x, Int(3)))

if is_sat(formula):
    model = get_model(formula)
    print(model)
```

---

## TypeScript Testing Tools

### Core Testing Frameworks

#### Jest (29+)
**Purpose:** JavaScript/TypeScript testing framework
**Website:** https://jestjs.io
**Installation:** `npm install --save-dev jest @types/jest ts-jest`

**Features:**
- Zero config for most projects
- Snapshot testing
- Mocking utilities
- Coverage reporting
- Parallel execution

**Example:**
```typescript
describe('VerificationService', () => {
  it('should verify chunk', async () => {
    const result = await service.verify(chunk)
    expect(result.verdict).toBe('SAT')
  })
})
```

---

#### Vitest
**Purpose:** Next-generation testing framework (Vite-based)
**Website:** https://vitest.dev
**Installation:** `npm install --save-dev vitest`

**Features:**
- Extremely fast (native ESM)
- Jest-compatible API
- Hot Module Replacement for tests
- Better TypeScript support
- Modern build tooling

**Example:**
```typescript
import { describe, it, expect } from 'vitest'

describe('VerificationService', () => {
  it('should verify chunk', async () => {
    const result = await service.verify(chunk)
    expect(result.verdict).toBe('SAT')
  })
})
```

**Recommendation:** Prefer Vitest for new projects, Jest for existing ones.

---

### React Testing

#### @testing-library/react
**Purpose:** React component testing utilities
**Website:** https://testing-library.com/react
**Installation:** `npm install --save-dev @testing-library/react`

**Features:**
- User-centric testing approach
- Queries by accessibility roles
- Event simulation
- Async utilities

**Example:**
```typescript
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

test('enables verification checkbox', async () => {
  render(<ChatInterface />)
  const checkbox = screen.getByRole('checkbox', {
    name: /enable verification/i
  })
  await userEvent.click(checkbox)
  expect(checkbox).toBeChecked()
})
```

---

#### @testing-library/jest-dom
**Purpose:** Custom matchers for DOM testing
**Website:** https://testing-library.com/jest-dom
**Installation:** `npm install --save-dev @testing-library/jest-dom`

**Features:**
- Readable assertions
- Accessibility-focused
- Custom matchers (toBeVisible, toHaveTextContent, etc.)

**Example:**
```typescript
expect(element).toBeInTheDocument()
expect(element).toHaveTextContent('Verification Result')
expect(button).toBeDisabled()
```

---

### External API Testing

#### Mock Service Worker (MSW)
**Purpose:** Network-level API mocking
**Website:** https://mswjs.io
**Installation:** `npm install --save-dev msw`

**Features:**
- Intercepts requests at network level
- Works with any HTTP client (fetch, axios, etc.)
- Node.js and browser support
- TypeScript-first

**Example:**
```typescript
import { rest } from 'msw'
import { setupServer } from 'msw/node'

const server = setupServer(
  rest.post('/api/verify', (req, res, ctx) => {
    return res(ctx.json({ verdict: 'SAT' }))
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

---

#### axios-mock-adapter
**Purpose:** Mock axios requests (alternative to MSW)
**Website:** https://github.com/ctimmerm/axios-mock-adapter
**Installation:** `npm install --save-dev axios-mock-adapter`

**Features:**
- Axios-specific mocking
- Request/response matching
- Delay simulation
- Passthrough mode

**Example:**
```typescript
import MockAdapter from 'axios-mock-adapter'
import axios from 'axios'

const mock = new MockAdapter(axios)

mock.onPost('/api/verify').reply(200, {
  verdict: 'SAT',
  confidence: 0.95
})
```

---

#### @pact-foundation/pact
**Purpose:** Consumer-driven contract testing
**Website:** https://docs.pact.io
**Installation:** `npm install --save-dev @pact-foundation/pact`

**Features:**
- Define consumer contracts
- Provider verification
- Pact Broker integration
- Multi-language support

**Example:**
```typescript
import { PactV3 } from '@pact-foundation/pact'

const provider = new PactV3({
  consumer: 'NodeJS Backend',
  provider: 'Python FastAPI'
})

await provider
  .addInteraction({
    states: [{ description: 'user exists' }],
    uponReceiving: 'verification request',
    withRequest: {
      method: 'POST',
      path: '/api/verify',
      body: { query: 'test', verification_enabled: true }
    },
    willRespondWith: {
      status: 200,
      body: { task_id: like('uuid') }
    }
  })
  .executeTest(async (mockServer) => {
    // Test against mock server
  })
```

---

### Test Data Generation

#### fishery
**Purpose:** TypeScript-native factory library
**Website:** https://github.com/thoughtbot/fishery
**Installation:** `npm install --save-dev fishery`

**Features:**
- Type-safe factories
- Factory extension
- Build hooks
- Transient attributes

**Example:**
```typescript
import { Factory } from 'fishery'

interface User {
  id: string
  email: string
  name: string
}

const userFactory = Factory.define<User>(({ sequence }) => ({
  id: `user-${sequence}`,
  email: `user${sequence}@example.com`,
  name: `User ${sequence}`
}))

const user = userFactory.build({ email: 'custom@example.com' })
const users = userFactory.buildList(5)
```

---

#### @faker-js/faker
**Purpose:** Generate synthetic test data
**Website:** https://fakerjs.dev
**Installation:** `npm install --save-dev @faker-js/faker`

**Features:**
- Realistic fake data
- Localization support
- Reproducible via seeds
- Extensive data types

**Example:**
```typescript
import { faker } from '@faker-js/faker'

faker.seed(12345)  // Reproducible

const user = {
  email: faker.internet.email(),
  name: faker.person.fullName(),
  bio: faker.lorem.paragraph()
}
```

---

### Playwright (E2E Testing)

#### @playwright/test
**Purpose:** End-to-end testing framework
**Website:** https://playwright.dev
**Installation:** `npm install --save-dev @playwright/test`

**Features:**
- Multi-browser support (Chromium, Firefox, WebKit)
- Auto-waiting for elements
- Network interception
- Screenshot/video recording
- Parallel execution
- TypeScript support

**Example:**
```typescript
import { test, expect } from '@playwright/test'

test('verification flow', async ({ page }) => {
  await page.goto('/chat')
  await page.getByRole('checkbox', {
    name: 'Enable Verification'
  }).check()
  await page.getByPlaceholder('Enter query').fill('test query')
  await page.getByRole('button', { name: 'Submit' }).click()
  await expect(page.getByTestId('verification-result')).toBeVisible()
})
```

---

#### pytest-playwright (Python)
**Purpose:** Playwright for Python/pytest
**Website:** https://playwright.dev/python
**Installation:** `pip install pytest-playwright`

**Features:**
- Same Playwright capabilities in Python
- pytest fixture integration
- Sync and async APIs

**Example:**
```python
def test_verification_flow(page):
    page.goto('/chat')
    page.get_by_role('checkbox', name='Enable Verification').check()
    page.get_by_placeholder('Enter query').fill('test query')
    page.get_by_role('button', name='Submit').click()
    expect(page.get_by_test_id('verification-result')).to_be_visible()
```

---

### Visual Testing

#### @axe-core/playwright
**Purpose:** Accessibility testing with Playwright
**Website:** https://github.com/dequelabs/axe-core-npm
**Installation:** `npm install --save-dev @axe-core/playwright`

**Features:**
- Automated accessibility checks
- WCAG compliance validation
- Detailed violation reports
- Playwright integration

**Example:**
```typescript
import { test } from '@playwright/test'
import { injectAxe, checkA11y } from 'axe-playwright'

test('accessibility check', async ({ page }) => {
  await page.goto('/chat')
  await injectAxe(page)
  await checkA11y(page)
})
```

---

#### pixelmatch
**Purpose:** Pixel-level image comparison
**Website:** https://github.com/mapbox/pixelmatch
**Installation:** `npm install --save-dev pixelmatch`

**Features:**
- Fast pixel diff algorithm
- Anti-aliasing detection
- Configurable threshold
- Works with Playwright screenshots

**Example:**
```typescript
import pixelmatch from 'pixelmatch'
import { PNG } from 'pngjs'

const diff = pixelmatch(
  img1.data,
  img2.data,
  diff.data,
  width,
  height,
  { threshold: 0.1 }
)

expect(diff).toBeLessThan(100)  // Max 100 pixel differences
```

---

## CI/CD and Integration Tools

### GitHub Actions

#### codecov/codecov-action
**Purpose:** Coverage reporting in GitHub Actions
**Website:** https://github.com/codecov/codecov-action
**Installation:** GitHub Actions workflow

**Features:**
- Coverage upload to Codecov
- PR comments with coverage deltas
- Coverage badges
- Threshold enforcement

**Example:**
```yaml
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
    files: ./coverage.xml
    fail_ci_if_error: true
```

---

#### actions/upload-artifact
**Purpose:** Store build artifacts in GitHub Actions
**Website:** https://github.com/actions/upload-artifact
**Installation:** Built-in GitHub Actions

**Features:**
- Upload test reports, logs, screenshots
- Retain artifacts for debugging
- Download in subsequent jobs

**Example:**
```yaml
- name: Upload test results
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: test-results
    path: test-results/
```

---

### Flaky Test Detection

#### BuildPulse
**Purpose:** Automated flaky test detection and management
**Website:** https://buildpulse.io
**Pricing:** Paid service with free tier

**Features:**
- Identifies flaky tests automatically
- Quarantine flaky tests
- Root cause analysis
- Trends and analytics
- GitHub Actions integration

**Example:**
```yaml
- name: Report test results to BuildPulse
  uses: buildpulse/buildpulse-action@v0.11.0
  with:
    account: ${{ secrets.BUILDPULSE_ACCOUNT_ID }}
    repository: ${{ secrets.BUILDPULSE_REPOSITORY_ID }}
    path: test-results/*.xml
```

---

#### ctrf-io/github-test-reporter
**Purpose:** Test reporting in GitHub Actions
**Website:** https://github.com/ctrf-io/github-test-reporter
**Installation:** GitHub Actions workflow

**Features:**
- Publish test results in PRs
- Failed test analysis
- Flaky test detection
- Duration trends
- AI summary (optional)

**Example:**
```yaml
- name: Publish test results
  uses: ctrf-io/github-test-reporter@v1
  with:
    results-file: test-results.json
```

---

## Docker and Containerization

### Testcontainers

**Available Modules:**
- testcontainers-python (Kafka, PostgreSQL, MongoDB, Redis, etc.)
- testcontainers-node (TypeScript/JavaScript)
- testcontainers-java
- testcontainers-go
- testcontainers-dotnet

**Common Containers:**
- Kafka (ConfluentInc images)
- PostgreSQL
- MongoDB
- Redis
- Elasticsearch
- Qdrant (vector database)

---

### Docker Compose

#### pytest-docker
**Purpose:** Docker Compose integration for pytest
**Website:** https://github.com/avast/pytest-docker
**Installation:** `pip install pytest-docker`

**Features:**
- Manage docker-compose services in tests
- Fixtures for service access
- Automatic cleanup

---

## Contract Testing

### Pact Broker

**Purpose:** Central repository for consumer-provider contracts
**Website:** https://docs.pact.io/pact_broker
**Deployment:** Self-hosted or PactFlow (SaaS)

**Features:**
- Store and version contracts
- Provider verification results
- Can I deploy? checks
- Webhooks for CI/CD integration

**Docker:**
```bash
docker run -d -p 9292:9292 pactfoundation/pact-broker
```

---

## Code Quality and Linting

### Python

#### mypy
**Purpose:** Static type checking
**Installation:** `pip install mypy`

**Features:**
- Type hint validation
- Gradual typing support
- Plugin ecosystem

---

#### ruff
**Purpose:** Fast Python linter (replaces flake8, isort, etc.)
**Installation:** `pip install ruff`

**Features:**
- 10-100x faster than alternatives
- Replaces multiple tools
- Auto-fix support

---

### TypeScript

#### ESLint
**Purpose:** JavaScript/TypeScript linting
**Installation:** `npm install --save-dev eslint @typescript-eslint/eslint-plugin`

**Recommended Rules:**
- @typescript-eslint/no-floating-promises (Playwright tests)
- @typescript-eslint/strict-type-assertions
- no-unused-vars

---

#### TypeScript Compiler
**Purpose:** Type checking in CI/CD
**Usage:** `tsc --noEmit`

**Benefits:**
- Catch type errors before runtime
- Validate function signatures
- Ensure type safety

---

## Summary and Recommendations

### Must-Have Tools (Priority 1)

**Python:**
- pytest (core framework)
- pytest-cov (coverage)
- pytest-asyncio (async support)
- factory_boy (test data)
- Faker (synthetic data)

**TypeScript:**
- Jest or Vitest (testing framework)
- @testing-library/react (component testing)
- @playwright/test (E2E testing)
- fishery (test data)
- @faker-js/faker (synthetic data)

**CI/CD:**
- codecov/codecov-action (coverage reporting)
- pytest-split (parallel Python tests)

---

### Should-Have Tools (Priority 2)

**Python:**
- pytest-recording (VCR pattern)
- testcontainers-python (integration tests)
- pact-python (contract testing)
- pytest-xdist (parallel execution)

**TypeScript:**
- msw (API mocking)
- @pact-foundation/pact (contract testing)

**CI/CD:**
- BuildPulse or ctrf-io (flaky test detection)
- actions/upload-artifact (test artifacts)

---

### Nice-to-Have Tools (Priority 3)

**Python:**
- pytest-split (CI/CD optimization)
- pytest-rerunfailures (flaky test retries)
- z3-solver or pysmt (SMT validation)

**TypeScript:**
- @axe-core/playwright (accessibility)
- pixelmatch (visual regression)

**Infrastructure:**
- Pact Broker (contract repository)
- Docker Compose (local development)

---

## Installation Commands

### Python Full Stack
```bash
# Core testing
pip install pytest pytest-asyncio pytest-cov

# External API testing
pip install pytest-recording pact-python responses respx

# Kafka testing
pip install testcontainers[kafka] pytest-kafka confluent-kafka

# Test data
pip install factory_boy pytest-factoryboy Faker

# Parallel execution
pip install pytest-xdist pytest-split

# Flaky tests
pip install pytest-rerunfailures

# SMT solvers
pip install z3-solver pysmt
```

---

### TypeScript Full Stack
```bash
# Core testing
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom

# API testing
npm install --save-dev msw @pact-foundation/pact

# E2E testing
npm install --save-dev @playwright/test

# Test data
npm install --save-dev fishery @faker-js/faker

# Visual/Accessibility
npm install --save-dev @axe-core/playwright pixelmatch

# Linting
npm install --save-dev eslint @typescript-eslint/eslint-plugin
```

---

## Version Compatibility Notes

**Python:**
- Python 3.10+ recommended
- pytest 7.4+ for latest features
- pytest-kafka requires kafka-python-ng for Python 3.12+

**TypeScript:**
- Node.js 18+ recommended
- TypeScript 5.0+ for latest features
- Playwright requires Node.js 16+

**Docker:**
- Docker 20.10+ for Testcontainers
- docker-compose 2.0+ recommended

---

This comprehensive tooling guide provides everything needed to implement the testing strategy outlined in RECOMMENDATIONS.md. All tools are production-ready, actively maintained, and widely adopted in the industry as of 2025.
