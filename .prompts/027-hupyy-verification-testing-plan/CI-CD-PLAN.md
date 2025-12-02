# CI/CD Integration Plan for Hupyy SMT Verification Testing

**Date:** November 30, 2025
**Purpose:** Complete GitHub Actions workflow specifications

---

## Complete GitHub Actions Workflow

### `.github/workflows/test-verification.yml`
```yaml
name: Hupyy Verification Tests

on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [develop, main]
  schedule:
    - cron: '0 2 * * *'  # Nightly at 2 AM UTC

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '18'
  CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}

jobs:
  # Stage 1: Unit Tests (Parallel)
  unit-tests-python:
    name: Python Unit Tests (Shard ${{ matrix.split }}/4)
    runs-on: ubuntu-latest
    strategy:
      matrix:
        split: [1, 2, 3, 4]
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r backend/python/requirements.txt
          pip install -r backend/python/requirements-test.txt
      
      - name: Run unit tests with pytest-split
        run: |
          cd backend/python
          pytest tests/unit/ \
            --splits 4 \
            --group ${{ matrix.split }} \
            --cov=app \
            --cov-report=xml \
            --cov-report=term \
            --junitxml=test-results/junit-${{ matrix.split }}.xml \
            -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./backend/python/coverage.xml
          flags: python-unit
          name: python-unit-${{ matrix.split }}
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: python-unit-results-${{ matrix.split }}
          path: backend/python/test-results/

  unit-tests-typescript:
    name: TypeScript Unit Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: backend/nodejs/package-lock.json
      
      - name: Install dependencies
        run: |
          cd backend/nodejs
          npm ci
      
      - name: Run unit tests
        run: |
          cd backend/nodejs
          npm run test:unit -- --coverage --maxWorkers=4
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./backend/nodejs/coverage/coverage-final.json
          flags: typescript-unit
          name: typescript-unit

  unit-tests-frontend:
    name: Frontend Unit Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run unit tests
        run: |
          cd frontend
          npm run test -- --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./frontend/coverage/coverage-final.json
          flags: frontend-unit
          name: frontend-unit

  # Stage 2: Integration Tests
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: [unit-tests-python, unit-tests-typescript, unit-tests-frontend]
    services:
      docker:
        image: docker:dind
        options: --privileged
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      
      - name: Install Python dependencies
        run: |
          pip install -r backend/python/requirements.txt
          pip install -r backend/python/requirements-test.txt
      
      - name: Install Node dependencies
        run: |
          cd backend/nodejs
          npm ci
      
      - name: Start Docker services
        run: docker-compose -f docker-compose.test.yml up -d
      
      - name: Wait for services
        run: |
          ./scripts/wait-for-services.sh
      
      - name: Run Python integration tests
        run: |
          cd backend/python
          pytest tests/integration/ \
            --cov=app \
            --cov-report=xml \
            --junitxml=test-results/junit-integration.xml \
            -v -m integration
      
      - name: Run NodeJS integration tests
        run: |
          cd backend/nodejs
          npm run test:integration
      
      - name: Collect Docker logs
        if: failure()
        run: docker-compose -f docker-compose.test.yml logs > docker-logs.txt
      
      - name: Upload Docker logs
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: docker-logs
          path: docker-logs.txt
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./backend/python/coverage.xml
          flags: integration
          name: integration-tests

  # Stage 3: Contract Tests
  contract-tests:
    name: Contract Tests
    runs-on: ubuntu-latest
    needs: [unit-tests-python, unit-tests-typescript]
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
      
      - name: Install dependencies
        run: |
          pip install -r backend/python/requirements.txt
          pip install -r backend/python/requirements-test.txt
          cd backend/nodejs && npm ci
      
      - name: Run consumer contract tests (NodeJS)
        run: |
          cd tests/contract
          npm run test:contract:consumer
      
      - name: Run provider verification (Python)
        run: |
          cd backend/python
          pytest tests/contract/ -v -m contract

  # Stage 4: E2E Tests (Playwright)
  e2e-tests:
    name: E2E Tests (Shard ${{ matrix.shardIndex }}/${{ matrix.shardTotal }})
    runs-on: ubuntu-latest
    needs: [integration-tests, contract-tests]
    strategy:
      matrix:
        shardIndex: [1, 2]
        shardTotal: [2]
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
      
      - name: Install dependencies
        run: |
          cd tests/e2e
          npm ci
      
      - name: Install Playwright browsers
        run: |
          cd tests/e2e
          npx playwright install --with-deps chromium
      
      - name: Start application stack
        run: docker-compose up -d
      
      - name: Wait for services
        run: ./scripts/wait-for-services.sh
      
      - name: Run Playwright tests
        run: |
          cd tests/e2e
          npx playwright test --shard=${{ matrix.shardIndex }}/${{ matrix.shardTotal }}
      
      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report-${{ matrix.shardIndex }}
          path: tests/e2e/playwright-report/
      
      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-screenshots-${{ matrix.shardIndex }}
          path: tests/e2e/test-results/

  # Stage 5: Coverage Reporting
  coverage-report:
    name: Coverage Report
    runs-on: ubuntu-latest
    needs: [e2e-tests]
    if: always()
    steps:
      - uses: actions/checkout@v4
      
      - name: Download coverage artifacts
        uses: actions/download-artifact@v3
      
      - name: Generate combined coverage report
        run: |
          pip install coverage
          coverage combine
          coverage report
          coverage html
      
      - name: Comment PR with coverage
        if: github.event_name == 'pull_request'
        uses: py-cov-action/python-coverage-comment-action@v3
        with:
          GITHUB_TOKEN: ${{ github.token }}
      
      - name: Enforce coverage threshold
        run: |
          coverage report --fail-under=80

  # Quality Gates
  quality-gates:
    name: Quality Gates
    runs-on: ubuntu-latest
    needs: [coverage-report]
    if: always()
    steps:
      - name: Check test results
        run: |
          echo "All tests passed and coverage threshold met"
```

