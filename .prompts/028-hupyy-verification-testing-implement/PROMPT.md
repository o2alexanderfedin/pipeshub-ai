<objective>
Implement comprehensive automated test suite for Hupyy SMT verification integration including unit tests, integration tests, and Playwright E2E tests. Execute test-driven development following the specifications and architecture defined in prompts 026 (research) and 027 (plan).
</objective>

<context>
**Foundation:**
- Read `.prompts/026-hupyy-verification-testing-research/` for testing best practices and recommended tools
- Read `.prompts/027-hupyy-verification-testing-plan/` for detailed test specifications and architecture
- Follow implementation checklist and test scenarios from planning phase

**Current Test Coverage:**
- Python unit tests: 18 tests in `backend/python/tests/verification/test_hupyy_api_integration.py` (100% passing)
- No integration tests
- No E2E tests
- No CI/CD workflows

**Target Test Coverage:**
- Unit tests: 50-80 tests (≥80% code coverage)
- Integration tests: 15-25 tests (≥60% coverage)
- E2E tests: 15-20 tests (critical paths)
- CI/CD: Automated workflows for all test types

**Technology Stack:**
- Python: pytest, pytest-asyncio, pytest-mock, httpx, respx
- TypeScript: Jest/Vitest, @testing-library/react, MSW
- Playwright: @playwright/test with TypeScript
- CI/CD: GitHub Actions

**System Under Test:**
- Backend Python: `backend/python/app/verification/`
- Backend NodeJS: `backend/nodejs/apps/src/modules/enterprise_search/`
- Frontend: `frontend/src/sections/qna/chatbot/`
- Integration: Full verification flow across all services

Read @CLAUDE.md for project conventions (TDD, SOLID, type safety).
</context>

<requirements>

## Implementation Phases

### Phase 1: Test Infrastructure Setup

**1.1 Directory Structure**

Create test organization following plan:

```
backend/python/
  tests/
    fixtures/
      verification_fixtures.py      # Shared fixtures
      mock_hupyy_responses.json     # Mock API responses
      test_queries.json              # Test data
    factories/
      verification_factory.py        # Test data factories
    verification/
      test_models.py                 # Model validation tests
      test_hupyy_client.py          # API client tests
      test_orchestrator.py          # Orchestrator tests
    integration/
      test_verification_flow.py     # End-to-end pipeline tests
      test_api_contracts.py         # Contract tests

backend/nodejs/
  apps/src/modules/enterprise_search/
    validators/
      es_validators.spec.ts         # Validation tests
    controller/
      es_controller.spec.ts         # Controller tests

frontend/
  src/sections/qna/chatbot/
    components/
      HupyyControls.spec.tsx        # Component tests

tests/
  e2e/
    fixtures/
      auth.fixture.ts               # Authentication helper
    verification/
      verification-ui.spec.ts       # UI interaction tests
      verification-integration.spec.ts  # Full workflow tests
    support/
      page-objects/
        chat-page.ts                # Page Object Models
```

**1.2 Configuration Files**

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    --asyncio-mode=auto
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (require services)
    slow: Slow tests (run in CI only)
```

**playwright.config.ts:**
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'cd deployment/docker-compose && docker-compose up',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

**1.3 Install Dependencies**

**Python:**
```bash
cd backend/python
pip install pytest pytest-asyncio pytest-mock pytest-cov httpx respx faker factory-boy
```

**TypeScript:**
```bash
cd backend/nodejs
npm install --save-dev jest @types/jest ts-jest @testing-library/react @testing-library/jest-dom msw
```

**Playwright:**
```bash
cd tests
npm install --save-dev @playwright/test
npx playwright install chromium
```

### Phase 2: Unit Tests Implementation

**2.1 Python Model Tests**

**File: `backend/python/tests/verification/test_models.py`**

Implement tests following TDD:

1. Write failing test for `HupyyRequest` validation
2. Run test (should fail)
3. Verify existing code passes (already implemented)
4. Write tests for edge cases
5. Ensure 100% coverage of models.py

**Tests to implement:**
```python
class TestHupyyRequest:
    def test_valid_request_creation(self):
        """Test creating valid HupyyRequest"""
        request = HupyyRequest(
            informal_text="Test query",
            skip_formalization=False,
            enrich=False
        )
        assert request.informal_text == "Test query"
        assert request.skip_formalization is False
        assert request.enrich is False

    def test_informal_text_required(self):
        """Test that informal_text is required"""
        with pytest.raises(ValidationError):
            HupyyRequest(skip_formalization=False)

    def test_default_values(self):
        """Test default values for optional fields"""
        request = HupyyRequest(informal_text="Test")
        assert request.skip_formalization is False
        assert request.enrich is False

    # ... 10 more tests covering all edge cases

