# Code Examples for Hupyy SMT Verification Testing

**Date:** November 30, 2025
**Project:** PipesHub AI - Hupyy SMT Verification Integration
**Purpose:** Practical code examples for all major testing patterns

---

## Table of Contents

1. [Mocking Hupyy API](#1-mocking-hupyy-api)
2. [Testing Kafka Message Flows](#2-testing-kafka-message-flows)
3. [Playwright UI Testing Structure](#3-playwright-ui-testing-structure)
4. [Integration Test Setup](#4-integration-test-setup)
5. [CI/CD Workflow Configuration](#5-cicd-workflow-configuration)
6. [Test Data Factories](#6-test-data-factories)
7. [Contract Testing](#7-contract-testing)
8. [SMT Verification Testing](#8-smt-verification-testing)

---

## 1. Mocking Hupyy API

### 1.1 VCR Pattern (Python)

#### Basic VCR Usage
```python
# tests/integration/test_hupyy_client.py
import vcr
import pytest
from src.hupyy.client import HupyyClient

# Configure VCR with custom cassette directory
my_vcr = vcr.VCR(
    cassette_library_dir='tests/fixtures/vcr_cassettes',
    record_mode='once',  # 'once', 'new_episodes', 'all', 'none'
    match_on=['uri', 'method', 'body'],
    filter_headers=['authorization'],  # Don't record auth tokens
)

@my_vcr.use_cassette('hupyy_sat_result.yaml')
def test_verify_chunk_sat_result():
    """Test verification with SAT result using recorded cassette."""
    client = HupyyClient(api_key='test-key')

    chunk = {
        'text': 'The sum of two numbers is ten',
        'formalization': '∃x,y. x + y = 10'
    }

    result = client.verify_chunk(chunk)

    assert result['check_sat_result'] == 'SAT'
    assert result['formalization_similarity'] > 0.8
    assert 'proof' in result
    assert result['metadata']['solver'] == 'z3'


@my_vcr.use_cassette('hupyy_unsat_result.yaml')
def test_verify_chunk_unsat_result():
    """Test verification with UNSAT result using recorded cassette."""
    client = HupyyClient(api_key='test-key')

    chunk = {
        'text': 'A number is both even and odd',
        'formalization': '∃x. (x mod 2 = 0) ∧ (x mod 2 = 1)'
    }

    result = client.verify_chunk(chunk)

    assert result['check_sat_result'] == 'UNSAT'
    assert 'proof' in result
    assert 'unsat_core' in result['metadata']


@my_vcr.use_cassette('hupyy_unknown_result.yaml')
def test_verify_chunk_unknown_result():
    """Test verification with UNKNOWN result (timeout/complex)."""
    client = HupyyClient(api_key='test-key')

    chunk = {
        'text': 'Complex non-linear arithmetic formula',
        'formalization': '∃x,y. x^3 + y^3 = z^3'  # Hard problem
    }

    result = client.verify_chunk(chunk)

    assert result['check_sat_result'] == 'UNKNOWN'
    assert result['metadata'].get('reason') in ['timeout', 'incomplete']
```

#### pytest-recording Plugin
```python
# tests/integration/test_hupyy_with_plugin.py
import pytest
from src.hupyy.client import HupyyClient

@pytest.mark.vcr
def test_verify_with_plugin():
    """Using pytest-recording plugin for automatic cassette management."""
    client = HupyyClient(api_key='test-key')
    result = client.verify_chunk({'text': 'test', 'formalization': 'x > 0'})
    assert result['check_sat_result'] in ['SAT', 'UNSAT', 'UNKNOWN']


# Record new cassettes with: pytest --record-mode=rewrite
# Use existing cassettes: pytest (default)
```

#### Cassette Example (YAML)
```yaml
# tests/fixtures/vcr_cassettes/hupyy_sat_result.yaml
interactions:
- request:
    body: '{"text": "The sum of two numbers is ten", "formalization": "\u2203x,y. x + y = 10"}'
    headers:
      Content-Type: [application/json]
      Authorization: [Bearer ***]  # Filtered
    method: POST
    uri: https://hupyy.example.com/api/v1/pipeline/process
  response:
    status:
      code: 200
      message: OK
    headers:
      Content-Type: [application/json]
    body:
      string: '{"check_sat_result": "SAT", "formalization_similarity": 0.92, "proof": {"model": {"x": 3, "y": 7}}, "metadata": {"solver": "z3", "time_ms": 42}}'
version: 1
```

---

### 1.2 Mock with responses Library (Python)

```python
# tests/unit/test_hupyy_client_mocked.py
import responses
import pytest
from src.hupyy.client import HupyyClient

@responses.activate
def test_verify_chunk_sat_mocked():
    """Unit test with mocked HTTP response."""
    # Mock the Hupyy API endpoint
    responses.add(
        responses.POST,
        'https://hupyy.example.com/api/v1/pipeline/process',
        json={
            'check_sat_result': 'SAT',
            'formalization_similarity': 0.95,
            'proof': {'model': {'x': 5}},
            'metadata': {'solver': 'z3', 'time_ms': 30}
        },
        status=200,
        headers={'Content-Type': 'application/json'}
    )

    client = HupyyClient(api_key='test-key')
    result = client.verify_chunk({
        'text': 'x is 5',
        'formalization': 'x = 5'
    })

    assert result['check_sat_result'] == 'SAT'
    assert result['proof']['model']['x'] == 5

    # Verify request was made correctly
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == 'https://hupyy.example.com/api/v1/pipeline/process'


@responses.activate
def test_verify_chunk_error_handling():
    """Test error handling when Hupyy API fails."""
    responses.add(
        responses.POST,
        'https://hupyy.example.com/api/v1/pipeline/process',
        json={'error': 'Invalid formalization'},
        status=400
    )

    client = HupyyClient(api_key='test-key')

    with pytest.raises(HupyyAPIError) as exc_info:
        client.verify_chunk({'text': 'invalid', 'formalization': '??'})

    assert 'Invalid formalization' in str(exc_info.value)


@responses.activate
def test_verify_chunk_retry_logic():
    """Test retry logic on transient failures."""
    # First call fails with 503, second succeeds
    responses.add(
        responses.POST,
        'https://hupyy.example.com/api/v1/pipeline/process',
        json={'error': 'Service unavailable'},
        status=503
    )
    responses.add(
        responses.POST,
        'https://hupyy.example.com/api/v1/pipeline/process',
        json={'check_sat_result': 'SAT', 'proof': {}},
        status=200
    )

    client = HupyyClient(api_key='test-key', max_retries=3)
    result = client.verify_chunk({'text': 'test', 'formalization': 'x > 0'})

    assert result['check_sat_result'] == 'SAT'
    assert len(responses.calls) == 2  # Failed once, succeeded second time
```

---

### 1.3 MSW (TypeScript)

```typescript
// tests/mocks/handlers.ts
import { rest } from 'msw'

export const handlers = [
  rest.post('/api/verify', (req, res, ctx) => {
    const { query, verification_enabled } = req.body as any

    if (!verification_enabled) {
      return res(ctx.status(400), ctx.json({ error: 'Verification not enabled' }))
    }

    return res(
      ctx.status(200),
      ctx.json({
        task_id: 'task-12345',
        status: 'queued'
      })
    )
  }),

  rest.get('/api/verify/:taskId', (req, res, ctx) => {
    const { taskId } = req.params

    return res(
      ctx.status(200),
      ctx.json({
        task_id: taskId,
        status: 'completed',
        result: {
          verdict: 'SAT',
          confidence: 0.95,
          proof: { model: { x: 5 } }
        }
      })
    )
  })
]

// tests/mocks/server.ts
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const server = setupServer(...handlers)

// tests/setup.ts
import { server } from './mocks/server'

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

```typescript
// tests/services/verification.test.ts
import { server } from '../mocks/server'
import { rest } from 'msw'
import { VerificationService } from '@/services/verification'

describe('VerificationService', () => {
  it('should submit verification request', async () => {
    const service = new VerificationService()

    const result = await service.verify({
      query: 'test query',
      verification_enabled: true
    })

    expect(result.task_id).toBe('task-12345')
    expect(result.status).toBe('queued')
  })

  it('should handle API errors', async () => {
    // Override handler for this test
    server.use(
      rest.post('/api/verify', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Internal error' }))
      })
    )

    const service = new VerificationService()

    await expect(
      service.verify({ query: 'test', verification_enabled: true })
    ).rejects.toThrow('Internal error')
  })

  it('should poll for results', async () => {
    const service = new VerificationService()

    const result = await service.verifyAndWait({
      query: 'test query',
      verification_enabled: true
    })

    expect(result.status).toBe('completed')
    expect(result.result.verdict).toBe('SAT')
  })
})
```

---

## 2. Testing Kafka Message Flows

### 2.1 Unit Tests with MockConsumer/MockProducer (Python)

```python
# tests/unit/test_kafka_producer.py
from unittest.mock import MagicMock, patch
import pytest
from src.kafka.producer import VerificationProducer

def test_publish_verification_request():
    """Unit test for Kafka producer using mocks."""
    # Create mock producer
    mock_producer = MagicMock()

    with patch('src.kafka.producer.KafkaProducer', return_value=mock_producer):
        producer = VerificationProducer(
            bootstrap_servers='localhost:9092',
            topic='verify_chunks'
        )

        chunk = {
            'chunk_id': 'chunk-123',
            'text': 'test text',
            'formalization': 'x > 0'
        }

        producer.publish_chunk(chunk)

        # Verify produce was called correctly
        mock_producer.send.assert_called_once()
        call_args = mock_producer.send.call_args

        assert call_args[0][0] == 'verify_chunks'  # topic
        assert call_args[1]['key'] == b'chunk-123'
        assert b'test text' in call_args[1]['value']


def test_publish_with_error_handling():
    """Test error handling in producer."""
    mock_producer = MagicMock()
    mock_producer.send.side_effect = Exception('Broker unavailable')

    with patch('src.kafka.producer.KafkaProducer', return_value=mock_producer):
        producer = VerificationProducer(
            bootstrap_servers='localhost:9092',
            topic='verify_chunks'
        )

        with pytest.raises(KafkaProducerError):
            producer.publish_chunk({'chunk_id': 'test'})
```

```python
# tests/unit/test_kafka_consumer.py
from unittest.mock import MagicMock, patch
from src.kafka.consumer import VerificationConsumer

def test_consume_verification_messages():
    """Unit test for Kafka consumer using mocks."""
    # Create mock consumer with messages
    mock_consumer = MagicMock()
    mock_message = MagicMock()
    mock_message.value = b'{"chunk_id": "chunk-123", "text": "test"}'
    mock_message.offset = 100
    mock_message.partition = 0

    mock_consumer.__iter__.return_value = [mock_message]

    with patch('src.kafka.consumer.KafkaConsumer', return_value=mock_consumer):
        consumer = VerificationConsumer(
            bootstrap_servers='localhost:9092',
            topic='verify_chunks',
            group_id='orchestrator'
        )

        messages = list(consumer.consume(max_messages=1))

        assert len(messages) == 1
        assert messages[0]['chunk_id'] == 'chunk-123'

        # Verify consumer subscribed correctly
        mock_consumer.subscribe.assert_called_once_with(['verify_chunks'])


def test_offset_management():
    """Test manual offset commit."""
    mock_consumer = MagicMock()

    with patch('src.kafka.consumer.KafkaConsumer', return_value=mock_consumer):
        consumer = VerificationConsumer(
            bootstrap_servers='localhost:9092',
            topic='verify_chunks',
            group_id='orchestrator',
            enable_auto_commit=False
        )

        # Process message and commit offset
        consumer.commit_offset(partition=0, offset=100)

        # Verify commit was called
        mock_consumer.commit.assert_called_once()
```

---

### 2.2 Integration Tests with Testcontainers (Python)

```python
# tests/integration/test_kafka_flow.py
import pytest
from testcontainers.kafka import KafkaContainer
from confluent_kafka import Producer, Consumer
import json
import time

@pytest.fixture(scope='module')
def kafka_container():
    """Start Kafka container for integration tests."""
    with KafkaContainer('confluentinc/cp-kafka:7.5.0') as kafka:
        # Wait for Kafka to be ready
        kafka.start()
        yield kafka


def test_end_to_end_kafka_flow(kafka_container):
    """Integration test for full Kafka producer-consumer flow."""
    bootstrap_server = kafka_container.get_bootstrap_server()
    topic = 'test_verify_chunks'

    # Create producer
    producer = Producer({
        'bootstrap.servers': bootstrap_server,
        'enable.idempotence': True
    })

    # Publish message
    message = {
        'chunk_id': 'chunk-123',
        'text': 'test text',
        'formalization': 'x > 0'
    }

    producer.produce(
        topic,
        key='chunk-123',
        value=json.dumps(message).encode('utf-8')
    )
    producer.flush()

    # Create consumer
    consumer = Consumer({
        'bootstrap.servers': bootstrap_server,
        'group.id': 'test-group',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    })

    consumer.subscribe([topic])

    # Consume message
    msg = consumer.poll(timeout=5.0)

    assert msg is not None
    assert msg.error() is None

    consumed_data = json.loads(msg.value().decode('utf-8'))
    assert consumed_data['chunk_id'] == 'chunk-123'
    assert consumed_data['text'] == 'test text'

    # Commit offset
    consumer.commit(msg)

    consumer.close()


def test_kafka_idempotency(kafka_container):
    """Test idempotent producer doesn't create duplicates."""
    bootstrap_server = kafka_container.get_bootstrap_server()
    topic = 'test_idempotency'

    producer = Producer({
        'bootstrap.servers': bootstrap_server,
        'enable.idempotence': True
    })

    # Send same message twice
    for _ in range(2):
        producer.produce(
            topic,
            key='dedup-key',
            value=b'duplicate message'
        )
    producer.flush()

    # Consume all messages
    consumer = Consumer({
        'bootstrap.servers': bootstrap_server,
        'group.id': 'dedup-test',
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe([topic])

    messages = []
    start_time = time.time()
    while time.time() - start_time < 3:
        msg = consumer.poll(timeout=1.0)
        if msg and not msg.error():
            messages.append(msg.value())

    consumer.close()

    # Should only receive one message due to idempotency
    assert len(messages) == 1


def test_offset_reset_behavior(kafka_container):
    """Test offset reset strategies."""
    bootstrap_server = kafka_container.get_bootstrap_server()
    topic = 'test_offset_reset'

    # Produce messages
    producer = Producer({'bootstrap.servers': bootstrap_server})
    for i in range(10):
        producer.produce(topic, value=f'message-{i}'.encode())
    producer.flush()

    # Consumer with 'earliest' reads all messages
    consumer_earliest = Consumer({
        'bootstrap.servers': bootstrap_server,
        'group.id': 'earliest-group',
        'auto.offset.reset': 'earliest'
    })
    consumer_earliest.subscribe([topic])

    earliest_messages = []
    for _ in range(10):
        msg = consumer_earliest.poll(timeout=1.0)
        if msg and not msg.error():
            earliest_messages.append(msg.value())

    assert len(earliest_messages) == 10
    consumer_earliest.close()

    # Consumer with 'latest' reads only new messages
    consumer_latest = Consumer({
        'bootstrap.servers': bootstrap_server,
        'group.id': 'latest-group',
        'auto.offset.reset': 'latest'
    })
    consumer_latest.subscribe([topic])

    latest_messages = []
    msg = consumer_latest.poll(timeout=1.0)
    if msg and not msg.error():
        latest_messages.append(msg.value())

    assert len(latest_messages) == 0  # No new messages
    consumer_latest.close()
```

---

### 2.3 pytest-kafka Plugin

```python
# tests/integration/test_with_pytest_kafka.py
import pytest

@pytest.fixture(scope='session')
def kafka_server():
    """Provided by pytest-kafka plugin."""
    # Automatically starts Kafka server
    pass


def test_with_kafka_fixture(kafka_server, kafka_producer, kafka_consumer):
    """Using pytest-kafka fixtures."""
    topic = 'test-topic'

    # Producer fixture automatically configured
    kafka_producer.send(topic, b'test message')
    kafka_producer.flush()

    # Consumer fixture automatically configured
    kafka_consumer.subscribe([topic])
    msg = next(kafka_consumer)

    assert msg.value == b'test message'
```

---

## 3. Playwright UI Testing Structure

### 3.1 Page Object Model Implementation

```typescript
// tests/pages/ChatPage.ts
import { Page, Locator } from '@playwright/test'

export class ChatPage {
  readonly page: Page
  readonly verificationCheckbox: Locator
  readonly queryInput: Locator
  readonly submitButton: Locator
  readonly verificationResult: Locator
  readonly verificationBadge: Locator
  readonly loadingSpinner: Locator

  constructor(page: Page) {
    this.page = page
    this.verificationCheckbox = page.getByRole('checkbox', {
      name: /enable verification/i
    })
    this.queryInput = page.getByPlaceholder(/enter.*query/i)
    this.submitButton = page.getByRole('button', { name: /submit/i })
    this.verificationResult = page.getByTestId('verification-result')
    this.verificationBadge = page.getByTestId('verification-badge')
    this.loadingSpinner = page.getByTestId('loading-spinner')
  }

  async goto() {
    await this.page.goto('/chat')
    await this.page.waitForLoadState('networkidle')
  }

  async enableVerification() {
    await this.verificationCheckbox.check()
    await this.page.waitForTimeout(100) // UI update
  }

  async disableVerification() {
    await this.verificationCheckbox.uncheck()
  }

  async submitQuery(query: string) {
    await this.queryInput.fill(query)
    await this.submitButton.click()
  }

  async submitQueryWithVerification(query: string) {
    await this.enableVerification()
    await this.submitQuery(query)
  }

  async waitForVerificationResult() {
    // Wait for loading to complete
    await this.loadingSpinner.waitFor({ state: 'hidden', timeout: 30000 })
    await this.verificationResult.waitFor({ state: 'visible' })
  }

  async getVerificationVerdict(): Promise<string> {
    await this.waitForVerificationResult()
    return await this.verificationResult.textContent() || ''
  }

  async getVerificationBadgeStatus(): Promise<'verified' | 'unverified' | 'unknown'> {
    const badgeText = await this.verificationBadge.textContent() || ''
    if (badgeText.includes('Verified')) return 'verified'
    if (badgeText.includes('Unverified')) return 'unverified'
    return 'unknown'
  }

  async hasVerificationCheckbox(): Promise<boolean> {
    return await this.verificationCheckbox.isVisible()
  }
}
```

```typescript
// tests/pages/SettingsPage.ts
import { Page, Locator } from '@playwright/test'

export class SettingsPage {
  readonly page: Page
  readonly verificationToggle: Locator
  readonly hupyyApiKeyInput: Locator
  readonly saveButton: Locator

  constructor(page: Page) {
    this.page = page
    this.verificationToggle = page.getByRole('switch', {
      name: /enable.*verification/i
    })
    this.hupyyApiKeyInput = page.getByLabel(/hupyy api key/i)
    this.saveButton = page.getByRole('button', { name: /save/i })
  }

  async goto() {
    await this.page.goto('/settings')
  }

  async enableGlobalVerification() {
    await this.verificationToggle.check()
  }

  async setHupyyApiKey(apiKey: string) {
    await this.hupyyApiKeyInput.fill(apiKey)
  }

  async saveSettings() {
    await this.saveButton.click()
    await this.page.waitForSelector('.toast-success')
  }
}
```

---

### 3.2 E2E Test Examples

```typescript
// tests/e2e/verification-flow.spec.ts
import { test, expect } from '@playwright/test'
import { ChatPage } from '../pages/ChatPage'
import { SettingsPage } from '../pages/SettingsPage'

test.describe('Verification Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Setup: Enable verification in settings
    const settings = new SettingsPage(page)
    await settings.goto()
    await settings.enableGlobalVerification()
    await settings.setHupyyApiKey('test-api-key')
    await settings.saveSettings()
  })

  test('should verify SAT query', async ({ page }) => {
    const chat = new ChatPage(page)
    await chat.goto()

    // Enable verification checkbox
    await chat.enableVerification()

    // Submit query
    await chat.submitQuery('The sum of 3 and 7 is 10')

    // Wait for and check result
    await chat.waitForVerificationResult()
    const verdict = await chat.getVerificationVerdict()

    expect(verdict).toContain('SAT')
    expect(verdict).toContain('Verified')

    const badgeStatus = await chat.getVerificationBadgeStatus()
    expect(badgeStatus).toBe('verified')
  })

  test('should verify UNSAT query', async ({ page }) => {
    const chat = new ChatPage(page)
    await chat.goto()

    await chat.submitQueryWithVerification(
      'A number is both even and odd'
    )

    await chat.waitForVerificationResult()
    const verdict = await chat.getVerificationVerdict()

    expect(verdict).toContain('UNSAT')
    expect(verdict).toContain('Contradiction')
  })

  test('should handle UNKNOWN result', async ({ page }) => {
    const chat = new ChatPage(page)
    await chat.goto()

    await chat.submitQueryWithVerification(
      'Complex non-linear formula: x^3 + y^3 = z^3'
    )

    await chat.waitForVerificationResult()
    const verdict = await chat.getVerificationVerdict()

    expect(verdict).toContain('UNKNOWN')
    expect(verdict).toMatch(/timeout|incomplete/i)

    const badgeStatus = await chat.getVerificationBadgeStatus()
    expect(badgeStatus).toBe('unknown')
  })

  test('should work without verification enabled', async ({ page }) => {
    const chat = new ChatPage(page)
    await chat.goto()

    // Don't enable verification
    await chat.submitQuery('Normal query without verification')

    // Should not see verification result
    await expect(chat.verificationResult).not.toBeVisible()
  })

  test('should toggle verification on/off', async ({ page }) => {
    const chat = new ChatPage(page)
    await chat.goto()

    // Initially unchecked
    await expect(chat.verificationCheckbox).not.toBeChecked()

    // Enable
    await chat.enableVerification()
    await expect(chat.verificationCheckbox).toBeChecked()

    // Disable
    await chat.disableVerification()
    await expect(chat.verificationCheckbox).not.toBeChecked()
  })
})
```

---

### 3.3 Visual Regression Testing

```typescript
// tests/e2e/visual-regression.spec.ts
import { test, expect } from '@playwright/test'
import { ChatPage } from '../pages/ChatPage'

test.describe('Visual Regression Tests', () => {
  test('chat page baseline', async ({ page }) => {
    const chat = new ChatPage(page)
    await chat.goto()

    // Full page screenshot
    await expect(page).toHaveScreenshot('chat-page.png', {
      fullPage: true,
      maxDiffPixels: 100
    })
  })

  test('verification checkbox states', async ({ page }) => {
    const chat = new ChatPage(page)
    await chat.goto()

    // Screenshot unchecked state
    await expect(chat.verificationCheckbox).toHaveScreenshot(
      'checkbox-unchecked.png'
    )

    // Screenshot checked state
    await chat.enableVerification()
    await expect(chat.verificationCheckbox).toHaveScreenshot(
      'checkbox-checked.png'
    )
  })

  test('verification result display', async ({ page }) => {
    const chat = new ChatPage(page)
    await chat.goto()

    await chat.submitQueryWithVerification('Test query')
    await chat.waitForVerificationResult()

    // Screenshot verification result card
    await expect(chat.verificationResult).toHaveScreenshot(
      'verification-result-sat.png',
      { maxDiffPixels: 50 }
    )
  })
})
```

---

### 3.4 Accessibility Testing

```typescript
// tests/e2e/accessibility.spec.ts
import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { ChatPage } from '../pages/ChatPage'

test.describe('Accessibility Tests', () => {
  test('chat page should have no accessibility violations', async ({ page }) => {
    const chat = new ChatPage(page)
    await chat.goto()

    const results = await new AxeBuilder({ page })
      .analyze()

    expect(results.violations).toEqual([])
  })

  test('verification checkbox should be keyboard accessible', async ({ page }) => {
    const chat = new ChatPage(page)
    await chat.goto()

    // Tab to checkbox
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')  // Adjust based on tab order

    // Space to toggle
    await page.keyboard.press('Space')
    await expect(chat.verificationCheckbox).toBeChecked()

    await page.keyboard.press('Space')
    await expect(chat.verificationCheckbox).not.toBeChecked()
  })

  test('verification result should have proper ARIA labels', async ({ page }) => {
    const chat = new ChatPage(page)
    await chat.goto()

    await chat.submitQueryWithVerification('Test query')
    await chat.waitForVerificationResult()

    const result = chat.verificationResult

    // Check for ARIA attributes
    await expect(result).toHaveAttribute('role', 'status')
    await expect(result).toHaveAttribute('aria-live', 'polite')
  })
})
```

---

## 4. Integration Test Setup

### 4.1 Docker Compose Test Configuration

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: testdb
      POSTGRES_USER: testuser
      POSTGRES_PASSWORD: testpass
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U testuser"]
      interval: 5s
      timeout: 5s
      retries: 5

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:9092"]
      interval: 10s
      timeout: 10s
      retries: 5

  backend-node:
    build:
      context: ./backend-node
      dockerfile: Dockerfile.test
    depends_on:
      postgres:
        condition: service_healthy
      kafka:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://testuser:testpass@postgres:5432/testdb
      KAFKA_BROKERS: kafka:9092
      PYTHON_BACKEND_URL: http://backend-python:8000
    ports:
      - "3000:3000"

  backend-python:
    build:
      context: ./backend-python
      dockerfile: Dockerfile.test
    depends_on:
      kafka:
        condition: service_healthy
    environment:
      KAFKA_BROKERS: kafka:9092
      HUPYY_API_URL: http://mock-hupyy:8080
    ports:
      - "8000:8000"

  mock-hupyy:
    image: mockserver/mockserver:latest
    ports:
      - "8080:1080"
    environment:
      MOCKSERVER_INITIALIZATION_JSON_PATH: /config/hupyy-mock.json
    volumes:
      - ./tests/fixtures/hupyy-mock.json:/config/hupyy-mock.json
```

---

### 4.2 pytest with Docker Compose

```python
# tests/integration/conftest.py
import pytest
import subprocess
import time
import requests
from testcontainers.compose import DockerCompose

@pytest.fixture(scope='session')
def docker_services():
    """Start all services with docker-compose."""
    compose = DockerCompose(
        filepath='.',
        compose_file_name='docker-compose.test.yml',
        pull=True
    )

    with compose:
        # Wait for services to be healthy
        wait_for_postgres(compose)
        wait_for_kafka(compose)
        wait_for_backends(compose)

        yield compose


def wait_for_postgres(compose, timeout=30):
    """Wait for PostgreSQL to be ready."""
    start = time.time()
    while time.time() - start < timeout:
        result = compose.exec_in_container(
            'postgres',
            ['pg_isready', '-U', 'testuser']
        )
        if result.exit_code == 0:
            return
        time.sleep(1)
    raise TimeoutError('PostgreSQL not ready')


def wait_for_kafka(compose, timeout=60):
    """Wait for Kafka to be ready."""
    start = time.time()
    while time.time() - start < timeout:
        result = compose.exec_in_container(
            'kafka',
            ['kafka-broker-api-versions', '--bootstrap-server', 'localhost:9092']
        )
        if result.exit_code == 0:
            return
        time.sleep(2)
    raise TimeoutError('Kafka not ready')


def wait_for_backends(compose, timeout=30):
    """Wait for backend services to be ready."""
    services = {
        'backend-node': 'http://localhost:3000/health',
        'backend-python': 'http://localhost:8000/health'
    }

    start = time.time()
    while time.time() - start < timeout:
        all_ready = True
        for service, url in services.items():
            try:
                response = requests.get(url, timeout=1)
                if response.status_code != 200:
                    all_ready = False
            except requests.RequestException:
                all_ready = False

        if all_ready:
            return
        time.sleep(2)

    raise TimeoutError('Backend services not ready')


@pytest.fixture
def db_session(docker_services):
    """Provide database session with cleanup."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine('postgresql://testuser:testpass@localhost:5433/testdb')
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    # Cleanup: rollback transaction
    session.rollback()
    session.close()


@pytest.fixture
def kafka_producer(docker_services):
    """Provide Kafka producer."""
    from confluent_kafka import Producer

    producer = Producer({'bootstrap.servers': 'localhost:9092'})

    yield producer

    producer.flush()


@pytest.fixture
def kafka_consumer(docker_services):
    """Provide Kafka consumer."""
    from confluent_kafka import Consumer

    consumer = Consumer({
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'test-group',
        'auto.offset.reset': 'earliest'
    })

    yield consumer

    consumer.close()
```

```python
# tests/integration/test_full_stack.py
import pytest
import requests
import json

def test_end_to_end_verification_flow(docker_services, kafka_consumer):
    """Test complete verification flow across all services."""
    # Subscribe to Kafka topic
    kafka_consumer.subscribe(['verify_chunks'])

    # Step 1: Submit query to NodeJS backend
    response = requests.post(
        'http://localhost:3000/api/verify',
        json={
            'query': 'The sum of 3 and 7 is 10',
            'verification_enabled': True
        }
    )

    assert response.status_code == 200
    data = response.json()
    task_id = data['task_id']

    # Step 2: Verify message published to Kafka
    message = kafka_consumer.poll(timeout=5.0)
    assert message is not None
    assert message.error() is None

    chunk_data = json.loads(message.value().decode('utf-8'))
    assert 'text' in chunk_data
    assert chunk_data['text'] == 'The sum of 3 and 7 is 10'

    # Step 3: Poll for verification result
    max_attempts = 30
    for _ in range(max_attempts):
        result_response = requests.get(
            f'http://localhost:3000/api/verify/{task_id}'
        )

        if result_response.status_code == 200:
            result_data = result_response.json()
            if result_data['status'] == 'completed':
                assert result_data['result']['verdict'] in ['SAT', 'UNSAT', 'UNKNOWN']
                return

        import time
        time.sleep(1)

    pytest.fail('Verification did not complete in time')
```

---

## 5. CI/CD Workflow Configuration

### 5.1 GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '20'

jobs:
  # Python unit tests (parallelized)
  python-unit:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        split: [1, 2, 3, 4]  # 4-way split
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run Python unit tests
        run: |
          pytest backend-python/tests/unit \
            --splits 4 \
            --group ${{ matrix.split }} \
            --cov=backend-python/src \
            --cov-report=xml \
            --junitxml=test-results/junit-${{ matrix.split }}.xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: python-unit
          fail_ci_if_error: false

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: python-unit-results-${{ matrix.split }}
          path: test-results/

  # Python integration tests (sequential)
  python-integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Start Docker services
        run: docker-compose -f docker-compose.test.yml up -d

      - name: Wait for services
        run: |
          bash scripts/wait-for-services.sh

      - name: Run Python integration tests
        run: |
          pytest backend-python/tests/integration \
            --cov=backend-python/src \
            --cov-report=xml \
            --junitxml=test-results/junit-integration.xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: python-integration

      - name: Stop Docker services
        if: always()
        run: docker-compose -f docker-compose.test.yml down

  # TypeScript tests
  typescript:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shard: [1, 2]  # 2-way split
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: backend-node/package-lock.json

      - name: Install dependencies
        working-directory: backend-node
        run: npm ci

      - name: Run TypeScript tests
        working-directory: backend-node
        run: |
          npm test -- \
            --shard=${{ matrix.shard }}/2 \
            --coverage \
            --coverageReporters=json \
            --coverageReporters=lcov

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend-node/coverage/lcov.info
          flags: typescript

      - name: Type check
        working-directory: backend-node
        run: npx tsc --noEmit

      - name: Lint
        working-directory: backend-node
        run: npm run lint

  # Playwright E2E tests
  playwright:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shard: [1, 2]  # 2-way split
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps chromium

      - name: Start Docker services
        run: docker-compose -f docker-compose.test.yml up -d

      - name: Wait for services
        run: bash scripts/wait-for-services.sh

      - name: Run Playwright tests
        run: |
          npx playwright test \
            --shard=${{ matrix.shard }}/2 \
            --reporter=html

      - name: Upload Playwright report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report-${{ matrix.shard }}
          path: playwright-report/
          retention-days: 30

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-results-${{ matrix.shard }}
          path: test-results/

      - name: Stop Docker services
        if: always()
        run: docker-compose -f docker-compose.test.yml down

  # Contract tests
  contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python & Node.js
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
          cd backend-node && npm ci

      - name: Run consumer tests (NodeJS)
        working-directory: backend-node
        run: npm run test:pact

      - name: Publish contracts
        run: |
          # Upload pacts to broker or save as artifacts
          cp backend-node/pacts/*.json pacts/

      - name: Run provider verification (Python)
        run: |
          pytest backend-python/tests/contract \
            --junitxml=test-results/junit-contract.xml

      - name: Upload pacts
        uses: actions/upload-artifact@v3
        with:
          name: pacts
          path: pacts/

  # Quality gates
  quality-gate:
    runs-on: ubuntu-latest
    needs: [python-unit, python-integration, typescript, playwright, contract]
    if: always()
    steps:
      - name: Check test results
        run: |
          if [ "${{ needs.python-unit.result }}" != "success" ]; then
            echo "Python unit tests failed"
            exit 1
          fi
          if [ "${{ needs.python-integration.result }}" != "success" ]; then
            echo "Python integration tests failed"
            exit 1
          fi
          if [ "${{ needs.typescript.result }}" != "success" ]; then
            echo "TypeScript tests failed"
            exit 1
          fi
          if [ "${{ needs.playwright.result }}" != "success" ]; then
            echo "Playwright tests failed"
            exit 1
          fi
          if [ "${{ needs.contract.result }}" != "success" ]; then
            echo "Contract tests failed"
            exit 1
          fi
```

---

### 5.2 Wait for Services Script

```bash
#!/bin/bash
# scripts/wait-for-services.sh

set -e

echo "Waiting for PostgreSQL..."
timeout=30
while ! docker-compose -f docker-compose.test.yml exec -T postgres pg_isready -U testuser > /dev/null 2>&1; do
  timeout=$((timeout - 1))
  if [ $timeout -le 0 ]; then
    echo "PostgreSQL failed to start"
    exit 1
  fi
  sleep 1
done
echo "PostgreSQL ready"

echo "Waiting for Kafka..."
timeout=60
while ! docker-compose -f docker-compose.test.yml exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; do
  timeout=$((timeout - 1))
  if [ $timeout -le 0 ]; then
    echo "Kafka failed to start"
    exit 1
  fi
  sleep 2
done
echo "Kafka ready"

echo "Waiting for backend services..."
timeout=30
while ! curl -s http://localhost:3000/health > /dev/null 2>&1 || ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
  timeout=$((timeout - 1))
  if [ $timeout -le 0 ]; then
    echo "Backend services failed to start"
    exit 1
  fi
  sleep 1
done
echo "All services ready"
```

---

## 6. Test Data Factories

### 6.1 factory_boy (Python)

```python
# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from factory import Faker, SubFactory, LazyAttribute
from src.models import User, VerificationRequest, VerificationResult
from src.database import db_session

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db_session
        sqlalchemy_session_persistence = 'commit'

    id = factory.Sequence(lambda n: f'user-{n}')
    email = Faker('email')
    name = Faker('name')
    created_at = Faker('date_time_this_year')
    is_active = True


class VerificationRequestFactory(SQLAlchemyModelFactory):
    class Meta:
        model = VerificationRequest
        sqlalchemy_session = db_session

    id = factory.Sequence(lambda n: f'req-{n}')
    user = SubFactory(UserFactory)
    query_text = Faker('sentence')
    formalization = LazyAttribute(lambda obj: f'∃x. P({obj.query_text})')
    status = 'pending'
    created_at = Faker('date_time_this_month')


class VerificationResultFactory(SQLAlchemyModelFactory):
    class Meta:
        model = VerificationResult
        sqlalchemy_session = db_session

    id = factory.Sequence(lambda n: f'result-{n}')
    request = SubFactory(VerificationRequestFactory)
    verdict = factory.Iterator(['SAT', 'UNSAT', 'UNKNOWN'])
    confidence = Faker('pyfloat', left_digits=0, right_digits=2, positive=True, max_value=1.0)
    proof = factory.LazyFunction(lambda: {'model': {'x': 5}})
    metadata = factory.LazyFunction(lambda: {'solver': 'z3', 'time_ms': 42})
    created_at = Faker('date_time_this_week')


# Specialized factories
class SATResultFactory(VerificationResultFactory):
    verdict = 'SAT'
    confidence = Faker('pyfloat', min_value=0.8, max_value=1.0, right_digits=2)
    proof = factory.LazyFunction(lambda: {
        'model': {'x': 3, 'y': 7},
        'explanation': 'Model satisfies all constraints'
    })


class UNSATResultFactory(VerificationResultFactory):
    verdict = 'UNSAT'
    confidence = Faker('pyfloat', min_value=0.9, max_value=1.0, right_digits=2)
    proof = factory.LazyFunction(lambda: {
        'unsat_core': ['constraint1', 'constraint2'],
        'explanation': 'Constraints are contradictory'
    })


class UNKNOWNResultFactory(VerificationResultFactory):
    verdict = 'UNKNOWN'
    confidence = Faker('pyfloat', min_value=0.0, max_value=0.5, right_digits=2)
    proof = {}
    metadata = factory.LazyFunction(lambda: {
        'solver': 'z3',
        'reason': 'timeout',
        'time_ms': 30000
    })
```

```python
# tests/test_with_factories.py
import pytest
from tests.factories import (
    UserFactory,
    VerificationRequestFactory,
    SATResultFactory,
    UNSATResultFactory
)

def test_create_user_with_factory():
    """Test user creation with factory."""
    user = UserFactory()

    assert user.id.startswith('user-')
    assert '@' in user.email
    assert user.is_active is True


def test_create_verification_request():
    """Test verification request with related user."""
    request = VerificationRequestFactory()

    assert request.user is not None
    assert request.user.email is not None
    assert request.status == 'pending'
    assert '∃x.' in request.formalization


def test_create_sat_result():
    """Test SAT result creation."""
    result = SATResultFactory()

    assert result.verdict == 'SAT'
    assert result.confidence >= 0.8
    assert 'model' in result.proof
    assert result.request is not None


def test_create_multiple_results_for_same_request():
    """Test creating multiple results for same request."""
    request = VerificationRequestFactory()

    results = [
        SATResultFactory(request=request),
        UNSATResultFactory(request=request)
    ]

    assert len(results) == 2
    assert all(r.request.id == request.id for r in results)


def test_custom_user_attributes():
    """Test overriding factory attributes."""
    user = UserFactory(
        email='custom@example.com',
        name='Custom Name'
    )

    assert user.email == 'custom@example.com'
    assert user.name == 'Custom Name'


def test_batch_creation():
    """Test creating multiple instances."""
    users = UserFactory.create_batch(10)

    assert len(users) == 10
    assert len(set(u.id for u in users)) == 10  # All unique IDs
```

---

### 6.2 pytest-factoryboy Integration

```python
# tests/conftest.py
import pytest
from pytest_factoryboy import register
from tests.factories import (
    UserFactory,
    VerificationRequestFactory,
    SATResultFactory,
    UNSATResultFactory
)

# Register factories as fixtures
register(UserFactory)
register(VerificationRequestFactory)
register(SATResultFactory, 'sat_result')
register(UNSATResultFactory, 'unsat_result')

# Now you can use 'user', 'verification_request', 'sat_result', 'unsat_result' as fixtures
```

```python
# tests/test_with_factoryboy_fixtures.py
def test_user_fixture(user):
    """Test using auto-generated user fixture."""
    assert user.id is not None
    assert user.email is not None


def test_verification_request_fixture(verification_request):
    """Test using auto-generated verification_request fixture."""
    assert verification_request.user is not None
    assert verification_request.query_text is not None


def test_sat_result_fixture(sat_result):
    """Test using custom-named SAT result fixture."""
    assert sat_result.verdict == 'SAT'
    assert sat_result.confidence >= 0.8


def test_with_custom_user(user_factory):
    """Test using factory function fixture."""
    custom_user = user_factory(email='test@example.com')
    assert custom_user.email == 'test@example.com'
```

---

### 6.3 fishery (TypeScript)

```typescript
// tests/factories/user.factory.ts
import { Factory } from 'fishery'
import { faker } from '@faker-js/faker'
import { User } from '@/types/user'

export const userFactory = Factory.define<User>(({ sequence }) => ({
  id: `user-${sequence}`,
  email: faker.internet.email(),
  name: faker.person.fullName(),
  createdAt: faker.date.recent(),
  isActive: true
}))

// tests/factories/verification.factory.ts
import { Factory } from 'fishery'
import { faker } from '@faker-js/faker'
import { VerificationRequest, VerificationResult } from '@/types/verification'
import { userFactory } from './user.factory'

export const verificationRequestFactory = Factory.define<VerificationRequest>(
  ({ sequence, associations }) => ({
    id: `req-${sequence}`,
    userId: associations.user?.id || userFactory.build().id,
    queryText: faker.lorem.sentence(),
    formalization: `∃x. P(${faker.lorem.word()})`,
    status: 'pending',
    createdAt: faker.date.recent()
  })
)

export const verificationResultFactory = Factory.define<VerificationResult>(
  ({ sequence, associations, params }) => {
    const verdict = params.verdict || faker.helpers.arrayElement(['SAT', 'UNSAT', 'UNKNOWN'])

    return {
      id: `result-${sequence}`,
      requestId: associations.request?.id || verificationRequestFactory.build().id,
      verdict,
      confidence: verdict === 'SAT' || verdict === 'UNSAT'
        ? faker.number.float({ min: 0.8, max: 1.0, precision: 0.01 })
        : faker.number.float({ min: 0.0, max: 0.5, precision: 0.01 }),
      proof: verdict === 'SAT'
        ? { model: { x: faker.number.int({ min: 1, max: 10 }) } }
        : verdict === 'UNSAT'
        ? { unsatCore: ['constraint1', 'constraint2'] }
        : {},
      metadata: {
        solver: 'z3',
        timeMs: faker.number.int({ min: 10, max: 1000 }),
        ...(verdict === 'UNKNOWN' && { reason: 'timeout' })
      },
      createdAt: faker.date.recent()
    }
  }
)

// Specialized factories using extension
export const satResultFactory = verificationResultFactory.params({ verdict: 'SAT' })
export const unsatResultFactory = verificationResultFactory.params({ verdict: 'UNSAT' })
export const unknownResultFactory = verificationResultFactory.params({ verdict: 'UNKNOWN' })
```

```typescript
// tests/services/verification.test.ts
import { userFactory, verificationRequestFactory, satResultFactory } from '../factories'

describe('VerificationService', () => {
  it('should create verification request', () => {
    const user = userFactory.build()
    const request = verificationRequestFactory.build({ userId: user.id })

    expect(request.userId).toBe(user.id)
    expect(request.status).toBe('pending')
  })

  it('should create SAT result', () => {
    const result = satResultFactory.build()

    expect(result.verdict).toBe('SAT')
    expect(result.confidence).toBeGreaterThanOrEqual(0.8)
    expect(result.proof.model).toBeDefined()
  })

  it('should create multiple results', () => {
    const request = verificationRequestFactory.build()
    const results = satResultFactory.buildList(5, { requestId: request.id })

    expect(results).toHaveLength(5)
    expect(results.every(r => r.requestId === request.id)).toBe(true)
  })

  it('should override factory attributes', () => {
    const result = satResultFactory.build({
      confidence: 0.99,
      metadata: { solver: 'cvc5', timeMs: 50 }
    })

    expect(result.confidence).toBe(0.99)
    expect(result.metadata.solver).toBe('cvc5')
  })
})
```

---

## 7. Contract Testing

### 7.1 Pact Consumer Tests (TypeScript/NodeJS)

```typescript
// tests/contract/python-backend.pact.test.ts
import { PactV3, MatchersV3 } from '@pact-foundation/pact'
import { VerificationClient } from '@/clients/verification'

const { like, uuid } = MatchersV3

const provider = new PactV3({
  consumer: 'NodeJS Backend',
  provider: 'Python FastAPI Backend',
  logLevel: 'info',
  dir: './pacts'
})

describe('Python Backend API Contract', () => {
  it('should submit verification request', async () => {
    await provider
      .given('user exists and has verification enabled')
      .uponReceiving('a verification request')
      .withRequest({
        method: 'POST',
        path: '/api/v1/verify',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': like('Bearer token123')
        },
        body: {
          query: like('The sum of 3 and 7 is 10'),
          user_id: like('user-123'),
          verification_enabled: true
        }
      })
      .willRespondWith({
        status: 202,
        headers: {
          'Content-Type': 'application/json'
        },
        body: {
          task_id: uuid('task-abc123'),
          status: 'queued'
        }
      })
      .executeTest(async (mockServer) => {
        const client = new VerificationClient(mockServer.url)
        const result = await client.submitVerification({
          query: 'The sum of 3 and 7 is 10',
          userId: 'user-123',
          verificationEnabled: true
        })

        expect(result.taskId).toBeDefined()
        expect(result.status).toBe('queued')
      })
  })

  it('should retrieve verification result', async () => {
    await provider
      .given('verification task is completed with SAT result')
      .uponReceiving('a request for verification result')
      .withRequest({
        method: 'GET',
        path: '/api/v1/verify/task-abc123',
        headers: {
          'Authorization': like('Bearer token123')
        }
      })
      .willRespondWith({
        status: 200,
        headers: {
          'Content-Type': 'application/json'
        },
        body: {
          task_id: 'task-abc123',
          status: 'completed',
          result: {
            verdict: like('SAT'),
            confidence: like(0.95),
            proof: like({ model: { x: 3, y: 7 } }),
            metadata: like({ solver: 'z3', time_ms: 42 })
          }
        }
      })
      .executeTest(async (mockServer) => {
        const client = new VerificationClient(mockServer.url)
        const result = await client.getVerificationResult('task-abc123')

        expect(result.status).toBe('completed')
        expect(result.result.verdict).toBe('SAT')
        expect(result.result.confidence).toBeGreaterThan(0)
      })
  })

  it('should handle error when verification fails', async () => {
    await provider
      .given('verification task failed')
      .uponReceiving('a request for failed verification')
      .withRequest({
        method: 'GET',
        path: '/api/v1/verify/task-failed',
        headers: {
          'Authorization': like('Bearer token123')
        }
      })
      .willRespondWith({
        status: 200,
        headers: {
          'Content-Type': 'application/json'
        },
        body: {
          task_id: 'task-failed',
          status: 'failed',
          error: like('Invalid formalization')
        }
      })
      .executeTest(async (mockServer) => {
        const client = new VerificationClient(mockServer.url)
        const result = await client.getVerificationResult('task-failed')

        expect(result.status).toBe('failed')
        expect(result.error).toBeDefined()
      })
  })
})
```

---

### 7.2 Pact Provider Verification (Python)

```python
# tests/contract/test_provider.py
import pytest
from pact import Verifier
from src.app import create_app
import threading
import time

@pytest.fixture(scope='module')
def provider_app():
    """Start FastAPI app for provider verification."""
    app = create_app()

    # Run app in background thread
    import uvicorn
    config = uvicorn.Config(app, host='127.0.0.1', port=8000, log_level='error')
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for server to start
    time.sleep(2)

    yield

    # Cleanup
    server.should_exit = True


def test_verify_contracts(provider_app):
    """Verify provider implements all consumer contracts."""
    verifier = Verifier(
        provider='Python FastAPI Backend',
        provider_base_url='http://localhost:8000'
    )

    # Configure provider states
    provider_states = {
        'user exists and has verification enabled': setup_user_with_verification,
        'verification task is completed with SAT result': setup_completed_task_sat,
        'verification task failed': setup_failed_task
    }

    success, logs = verifier.verify_pacts(
        './pacts/nodejs_backend-python_fastapi_backend.json',
        provider_states_setup_url='http://localhost:8000/_pact/provider_states',
        enable_pending=False,
        publish_version='1.0.0',
        publish_verification_results=True
    )

    assert success, f"Pact verification failed:\n{logs}"


# Provider state setup functions
def setup_user_with_verification(state):
    """Set up state: user exists and has verification enabled."""
    from src.database import db_session
    from src.models import User

    user = User(
        id='user-123',
        email='test@example.com',
        verification_enabled=True
    )
    db_session.add(user)
    db_session.commit()

    return {'user_id': 'user-123'}


def setup_completed_task_sat(state):
    """Set up state: verification task completed with SAT result."""
    from src.database import db_session
    from src.models import VerificationTask

    task = VerificationTask(
        id='task-abc123',
        status='completed',
        result={
            'verdict': 'SAT',
            'confidence': 0.95,
            'proof': {'model': {'x': 3, 'y': 7}},
            'metadata': {'solver': 'z3', 'time_ms': 42}
        }
    )
    db_session.add(task)
    db_session.commit()

    return {'task_id': 'task-abc123'}


def setup_failed_task(state):
    """Set up state: verification task failed."""
    from src.database import db_session
    from src.models import VerificationTask

    task = VerificationTask(
        id='task-failed',
        status='failed',
        error='Invalid formalization'
    )
    db_session.add(task)
    db_session.commit()

    return {'task_id': 'task-failed'}
```

---

## 8. SMT Verification Testing

### 8.1 SAT/UNSAT/UNKNOWN Result Validation

```python
# tests/unit/test_smt_validation.py
import pytest
from src.smt.validator import SMTValidator
from z3 import *

def test_validate_sat_result_with_model():
    """Test that SAT model actually satisfies formula."""
    validator = SMTValidator()

    # Formula: x + y = 10 ∧ x = 3
    formula = And(
        IntVal(x) + IntVal(y) == 10,
        IntVal(x) == 3
    )

    # Model from solver
    model = {'x': 3, 'y': 7}

    # Validate model satisfies formula
    is_valid = validator.validate_sat_model(formula, model)
    assert is_valid is True


def test_validate_sat_result_with_invalid_model():
    """Test detection of invalid SAT model."""
    validator = SMTValidator()

    formula = And(
        IntVal(x) + IntVal(y) == 10,
        IntVal(x) == 3
    )

    # Invalid model
    model = {'x': 3, 'y': 8}  # 3 + 8 ≠ 10

    is_valid = validator.validate_sat_model(formula, model)
    assert is_valid is False


def test_validate_unsat_proof():
    """Test UNSAT proof validation."""
    validator = SMTValidator()

    # Unsatisfiable formula: x = 5 ∧ x = 3
    formula = And(
        IntVal(x) == 5,
        IntVal(x) == 3
    )

    # Get proof from Z3
    solver = Solver()
    solver.add(formula)
    result = solver.check()

    assert result == unsat

    # Verify proof (simplified - actual proof validation is complex)
    unsat_core = solver.unsat_core()
    assert len(unsat_core) > 0


def test_cross_validate_with_multiple_solvers():
    """Test result consistency across SMT solvers."""
    formula_text = "(declare-const x Int) (declare-const y Int) (assert (= (+ x y) 10)) (assert (= x 3))"

    # Test with Z3
    z3_result = validate_with_z3(formula_text)
    assert z3_result['verdict'] == 'SAT'

    # Test with cvc5
    cvc5_result = validate_with_cvc5(formula_text)
    assert cvc5_result['verdict'] == 'SAT'

    # Results should match
    assert z3_result['verdict'] == cvc5_result['verdict']


def test_formalization_similarity_scoring():
    """Test formalization similarity calculation."""
    from src.smt.similarity import calculate_formalization_similarity

    text = "The sum of 3 and 7 is 10"
    formalization = "∃x,y. x = 3 ∧ y = 7 ∧ x + y = 10"

    similarity = calculate_formalization_similarity(text, formalization)

    assert 0.0 <= similarity <= 1.0
    assert similarity > 0.8  # Should be highly similar


def test_confidence_calculation():
    """Test confidence score calculation."""
    from src.smt.confidence import calculate_confidence

    # SAT with quick solve time
    confidence_sat = calculate_confidence(
        verdict='SAT',
        solve_time_ms=50,
        formalization_similarity=0.95
    )
    assert confidence_sat > 0.9

    # UNKNOWN due to timeout
    confidence_unknown = calculate_confidence(
        verdict='UNKNOWN',
        solve_time_ms=30000,
        formalization_similarity=0.85
    )
    assert confidence_unknown < 0.5
```

---

### 8.2 Hupyy Response Transformation Testing

```python
# tests/unit/test_hupyy_transformer.py
import pytest
from src.hupyy.transformer import HupyyResponseTransformer

def test_transform_sat_response():
    """Test transformation of Hupyy SAT response to internal format."""
    transformer = HupyyResponseTransformer()

    hupyy_response = {
        'check_sat_result': 'SAT',
        'formalization_similarity': 0.92,
        'proof': {
            'model': {'x': 3, 'y': 7},
            'explanation': 'Values satisfy all constraints'
        },
        'metadata': {
            'solver': 'z3',
            'time_ms': 42,
            'version': '4.12.0'
        }
    }

    internal_format = transformer.transform(hupyy_response)

    assert internal_format['verdict'] == 'SAT'
    assert internal_format['confidence'] >= 0.9
    assert 'model' in internal_format['proof']
    assert internal_format['metadata']['solver'] == 'z3'


def test_transform_unsat_response():
    """Test transformation of Hupyy UNSAT response."""
    transformer = HupyyResponseTransformer()

    hupyy_response = {
        'check_sat_result': 'UNSAT',
        'formalization_similarity': 0.88,
        'proof': {
            'unsat_core': ['constraint_1', 'constraint_2'],
            'explanation': 'Constraints are contradictory'
        },
        'metadata': {
            'solver': 'z3',
            'time_ms': 120
        }
    }

    internal_format = transformer.transform(hupyy_response)

    assert internal_format['verdict'] == 'UNSAT'
    assert internal_format['confidence'] >= 0.85
    assert 'unsat_core' in internal_format['proof']


def test_transform_unknown_response():
    """Test transformation of Hupyy UNKNOWN response."""
    transformer = HupyyResponseTransformer()

    hupyy_response = {
        'check_sat_result': 'UNKNOWN',
        'formalization_similarity': 0.75,
        'proof': {},
        'metadata': {
            'solver': 'z3',
            'time_ms': 30000,
            'reason': 'timeout'
        }
    }

    internal_format = transformer.transform(hupyy_response)

    assert internal_format['verdict'] == 'UNKNOWN'
    assert internal_format['confidence'] < 0.5
    assert internal_format['metadata']['reason'] == 'timeout'


def test_handle_malformed_response():
    """Test error handling for malformed Hupyy response."""
    transformer = HupyyResponseTransformer()

    malformed_response = {
        'check_sat_result': 'INVALID',  # Invalid verdict
        'formalization_similarity': 1.5,  # Out of range
    }

    with pytest.raises(ValueError) as exc_info:
        transformer.transform(malformed_response)

    assert 'Invalid' in str(exc_info.value)
```

---

### 8.3 Property-Based Testing with Hypothesis

```python
# tests/property/test_smt_properties.py
import pytest
from hypothesis import given, strategies as st
from src.smt.validator import SMTValidator

@given(
    x=st.integers(min_value=-1000, max_value=1000),
    y=st.integers(min_value=-1000, max_value=1000)
)
def test_addition_is_commutative(x, y):
    """Property: x + y = y + x (commutativity)."""
    validator = SMTValidator()

    formula = validator.parse_formula(f"x + y = {x + y} ∧ y + x = {y + x}")
    result = validator.check_sat(formula)

    assert result['verdict'] == 'SAT'


@given(
    constraint1=st.text(min_size=1, max_size=50),
    constraint2=st.text(min_size=1, max_size=50)
)
def test_consistency_of_confidence_scores(constraint1, constraint2):
    """Property: Confidence should be consistent across similar inputs."""
    from src.smt.confidence import calculate_confidence

    score1 = calculate_confidence('SAT', 100, 0.9)
    score2 = calculate_confidence('SAT', 100, 0.9)

    # Same inputs should produce same confidence
    assert score1 == score2


@given(
    text=st.text(min_size=10, max_size=100),
    formalization=st.text(min_size=5, max_size=50)
)
def test_similarity_bounds(text, formalization):
    """Property: Similarity score should be in [0, 1]."""
    from src.smt.similarity import calculate_formalization_similarity

    similarity = calculate_formalization_similarity(text, formalization)

    assert 0.0 <= similarity <= 1.0
```

---

## Conclusion

This examples document provides practical, production-ready code for all major testing patterns in the Hupyy SMT verification integration:

1. **External API Testing**: VCR pattern, responses library, MSW for comprehensive Hupyy API mocking
2. **Kafka Testing**: Unit tests with mocks, integration tests with Testcontainers, idempotency validation
3. **Playwright UI Testing**: Page Object Model, E2E flows, visual regression, accessibility
4. **Integration Tests**: Docker Compose setup, multi-service orchestration, health checks
5. **CI/CD**: GitHub Actions workflows with parallelization, coverage reporting, quality gates
6. **Test Data**: factory_boy (Python) and fishery (TypeScript) for maintainable test data
7. **Contract Testing**: Pact consumer and provider tests for API compatibility
8. **SMT Validation**: SAT/UNSAT/UNKNOWN result validation, proof verification, property-based testing

All examples follow 2025 best practices and are ready for implementation in the project. Copy and adapt these patterns to build a comprehensive, maintainable test suite.
