# Test Directory Structure

This directory contains all tests for the PipesHub AI verification feature.

## Directory Organization

```
tests/
├── unit/                           # Unit tests (fast, isolated)
│   └── verification/              # Verification feature unit tests
├── integration/                    # Integration tests (component interactions)
│   ├── test_kafka_flow.py         # Kafka integration tests
│   └── test_hupyy_api_integration.py  # Hupyy API integration tests
├── e2e/                           # End-to-end tests (full workflows)
│   ├── verification/              # Verification feature E2E tests
│   │   └── verification-checkbox.spec.ts
│   └── support/                   # E2E test support files
│       ├── page-objects/          # Page Object Model classes
│       │   └── chat-page.ts       # Chat page interactions
│       └── fixtures/              # Test data and helpers
├── fixtures/                      # Shared test fixtures
│   ├── data/                      # Static test data (JSON, CSV, etc.)
│   └── vcr_cassettes/             # HTTP interaction recordings
└── README.md                      # This file
```

## Test Categories

### Unit Tests (`unit/`)

Fast, isolated tests that test individual functions, classes, or components.

**Python Examples**:
- `backend/python/tests/verification/test_models.py` - Pydantic model validation
- `backend/python/tests/verification/test_hupyy_client.py` - HupyyClient with mocks

**TypeScript Examples**:
- `backend/nodejs/apps/tests/modules/configuration_manager/validators.spec.ts`
- `frontend/src/components/verification/HupyyControls.spec.tsx`

**Characteristics**:
- Run in < 1 second each
- No external dependencies (use mocks)
- Test one thing at a time
- Use `pytest -m unit` or similar

### Integration Tests (`integration/`)

Tests that verify component interactions and external service integration.

**Examples**:
- `test_kafka_flow.py` - Kafka message production and consumption
- `test_hupyy_api_integration.py` - Real Hupyy API calls (with VCR)

**Characteristics**:
- May take several seconds
- Use real or containerized services (Testcontainers)
- Test component boundaries
- Use `pytest -m integration`

### E2E Tests (`e2e/`)

Full user workflow tests using Playwright.

**Examples**:
- `verification/verification-checkbox.spec.ts` - Complete verification flow
- Uses Page Object Model pattern

**Characteristics**:
- Slowest tests (30-60 seconds each)
- Test complete user workflows
- Run against full application stack
- Use `npx playwright test`

## Running Tests

### Quick Commands

```bash
# Run all tests
pytest                          # Python
npm test                        # Node.js/React
npx playwright test             # E2E

# Run specific category
pytest -m unit                  # Unit tests only
pytest -m integration           # Integration tests only
pytest -m verification          # Verification feature only

# Run single test file
pytest tests/verification/test_models.py
npm test -- validators.spec.ts
npx playwright test verification-checkbox.spec.ts

# Run with coverage
pytest --cov=app --cov-report=html
npm test -- --coverage
```

### Advanced Usage

```bash
# Parallel execution
pytest -n auto                  # Use all CPU cores
npm test -- --maxWorkers=4      # Use 4 workers

# Stop on first failure
pytest -x

# Verbose output
pytest -vv
npm test -- --verbose

# Debug mode
pytest -vv -s                   # Show print statements
npx playwright test --headed    # Show browser
```

## Writing New Tests

### 1. Choose Test Type

- **Unit Test**: Testing single function/class in isolation?
- **Integration Test**: Testing component interactions or external services?
- **E2E Test**: Testing complete user workflow?

### 2. Place Test in Correct Location

```bash
# Python unit test
backend/python/tests/verification/test_[component].py

# Node.js unit test
backend/nodejs/apps/tests/modules/[module]/[component].spec.ts

# React component test
frontend/src/components/[component]/[Component].spec.tsx

# Integration test
tests/integration/test_[feature]_integration.py

# E2E test
tests/e2e/[feature]/[workflow].spec.ts
```

### 3. Follow Naming Conventions

**Python**:
- File: `test_*.py` or `*_test.py`
- Class: `Test*` or `*Tests`
- Function: `test_*`