class TestHupyyResponse:
    def test_from_hupyy_process_response_sat(self):
        """Test parsing SAT response"""
        response_data = {
            "check_sat_result": "SAT",
            "formalization_similarity": 0.95,
            "proof": {"summary": "Valid proof"},
            "model": "gpt-4",
            "smt_lib_code": "(assert (> x 0))",
            "formal_text": "x > 0"
        }
        response = HupyyResponse.from_hupyy_process_response(response_data)
        assert response.verdict == VerificationVerdict.SAT
        assert response.confidence == 0.95
        assert response.explanation == "Valid proof"

    def test_from_hupyy_process_response_unsat(self):
        """Test parsing UNSAT response"""
        # Similar test for UNSAT

    def test_from_hupyy_process_response_unknown(self):
        """Test parsing UNKNOWN response"""
        # Similar test for UNKNOWN

    def test_from_hupyy_process_response_missing_fields(self):
        """Test handling missing optional fields"""
        response_data = {
            "check_sat_result": "SAT",
            "formalization_similarity": 0.85
        }
        response = HupyyResponse.from_hupyy_process_response(response_data)
        assert response.verdict == VerificationVerdict.SAT
        assert response.metadata == {}

    # ... 10 more tests covering all edge cases
```

**Expected:** 25-30 tests in test_models.py

**2.2 Python Client Tests**

**File: `backend/python/tests/verification/test_hupyy_client.py`**

**Tests to implement:**
```python
class TestHupyyClient:
    @pytest.fixture
    def hupyy_client(self):
        return HupyyClient(
            api_url="https://test-hupyy.example.com",
            timeout_seconds=30
        )

    @pytest.fixture
    def mock_hupyy_response(self):
        return {
            "check_sat_result": "SAT",
            "formalization_similarity": 0.92,
            "proof": {"summary": "Test proof"},
            "model": "claude-3",
            "smt_lib_code": "(assert true)",
            "formal_text": "True statement"
        }

    @pytest.mark.asyncio
    async def test_verify_chunk_success(self, hupyy_client, mock_hupyy_response, respx_mock):
        """Test successful verification request"""
        # Mock the API endpoint
        respx_mock.post(
            "https://test-hupyy.example.com/pipeline/process"
        ).mock(return_value=httpx.Response(200, json=mock_hupyy_response))

        chunk = VerificationChunk(
            chunk_id="test-123",
            content="Test query",
            conversation_id="conv-456"
        )

        result = await hupyy_client.verify_chunk(chunk)

        assert result.verdict == VerificationVerdict.SAT
        assert result.confidence == 0.92

    @pytest.mark.asyncio
    async def test_verify_chunk_timeout(self, hupyy_client, respx_mock):
        """Test timeout handling"""
        respx_mock.post(
            "https://test-hupyy.example.com/pipeline/process"
        ).mock(side_effect=httpx.TimeoutException("Timeout"))

        chunk = VerificationChunk(
            chunk_id="test-123",
            content="Test query",
            conversation_id="conv-456"
        )

        with pytest.raises(VerificationError):
            await hupyy_client.verify_chunk(chunk)

    @pytest.mark.asyncio
    async def test_verify_chunk_http_error_404(self, hupyy_client, respx_mock):
        """Test 404 error handling"""
        respx_mock.post(
            "https://test-hupyy.example.com/pipeline/process"
        ).mock(return_value=httpx.Response(404, json={"error": "Not found"}))

        chunk = VerificationChunk(
            chunk_id="test-123",
            content="Test query",
            conversation_id="conv-456"
        )

        with pytest.raises(VerificationError):
            await hupyy_client.verify_chunk(chunk)

    # ... 15 more tests covering all scenarios