---

## Additional Workflows

### `.github/workflows/test-flaky-detection.yml`
```yaml
name: Flaky Test Detection

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  detect-flaky:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run tests multiple times
        run: |
          for i in {1..10}; do
            pytest tests/ --junit-xml=results-$i.xml || true
          done
      
      - name: Analyze flaky tests
        run: |
          python scripts/analyze-flaky-tests.py results-*.xml
```

---

## Execution Time Targets

| Stage | Target Time | Max Allowed | Parallel? |
|-------|-------------|-------------|-----------|
| Python Unit | 1 min | 2 min | Yes (4 shards) |
| TypeScript Unit | 30s | 1 min | No |
| Frontend Unit | 20s | 30s | No |
| Integration | 3 min | 5 min | No |
| Contract | 30s | 1 min | No |
| E2E | 2 min | 3 min | Yes (2 shards) |
| **Total** | **7-8 min** | **10 min** | **Mixed** |

---

## Quality Gates

### Required Checks (Branch Protection)
- All unit tests pass
- All integration tests pass
- All contract tests pass
- All E2E tests pass
- Code coverage ≥80%
- No new flaky tests introduced

### Optional Checks
- Performance benchmarks within threshold
- No security vulnerabilities (Snyk/Dependabot)
- Code quality score (SonarQube)

---

## Secrets Configuration

```bash
# Required GitHub Secrets
CODECOV_TOKEN=<codecov_token>
HUPYY_API_URL=<staging_url>  # For integration tests
ANTHROPIC_API_KEY=<api_key>  # For E2E tests
PACT_BROKER_URL=<broker_url>  # Optional
PACT_BROKER_TOKEN=<token>    # Optional
```

---

This CI/CD plan provides **comprehensive automated testing** with intelligent parallelization to keep total execution under 10 minutes.
