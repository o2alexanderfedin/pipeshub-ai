# Testing Guide for PipesHub AI

Complete guide to the testing infrastructure for PipesHub AI verification feature.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Test Infrastructure](#test-infrastructure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Overview

The PipesHub AI project uses a comprehensive testing strategy with multiple layers:

```
┌─────────────────────────────────────────────────────────┐
│                    Testing Pyramid                       │
├─────────────────────────────────────────────────────────┤
│  E2E Tests (Playwright)        │ Full user workflows   │
│  ──────────────────────────────┼───────────────────────┤
│  Integration Tests (Pytest)    │ Component integration │
│  ──────────────────────────────┼───────────────────────┤
│  Unit Tests (Pytest/Jest)      │ Individual units      │
└─────────────────────────────────────────────────────────┘
```

### Test Distribution

- **Unit Tests**: ~70% (Fast, isolated)
- **Integration Tests**: ~20% (Component interactions)
- **E2E Tests**: ~10% (Full workflows)

## Quick Start

### Python Backend Tests

```bash
# Install dependencies
cd backend/python
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific tests
pytest tests/verification/ -v
pytest tests/verification/test_models.py::test_valid_request -v
```

### Node.js Backend Tests

```bash
# Install dependencies
cd backend/nodejs/apps
npm install

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific tests
npm test -- validators.spec.ts
```

### React Frontend Tests

```bash
# Install dependencies
cd frontend
npm install

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific tests
npm test -- HupyyControls.spec.tsx
```

### E2E Tests

```bash
# Install Playwright
npm install
npx playwright install

# Run all E2E tests
npx playwright test

# Run in headed mode (see browser)
npx playwright test --headed

# Run specific test
npx playwright test verification-checkbox.spec.ts

# Generate report
npx playwright show-report
```

## Test Infrastructure

### Python (Pytest)

**Configuration**: `backend/python/pytest.ini`

Key features:
- Async test support (`pytest-asyncio`)
- VCR.py for HTTP recording
- Code coverage tracking
- Parallel execution (`pytest-xdist`)
- Markers for test categorization

**Fixtures**: `backend/python/conftest.py`

Global fixtures include:
- Mock Kafka producer/consumer
- Mock Redis client
- Mock database connections
- Mock Anthropic API client
- Test data factories

### TypeScript/JavaScript (Jest)

**Node.js Backend**: `backend/nodejs/apps/jest.config.ts`
**React Frontend**: `frontend/jest.config.ts`

Key features:
- TypeScript support (ts-jest)
- React Testing Library
- Module mocking
- Coverage reporting
- Snapshot testing

### E2E (Playwright)

**Configuration**: `playwright.config.ts`

Key features:
- Cross-browser testing (Chromium, Firefox, WebKit)
- Visual regression testing
- Network mocking
- Video recording on failure
- Parallel execution

## Running Tests

### By Test Type

```bash
# Unit tests only
pytest -m unit
npm test -- --testPathPattern=spec

# Integration tests only
pytest -m integration

# E2E tests only
npx playwright test

# Slow tests excluded
pytest -m "not slow"
```

### By Component

```bash
# Verification feature only
pytest tests/verification/
pytest -m verification

# Configuration manager
npm test -- configuration_manager

# Frontend components
npm test -- src/components/verification/
```

### With Coverage

```bash
# Python with coverage
pytest --cov=app/verification --cov-report=html
open htmlcov/index.html

# Node.js with coverage
npm test -- --coverage
open coverage/lcov-report/index.html

# Frontend with coverage
cd frontend
npm test -- --coverage
open coverage/lcov-report/index.html
```

### In CI/CD

The GitHub Actions workflow automatically runs all tests on:
- Push to `main` or `develop`
- Pull requests
- Manual trigger

See `.github/workflows/verification-tests.yml`

## Writing Tests

### Python Unit Tests

```python
import pytest
from app.verification.models import HupyyRequest

class TestHupyyRequest:
    def test_valid_request(self):
        # Arrange
        data = {
            "informal_text": "Test query",
            "skip_formalization": False,
        }

        # Act
        request = HupyyRequest(**data)

        # Assert
        assert request.informal_text == "Test query"
        assert request.enrich is False  # Forced to False

    @pytest.mark.asyncio
    async def test_async_operation(self):
        # Test async code
        result = await async_function()
        assert result is not None
```

### Python Tests with VCR

```python
import vcr

my_vcr = vcr.VCR(
    cassette_library_dir='tests/fixtures/vcr_cassettes',
    record_mode='once',
)

@pytest.mark.asyncio
@my_vcr.use_cassette('hupyy_verify.yaml')
async def test_api_call():
    # First run: records HTTP interaction
    # Subsequent runs: replays from cassette
    result = await client.verify(request)
    assert result.verdict == "SAT"
```

### TypeScript Unit Tests (Jest)

```typescript
import { describe, expect, it } from '@jest/globals';
import { validateConfig } from './validators';

describe('Configuration Validators', () => {
  it('should validate valid configuration', () => {
    // Arrange
    const config = {
      storageType: 'S3',
      s3BucketName: 'test-bucket',
    };

    // Act
    const result = validateConfig(config);

    // Assert
    expect(result.success).toBe(true);
  });
});
```

### React Component Tests

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { HupyyControls } from './HupyyControls';

it('should call onVerify when button clicked', async () => {
  // Arrange
  const mockOnVerify = jest.fn();
  render(<HupyyControls onVerify={mockOnVerify} />);

  // Act
  const button = screen.getByTestId('verify-button');
  await fireEvent.click(button);

  // Assert
  expect(mockOnVerify).toHaveBeenCalledTimes(1);
});
```

### E2E Tests (Playwright)

```typescript
import { test, expect } from '@playwright/test';

test('should enable verification', async ({ page }) => {
  // Arrange
  await page.goto('/chat');

  // Act
  const checkbox = page.locator('[data-testid="verification-checkbox"]');
  await checkbox.click();

  // Assert
  await expect(checkbox).toBeChecked();
});
```

## CI/CD Integration

### GitHub Actions Workflow

The verification tests workflow (`.github/workflows/verification-tests.yml`) runs:

1. **Python Tests** (Ubuntu)
   - Linting (ruff, mypy)
   - Unit tests
   - Coverage reporting

2. **Node.js Tests** (Ubuntu)
   - Linting (eslint)
   - Unit tests
   - Coverage reporting

3. **Frontend Tests** (Ubuntu)
   - Linting (eslint)
   - Component tests
   - Coverage reporting

4. **Integration Tests** (Ubuntu)
   - With Kafka/Zookeeper services
   - Full component integration

5. **E2E Tests** (Ubuntu)
   - Playwright with all browsers
   - Visual regression tests

### Artifacts

All test runs generate artifacts:
- Test results (JUnit XML)
- Coverage reports (HTML, XML, LCOV)
- Playwright reports
- Screenshots/videos (on failure)

Access artifacts from GitHub Actions run page.

### Coverage Reporting

Coverage reports are automatically uploaded to Codecov:
- Backend Python coverage
- Backend Node.js coverage
- Frontend coverage

## Troubleshooting

### Common Issues

#### Python: ModuleNotFoundError

```bash
# Ensure package is installed in editable mode
cd backend/python
pip install -e .
```

#### Node.js: Cannot find module

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### Playwright: Browser not installed

```bash
# Install browsers
npx playwright install chromium firefox webkit
```

#### VCR: Cassette not found

```bash
# Re-record cassettes
rm -rf tests/fixtures/vcr_cassettes/
pytest tests/verification/test_hupyy_client.py -v
```

#### Tests timing out

```bash
# Increase timeout
pytest --timeout=300  # 5 minutes

# Or in test file
@pytest.mark.timeout(300)
def test_slow_operation():
    ...
```

### Debug Mode

```bash
# Python: verbose output with print statements
pytest -vv -s

# Node.js: run single test with debugging
npm test -- --testNamePattern="specific test" --runInBand

# Playwright: headed mode with slow motion
npx playwright test --headed --slow-mo=500
```

### Getting Help

1. Check test logs for specific error messages
2. Review test documentation in `tests/README.md`
3. Check test specifications in `docs/UNIT-TEST-SPECS.md` (if exists)
4. Review example tests in each test directory

## Best Practices

### Writing Tests

1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **One assertion per test** (when possible)
3. **Descriptive test names**: `test_should_validate_empty_string_as_invalid`
4. **Use fixtures**: Share setup code across tests
5. **Mock external dependencies**: Don't hit real APIs in unit tests
6. **Test edge cases**: Empty, null, boundaries, errors

### Test Organization

```
tests/
├── unit/                    # Fast, isolated tests
├── integration/             # Component interactions
├── e2e/                     # Full user workflows
├── fixtures/                # Test data
│   ├── data/               # Static test data
│   └── vcr_cassettes/      # HTTP recordings
└── support/                 # Test helpers
    └── page-objects/       # E2E page objects
```

### Performance

- Keep unit tests fast (< 1 second each)
- Use mocks for external services
- Run tests in parallel when possible
- Mark slow tests with `@pytest.mark.slow`
- Skip slow tests in development: `pytest -m "not slow"`

## Next Steps

- Review `tests/README.md` for detailed test organization
- Check example tests in each test directory
- Review CI/CD workflow in `.github/workflows/`
- Add new tests following the patterns shown

---

**Last Updated**: 2025-11-30
**Maintainer**: PipesHub AI Team