```

**Expected:** 20-25 tests in test_hupyy_client.py

**2.3 TypeScript Controller Tests**

**File: `backend/nodejs/apps/src/modules/enterprise_search/controller/es_controller.spec.ts`**

**Tests to implement:**
```typescript
describe('ES Controller - Verification', () => {
  let controller: ESController;
  let mockPythonBackend: MockAdapter;

  beforeEach(() => {
    controller = new ESController();
    mockPythonBackend = new MockAdapter(axios);
  });

  afterEach(() => {
    mockPythonBackend.restore();
  });

  it('should forward verification_enabled to Python backend', async () => {
    const request = {
      body: {
        query: 'test query',
        verification_enabled: true,
        model_key: 'claude-3',
        chat_mode: 'contextual'
      }
    };

    mockPythonBackend
      .onPost('http://localhost:8000/query')
      .reply(200, { response: 'test response' });

    await controller.handleQuery(request, response);

    const sentData = JSON.parse(mockPythonBackend.history.post[0].data);
    expect(sentData.verification_enabled).toBe(true);
  });

  it('should default verification_enabled to false if not provided', async () => {
    const request = {
      body: {
        query: 'test query',
        model_key: 'claude-3',
        chat_mode: 'contextual'
      }
    };

    mockPythonBackend
      .onPost('http://localhost:8000/query')
      .reply(200, { response: 'test response' });

    await controller.handleQuery(request, response);

    const sentData = JSON.parse(mockPythonBackend.history.post[0].data);
    expect(sentData.verification_enabled).toBe(false);
  });

  // ... 8 more tests
});
```

**Expected:** 10-15 tests in es_controller.spec.ts

**2.4 Frontend Component Tests**

**File: `frontend/src/sections/qna/chatbot/components/HupyyControls.spec.tsx`**

**Tests to implement:**
```typescript
describe('HupyyControls', () => {
  it('should render checkbox with label', () => {
    render(
      <HupyyControls
        enabled={false}
        onToggle={jest.fn()}
        disabled={false}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeInTheDocument();
    expect(checkbox).not.toBeChecked();
  });

  it('should show tooltip on hover', async () => {
    render(
      <HupyyControls
        enabled={false}
        onToggle={jest.fn()}
        disabled={false}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    userEvent.hover(checkbox);

    await waitFor(() => {
      expect(screen.getByText(/SMT verification uses formal logic/i)).toBeInTheDocument();
    });
  });

  it('should call onToggle when clicked', () => {
    const onToggleMock = jest.fn();
    render(
      <HupyyControls
        enabled={false}
        onToggle={onToggleMock}
        disabled={false}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    userEvent.click(checkbox);

    expect(onToggleMock).toHaveBeenCalledTimes(1);
  });

  it('should be disabled when disabled prop is true', () => {
    render(
      <HupyyControls
        enabled={false}
        onToggle={jest.fn()}
        disabled={true}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeDisabled();
  });

  // ... 6 more tests
});
```

**Expected:** 10 tests in HupyyControls.spec.tsx

### Phase 3: Integration Tests Implementation

**3.1 Verification Flow Integration Tests**

**File: `backend/python/tests/integration/test_verification_flow.py`**

**Setup:**
- Use pytest fixtures to manage test environment
- Mock external dependencies (Hupyy API)
- Use embedded Kafka or mock Kafka consumer

**Tests to implement:**
```python
@pytest.mark.integration
class TestVerificationFlowIntegration:
    @pytest.fixture(autouse=True)
    async def setup_test_env(self):
        """Setup test environment before each test"""
        # Start mock Hupyy API server
        # Setup test Kafka topics
        # Initialize test databases
        yield
        # Cleanup after test

    @pytest.mark.asyncio
    async def test_end_to_end_verification_pipeline(self, test_client):
        """Test complete verification flow from API to storage"""
        # 1. Send request to Python API
        response = await test_client.post(
            "/query",
            json={
                "query": "Test mathematical statement",
                "verification_enabled": True,
                "model_key": "claude-3"
            }
        )

        assert response.status_code == 200

        # 2. Verify Kafka message published
        # (check mock Kafka consumer received message)

        # 3. Verify orchestrator called Hupyy API
        # (check mock Hupyy API received request)

        # 4. Verify result stored in database
        # (query database for verification result)

    @pytest.mark.asyncio
    async def test_kafka_message_publishing_format(self):
        """Test that Kafka messages have correct format"""
        # Trigger verification
        # Consume message from Kafka
        # Validate message schema

    @pytest.mark.asyncio
    async def test_concurrent_verification_requests(self):
        """Test handling multiple concurrent verifications"""
        # Send 10 concurrent verification requests
        # Verify all processed correctly
        # Verify no race conditions

    # ... 12 more integration tests
```

**Expected:** 15-20 tests in test_verification_flow.py

**3.2 API Contract Tests**

**File: `backend/python/tests/integration/test_api_contracts.py`**

**Tests to implement:**
```python
@pytest.mark.integration
class TestHupyyAPIContract:
    @pytest.mark.asyncio
    async def test_request_matches_hupyy_spec(self):
        """Verify request format matches Hupyy OpenAPI spec"""
        # Load OpenAPI spec
        spec = load_openapi_spec("https://verticalslice-smt-service-gvav8.ondigitalocean.app/openapi.json")

        # Generate test request
        request = HupyyRequest(
            informal_text="Test",
            skip_formalization=False,
            enrich=False
        )

        # Validate against spec
        validate_request_against_spec(request, spec, "/pipeline/process")

    @pytest.mark.asyncio
    async def test_response_validates_against_hupyy_spec(self):
        """Verify response parsing handles all Hupyy response formats"""
        # Similar validation for responses

    # ... 3 more contract tests
```

**Expected:** 5 tests in test_api_contracts.py

### Phase 4: Playwright E2E Tests Implementation

**4.1 Page Object Models**

**File: `tests/e2e/support/page-objects/chat-page.ts`**

```typescript
export class ChatPage {
  constructor(private page: Page) {}

  async navigate() {
    await this.page.goto('/');
  }

  async login(email: string, password: string) {
    await this.page.fill('[name="email"]', email);
    await this.page.fill('[name="password"]', password);
    await this.page.click('button[type="submit"]');
    await this.page.waitForURL('**/chat');
  }

  async clickConversation(index: number = 0) {
    await this.page.click(`[data-testid="conversation-${index}"]`);
    await this.page.waitForSelector('[data-testid="verification-checkbox"]');
  }

  async toggleVerificationCheckbox() {
    const checkbox = this.page.locator('[data-testid="verification-checkbox"]');
    await checkbox.click();
  }

  async isVerificationCheckboxChecked(): Promise<boolean> {
    const checkbox = this.page.locator('[data-testid="verification-checkbox"]');
    return await checkbox.isChecked();
  }

  async isVerificationCheckboxVisible(): Promise<boolean> {
    const checkbox = this.page.locator('[data-testid="verification-checkbox"]');
    return await checkbox.isVisible();
  }

  async sendMessage(message: string) {
    await this.page.fill('[data-testid="chat-input"]', message);
    await this.page.click('[data-testid="send-button"]');
  }

  async waitForResponse() {
    await this.page.waitForSelector('[data-testid="chat-response"]:last-child');
  }

  async getLastResponseText(): Promise<string> {
    return await this.page.locator('[data-testid="chat-response"]:last-child').textContent();
  }
}
```

**4.2 Verification UI Tests**

**File: `tests/e2e/verification/verification-ui.spec.ts`**

```typescript
import { test, expect } from '@playwright/test';
import { ChatPage } from '../support/page-objects/chat-page';

test.describe('Verification Checkbox', () => {
  let chatPage: ChatPage;

  test.beforeEach(async ({ page }) => {
    chatPage = new ChatPage(page);
    await chatPage.navigate();
    await chatPage.login('af@o2.services', 'Vilisaped1!');
  });

  test('should display verification checkbox in active conversation', async ({ page }) => {
    await chatPage.clickConversation();

    const isVisible = await chatPage.isVerificationCheckboxVisible();
    expect(isVisible).toBe(true);

    await page.screenshot({ path: 'test-results/verification-checkbox-visible.png' });
  });

  test('should toggle verification checkbox', async ({ page }) => {
    await chatPage.clickConversation();

    // Initially unchecked
    let isChecked = await chatPage.isVerificationCheckboxChecked();
    expect(isChecked).toBe(false);

    // Click to check
    await chatPage.toggleVerificationCheckbox();
    isChecked = await chatPage.isVerificationCheckboxChecked();
    expect(isChecked).toBe(true);

    await page.screenshot({ path: 'test-results/verification-checkbox-checked.png' });

    // Click to uncheck
    await chatPage.toggleVerificationCheckbox();
    isChecked = await chatPage.isVerificationCheckboxChecked();
    expect(isChecked).toBe(false);
  });

  test('should show tooltip on checkbox hover', async ({ page }) => {
    await chatPage.clickConversation();

    await page.hover('[data-testid="verification-checkbox"]');

    const tooltip = await page.locator('[role="tooltip"]').textContent();
    expect(tooltip).toContain('SMT verification uses formal logic');
  });

  // ... 7 more UI tests
});

test.describe('Chat with Verification', () => {
  let chatPage: ChatPage;

  test.beforeEach(async ({ page }) => {
    chatPage = new ChatPage(page);
    await chatPage.navigate();
    await chatPage.login('af@o2.services', 'Vilisaped1!');
    await chatPage.clickConversation();
  });

  test('should send query with verification enabled', async ({ page }) => {
    // Intercept API request
    await page.route('**/api/query', async (route) => {
      const request = route.request();
      const postData = request.postDataJSON();

      expect(postData.verification_enabled).toBe(true);

      await route.fulfill({
        status: 200,
        body: JSON.stringify({ response: 'Test response' })
      });
    });

    await chatPage.toggleVerificationCheckbox();
    await chatPage.sendMessage('What is the LLM optimization module?');
    await chatPage.waitForResponse();

    await page.screenshot({ path: 'test-results/chat-with-verification.png' });
  });

  test('should send query without verification when unchecked', async ({ page }) => {
    // Intercept API request
    await page.route('**/api/query', async (route) => {
      const request = route.request();
      const postData = request.postDataJSON();

      expect(postData.verification_enabled).toBe(false);

      await route.fulfill({
        status: 200,
        body: JSON.stringify({ response: 'Test response' })
      });
    });

    await chatPage.sendMessage('What is the LLM optimization module?');
    await chatPage.waitForResponse();

    await page.screenshot({ path: 'test-results/chat-without-verification.png' });
  });

  // ... 6 more chat tests
});
```

**Expected:** 15-20 tests in verification-ui.spec.ts

**4.3 Full Workflow Integration Tests**

**File: `tests/e2e/verification/verification-integration.spec.ts`**

```typescript
test.describe('Full Verification Workflow', () => {
  test('should complete end-to-end verification', async ({ page }) => {
    // This test requires full stack running
    const chatPage = new ChatPage(page);

    await chatPage.navigate();
    await chatPage.login('af@o2.services', 'Vilisaped1!');
    await chatPage.clickConversation();
    await chatPage.toggleVerificationCheckbox();
    await chatPage.sendMessage('All prime numbers greater than 2 are odd');

    await chatPage.waitForResponse();

    // Verify response contains verification badge or indicator
    const response = await chatPage.getLastResponseText();
    expect(response).toBeTruthy();

    await page.screenshot({ path: 'test-results/e2e-verification-complete.png' });
  });

  // ... 4 more E2E workflow tests
});
```

**Expected:** 5 tests in verification-integration.spec.ts

### Phase 5: CI/CD Implementation

**5.1 GitHub Actions Workflow**

**File: `.github/workflows/verification-tests.yml`**

```yaml
name: Verification Tests

on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [develop, main]

jobs:
  python-unit-tests:
    name: Python Unit Tests
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend/python
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-mock pytest-cov httpx respx

      - name: Run unit tests
        run: |
          cd backend/python
          pytest tests/verification/test_models.py tests/verification/test_hupyy_client.py \
            -v --cov=app/verification --cov-report=xml --cov-report=term-missing \
            --junit-xml=test-results/pytest.xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./backend/python/coverage.xml
          flags: python-unit
          name: python-unit-coverage

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: python-unit-test-results
          path: backend/python/test-results/

  typescript-unit-tests:
    name: TypeScript Unit Tests
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js 18
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: |
            backend/nodejs/package-lock.json
            frontend/package-lock.json

      - name: Install dependencies
        run: |
          cd backend/nodejs && npm ci
          cd ../../frontend && npm ci

      - name: Run backend unit tests
        run: |
          cd backend/nodejs
          npm run test -- --coverage --coverageReporters=xml --coverageReporters=text

      - name: Run frontend unit tests
        run: |
          cd frontend
          npm run test -- --coverage --coverageReporters=xml --coverageReporters=text

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./backend/nodejs/coverage/coverage.xml,./frontend/coverage/coverage.xml
          flags: typescript-unit
          name: typescript-unit-coverage

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest

    services:
      kafka:
        image: confluentinc/cp-kafka:7.9.0
        env:
          KAFKA_BROKER_ID: 1
          KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
          KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
          KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
        ports:
          - 9092:9092

      zookeeper:
        image: confluentinc/cp-zookeeper:7.9.0
        env:
          ZOOKEEPER_CLIENT_PORT: 2181
        ports:
          - 2181:2181

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend/python
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-mock httpx respx

      - name: Run integration tests
        run: |
          cd backend/python
          pytest tests/integration/ -v -m integration \
            --junit-xml=test-results/integration.xml
        env:
          KAFKA_BROKERS: localhost:9092
          HUPYY_API_URL: http://mock-hupyy:8080

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: integration-test-results
          path: backend/python/test-results/

  e2e-tests:
    name: E2E Tests (Playwright)
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js 18
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd tests
          npm ci

      - name: Install Playwright browsers
        run: |
          cd tests
          npx playwright install --with-deps chromium

      - name: Start application
        run: |
          cd deployment/docker-compose
          docker-compose -f docker-compose.dev.yml up -d
          sleep 30  # Wait for services to start

      - name: Wait for application to be ready
        run: |
          timeout 120 bash -c 'until curl -f http://localhost:3000; do sleep 2; done'

      - name: Run Playwright tests
        run: |
          cd tests
          npx playwright test --project=chromium

      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: tests/playwright-report/

      - name: Upload screenshots and videos
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-artifacts
          path: |
            tests/test-results/
            tests/screenshots/
            tests/videos/

      - name: Stop application
        if: always()
        run: |
          cd deployment/docker-compose
          docker-compose -f docker-compose.dev.yml down

  quality-gates:
    name: Quality Gates
    needs: [python-unit-tests, typescript-unit-tests, integration-tests, e2e-tests]
    runs-on: ubuntu-latest

    steps:
      - name: All tests passed
        run: echo "All tests passed successfully!"
```

**5.2 Test Scripts in package.json**

**File: `package.json` (root)**

```json
{
  "scripts": {
    "test:unit": "npm run test:unit:python && npm run test:unit:typescript",
    "test:unit:python": "cd backend/python && pytest tests/verification/ -m unit",
    "test:unit:typescript": "npm run test:unit:backend && npm run test:unit:frontend",
    "test:unit:backend": "cd backend/nodejs && npm test",
    "test:unit:frontend": "cd frontend && npm test",
    "test:integration": "cd backend/python && pytest tests/integration/ -m integration",
    "test:e2e": "cd tests && npx playwright test",
    "test:e2e:headed": "cd tests && npx playwright test --headed",
    "test:e2e:debug": "cd tests && npx playwright test --debug",
    "test:all": "npm run test:unit && npm run test:integration && npm run test:e2e",
    "test:coverage": "npm run test:unit -- --coverage"
  }
}
```

### Phase 6: Documentation and Reporting

**6.1 Test Documentation**

**File: `TESTING.md`**

Create comprehensive testing documentation:
- How to run tests locally
- Test organization and structure
- Writing new tests
- Debugging failing tests
- CI/CD integration
- Coverage requirements

**6.2 Test Summary Report**

**File: `test-results/IMPLEMENTATION-SUMMARY.md`**

After completing implementation, create summary:
- Total tests implemented
- Coverage achieved (unit, integration, E2E)
- Test execution times
- Known issues or limitations
- Maintenance recommendations

</requirements>

<implementation_checklist>

## Week 1: Foundation

- [ ] Create test directory structure
- [ ] Configure pytest (pytest.ini, conftest.py)
- [ ] Configure Jest/Vitest for TypeScript
- [ ] Configure Playwright (playwright.config.ts)
- [ ] Install all testing dependencies
- [ ] Create base fixtures and factories
- [ ] Create Page Object Models for Playwright
- [ ] Set up test data (mock responses, test queries)

## Week 2: Unit Tests

- [ ] Implement test_models.py (25-30 tests)
- [ ] Implement test_hupyy_client.py (20-25 tests)
- [ ] Implement es_validators.spec.ts (5-10 tests)
- [ ] Implement es_controller.spec.ts (10-15 tests)
- [ ] Implement HupyyControls.spec.tsx (10 tests)
- [ ] Achieve ≥80% coverage for all modules
- [ ] Fix any failing tests
- [ ] Run linters on test code

## Week 3: Integration Tests

- [ ] Set up mock Hupyy API server
- [ ] Implement test_verification_flow.py (15-20 tests)
- [ ] Implement test_api_contracts.py (5 tests)
- [ ] Configure test Kafka environment
- [ ] Test database integration
- [ ] Achieve ≥60% coverage
- [ ] Fix any flaky tests

## Week 4: E2E Tests

- [ ] Implement verification-ui.spec.ts (10 tests)
- [ ] Implement verification-integration.spec.ts (5 tests)
- [ ] Add screenshot capture for all tests
- [ ] Add video recording for failures
- [ ] Test across different browsers (optional)
- [ ] Optimize test execution time
- [ ] Fix flaky E2E tests

## Week 5: CI/CD and Polish

- [ ] Create GitHub Actions workflow
- [ ] Configure test parallelization
- [ ] Set up coverage reporting (Codecov)
- [ ] Configure quality gates
- [ ] Add test result artifacts
- [ ] Write TESTING.md documentation
- [ ] Create implementation summary report
- [ ] Review all tests for maintainability
- [ ] Final code review and linting

## Week 6: Validation

- [ ] Run full test suite locally
- [ ] Run full test suite in CI
- [ ] Verify coverage thresholds met
- [ ] Verify all quality gates pass
- [ ] Fix any remaining issues
- [ ] Get test suite reviewed
- [ ] Commit and push all test code
- [ ] Create git release

</implementation_checklist>

<success_criteria>

Implementation is complete when:

- ✅ 50-80 unit tests implemented (≥80% coverage)
- ✅ 15-25 integration tests implemented (≥60% coverage)
- ✅ 15-20 E2E tests implemented (critical paths)
- ✅ All tests passing in CI/CD
- ✅ GitHub Actions workflow configured and working
- ✅ Test documentation complete (TESTING.md)
- ✅ Coverage reports integrated (Codecov or similar)
- ✅ Quality gates enforced (coverage thresholds)
- ✅ No flaky tests (consistent pass rate >95%)
- ✅ Test execution time reasonable (<10 min for all tests)
- ✅ All code linted and reviewed
- ✅ Implementation summary created
- ✅ Code committed and released

</success_criteria>

<notes>

## TDD Workflow

Follow strict TDD for all tests:

1. **Red**: Write failing test first
2. **Green**: Write minimal code to pass
3. **Refactor**: Improve while keeping tests green

## Test Quality Checklist

For each test, ensure:
- ✅ Clear, descriptive name
- ✅ Single responsibility (tests one thing)
- ✅ Isolated (no dependencies on other tests)
- ✅ Deterministic (always same result)
- ✅ Fast execution (<100ms for unit tests)
- ✅ Good assertions (specific, meaningful)
- ✅ Proper cleanup (no side effects)

## Common Pitfalls to Avoid

- **Don't skip TDD** - Write tests first, always
- **Don't ignore flaky tests** - Fix immediately
- **Don't hardcode test data** - Use fixtures and factories
- **Don't test implementation details** - Test behavior
- **Don't write slow unit tests** - Mock dependencies
- **Don't forget edge cases** - Test happy path AND error paths
- **Don't commit commented-out tests** - Delete or fix

## Debugging Tips

**Failing unit test:**
- Run with -vv for verbose output
- Use pytest --pdb for debugger
- Check mock configurations
- Verify test data

**Failing integration test:**
- Check service connectivity
- Review logs from services
- Verify test environment setup
- Check database state

**Failing E2E test:**
- Run with --headed to see browser
- Use --debug for step-by-step
- Check screenshots and videos
- Review network requests in browser DevTools

</notes>