**TypeScript**:
- File: `*.spec.ts` or `*.test.ts`
- Describe block: `describe('Component Name', ...)`
- Test case: `it('should do something', ...)`

### 4. Use Test Templates

See existing tests as templates:

**Python Unit Test**:
```python
class TestComponentName:
    def test_specific_behavior(self):
        # Arrange
        data = {...}

        # Act
        result = function(data)

        # Assert
        assert result == expected
```

**TypeScript Unit Test**:
```typescript
describe('ComponentName', () => {
  it('should test specific behavior', () => {
    // Arrange
    const data = {...};

    // Act
    const result = function(data);

    // Assert
    expect(result).toBe(expected);
  });
});
```

**E2E Test**:
```typescript
test('should complete user workflow', async ({ page }) => {
  // Arrange
  await page.goto('/path');

  // Act
  await page.click('[data-testid="button"]');

  // Assert
  await expect(page.locator('[data-testid="result"]')).toBeVisible();
});
```

## Test Fixtures

### Shared Fixtures (`fixtures/`)

**Data Fixtures** (`fixtures/data/`):
- `sample_verification_request.json`
- `mock_hupyy_response.json`
- `test_documents.json`

**VCR Cassettes** (`fixtures/vcr_cassettes/`):
- HTTP interaction recordings
- Auto-created by VCR.py
- Commit to git for reproducible tests

### Using Fixtures

**Python**:
```python
@pytest.fixture
def sample_data(test_data_dir):
    with open(test_data_dir / "sample.json") as f:
        return json.load(f)

def test_with_fixture(sample_data):
    result = process(sample_data)
    assert result.is_valid
```

**TypeScript**:
```typescript
const sampleData = require('../fixtures/data/sample.json');

it('should process data', () => {
  const result = process(sampleData);
  expect(result.isValid).toBe(true);
});
```

## Page Objects (E2E)

Use Page Object Model pattern for maintainable E2E tests.

**Example** (`e2e/support/page-objects/chat-page.ts`):
```typescript
export class ChatPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async sendMessage(text: string) {
    await this.page.fill('[data-testid="message-input"]', text);
    await this.page.click('[data-testid="send-button"]');
  }
}
```

**Usage in Tests**:
```typescript
import { ChatPage } from '../support/page-objects/chat-page';

test('should send message', async ({ page }) => {
  const chatPage = new ChatPage(page);
  await chatPage.sendMessage('Hello');
  // ...
});
```

## Test Markers

### Python Markers (pytest)

```python
@pytest.mark.unit           # Unit test
@pytest.mark.integration    # Integration test
@pytest.mark.e2e            # E2E test
@pytest.mark.slow           # Slow test
@pytest.mark.verification   # Verification feature
@pytest.mark.asyncio        # Async test
```

Usage:
```bash
pytest -m unit              # Run unit tests only
pytest -m "not slow"        # Skip slow tests
pytest -m "verification and unit"  # Verification unit tests
```

### Jest/Playwright Markers

```typescript
describe.skip('ComponentName', ...);     // Skip entire suite
it.skip('should test', ...);             // Skip single test
it.only('should test', ...);             // Run only this test
```

## Coverage Requirements

Aim for these coverage thresholds:

- **Overall**: 70%+
- **Verification feature**: 80%+
- **Critical paths**: 90%+

Check coverage:
```bash
# Python
pytest --cov=app --cov-report=term-missing

# Node.js/React
npm test -- --coverage
```

## CI/CD Integration

Tests run automatically in GitHub Actions:
- On push to `main` or `develop`
- On pull requests
- Manual workflow trigger

See `.github/workflows/verification-tests.yml`

## Extending Tests

To add tests for new features:

1. **Add unit tests** for each component
2. **Add integration tests** for component interactions
3. **Add E2E tests** for user workflows
4. **Update this README** if adding new test categories
5. **Update CI/CD workflow** if needed

## Getting Help

- Check `TESTING.md` for comprehensive testing guide
- Review existing tests as examples
- Check test output for error messages
- Use `pytest -vv -s` or `npm test -- --verbose` for debugging

---

**Last Updated**: 2025-11-30
