# Integration Test Specifications for Hupyy SMT Verification

**Date:** November 30, 2025
**Project:** PipesHub AI - Hupyy SMT Verification Integration

---

## Executive Summary

Integration tests validate **service interactions** and **cross-boundary communication**. These tests use **real dependencies** (Testcontainers for Kafka/DB, VCR for external APIs) to ensure the system works as a whole.

**Test Distribution:** 20-30 tests (20% of total suite)
**Execution Time:** <5 minutes
**Coverage Target:** ≥70%

---

## 1. Kafka Message Flow Tests

**File:** `backend/python/tests/integration/test_kafka_flow.py`
**Test Count:** 10 tests

### Test 1: test_publish_verification_request_to_kafka
```python
@pytest.mark.integration
async def test_publish_verification_request_to_kafka(kafka_container, kafka_producer):
    """Test publishing verification request to verify_chunks topic."""
    message = {
        "request_id": "req_123",
        "content": "Test content",
        "nl_query": "Find admins",
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    await kafka_producer.send("verify_chunks", value=message)
    await kafka_producer.flush()
    
    # Verify message in topic
    consumer = AIOKafkaConsumer(
        "verify_chunks",
        bootstrap_servers=kafka_container.get_bootstrap_server(),
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    )
    await consumer.start()
    
    msg = await asyncio.wait_for(consumer.getone(), timeout=5.0)
    assert msg.value["request_id"] == "req_123"
    
    await consumer.stop()
```

### Test 2: test_consume_verify_publish_result
```python
@pytest.mark.integration
async def test_consume_verify_publish_result(
    kafka_container, orchestrator, mock_hupyy_client
):
    """Test full flow: consume request → verify → publish result."""
    # Publish request
    producer = AIOKafkaProducer(
        bootstrap_servers=kafka_container.get_bootstrap_server(),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    )
    await producer.start()
    
    request_msg = {
        "request_id": "req_456",
        "content": "2 + 2 = 4",
        "nl_query": "Is 2+2=4?",
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    await producer.send("verify_chunks", value=request_msg)
    await producer.flush()
    
    # Mock Hupyy response
    mock_hupyy_client.verify_parallel.return_value = [
        VerificationResult(
            request_id="req_456",
            chunk_index=0,
            verdict=VerificationVerdict.SAT,
            confidence=0.95,
            duration_seconds=60.0,
            cached=False,
        )
    ]
    
    # Process messages
    await orchestrator.process_batch([request_msg])
    
    # Verify result published
    consumer = AIOKafkaConsumer(
        "verification_complete",
        bootstrap_servers=kafka_container.get_bootstrap_server(),
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    )
    await consumer.start()
    
    result_msg = await asyncio.wait_for(consumer.getone(), timeout=5.0)
    assert result_msg.value["request_id"] == "req_456"
    assert result_msg.value["verdict"] == "SAT"
    
    await consumer.stop()
    await producer.stop()
```

### Additional Tests (8 more):
- test_kafka_message_serialization_deserialization
- test_kafka_consumer_offset_management
- test_kafka_idempotent_producer
- test_kafka_partition_assignment
- test_kafka_consumer_group_coordination
- test_kafka_failed_message_to_dlq
- test_kafka_batch_consumption
- test_kafka_producer_retry_on_failure

---

## 2. External API Integration Tests (Hupyy)

**File:** `backend/python/tests/integration/test_hupyy_external.py`
**Test Count:** 7 tests

### Test 3: test_hupyy_api_sat_response (VCR)
```python
@pytest.mark.integration
@pytest.mark.vcr(cassette_library_dir='tests/fixtures/cassettes')
async def test_hupyy_api_sat_response():
    """Test Hupyy API with SAT response (VCR recorded)."""
    client = HupyyClient(api_url="https://verticalslice-smt-service-gvav8.ondigitalocean.app")
    
    request = VerificationRequest(
        request_id="req_vcr_sat",
        content="All prime numbers greater than 2 are odd",
        nl_query="Verify prime statement",
    )
    
    result = await client.verify(request)
    
    assert result.verdict == VerificationVerdict.SAT
    assert result.confidence > 0.8
    assert result.formalization_similarity is not None
    
    await client.close()
```

### Test 4: test_hupyy_api_unsat_response (VCR)
```python
@pytest.mark.integration
@pytest.mark.vcr(cassette_library_dir='tests/fixtures/cassettes')
async def test_hupyy_api_unsat_response():
    """Test Hupyy API with UNSAT response (VCR recorded)."""
    client = HupyyClient(api_url="https://verticalslice-smt-service-gvav8.ondigitalocean.app")
    
    request = VerificationRequest(
        request_id="req_vcr_unsat",
        content="2 + 2 = 5",
        nl_query="Is 2+2=5?",
    )
    
    result = await client.verify(request)
    
    assert result.verdict == VerificationVerdict.UNSAT
    
    await client.close()
```

### Additional Tests (5 more):
- test_hupyy_api_timeout_handling
- test_hupyy_api_http_error_codes
- test_hupyy_api_malformed_response
- test_hupyy_api_network_failure
- test_hupyy_api_retry_logic

---

## 3. NodeJS → Python API Integration Tests

**File:** `backend/nodejs/tests/integration/test_api_integration.spec.ts`
**Test Count:** 8 tests

### Test 5: test_nodejs_forwards_to_python
```typescript
describe('NodeJS → Python Integration', () => {
  test('should forward verification request to Python API', async () => {
    const axios = require('axios')
    
    const payload = {
      query: 'Find all admin users',
      verification_enabled: true,
    }
    
    const response = await axios.post(
      'http://localhost:3000/api/search',
      payload
    )
    
    expect(response.status).toBe(200)
    expect(response.data).toHaveProperty('results')
    expect(response.data).toHaveProperty('verification_results')
  })
})
```

### Additional Tests (7 more):
- test_nodejs_python_error_propagation
- test_nodejs_python_timeout_handling
- test_nodejs_python_payload_validation
- test_python_returns_verification_results
- test_nodejs_handles_missing_python_service
- test_end_to_end_search_with_verification
- test_verification_disabled_skips_processing

---

## 4. Database Integration Tests

**File:** `backend/python/tests/integration/test_database.py`
**Test Count:** 5 tests

### Test 6: test_store_verification_result_in_mongodb
```python
@pytest.mark.integration
async def test_store_verification_result_in_mongodb(mongo_container):
    """Test storing verification result in MongoDB."""
    from motor.motor_asyncio import AsyncIOMotorClient
    
    client = AsyncIOMotorClient(mongo_container.get_connection_url())
    db = client['test_db']
    collection = db['verification_results']
    
    result = {
        "request_id": "req_123",
        "verdict": "SAT",
        "confidence": 0.95,
        "timestamp": datetime.utcnow(),
    }
    
    await collection.insert_one(result)
    
    # Verify stored
    stored = await collection.find_one({"request_id": "req_123"})
    assert stored is not None
    assert stored["verdict"] == "SAT"
```

### Additional Tests (4 more):
- test_cache_verification_in_redis
- test_retrieve_cached_verification
- test_database_transaction_rollback
- test_concurrent_database_writes

---

## 5. Contract Tests (Pact)

**File:** `tests/contract/nodejs-python/test_verification_api_contract.py`
**Test Count:** 5 tests (Provider side)

### Test 7: test_python_satisfies_nodejs_contract
```python
@pytest.mark.contract
def test_python_satisfies_nodejs_contract():
    """Test Python FastAPI satisfies NodeJS contract."""
    from pact import Verifier
    
    verifier = Verifier(
        provider='Python Verification API',
        provider_base_url='http://localhost:8000',
    )
    
    verifier.verify_pacts(
        './pacts/nodejs-python-verification.json',
        provider_states_setup_url='http://localhost:8000/pact/setup',
    )
```

**File:** `tests/contract/nodejs-python/verification-api.pact.ts`
**Test Count:** 5 tests (Consumer side)

### Test 8: test_nodejs_defines_contract_for_python
```typescript
import { PactV3, MatchersV3 } from '@pact-foundation/pact'

describe('NodeJS → Python Contract', () => {
  const provider = new PactV3({
    consumer: 'NodeJS API',
    provider: 'Python Verification API',
  })
  
  test('should receive verification results for SAT query', () => {
    return provider
      .given('verification enabled and query is satisfiable')
      .uponReceiving('a search request with verification')
      .withRequest({
        method: 'POST',
        path: '/api/verify',
        headers: { 'Content-Type': 'application/json' },
        body: {
          query: MatchersV3.like('Find admins'),
          verification_enabled: true,
        },
      })
      .willRespondWith({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: {
          results: MatchersV3.eachLike({ id: '1', content: 'Result' }),
          verification_results: MatchersV3.eachLike({
            verdict: 'SAT',
            confidence: MatchersV3.decimal(0.95),
          }),
        },
      })
      .executeTest(async (mockServer) => {
        const axios = require('axios')
        const response = await axios.post(`${mockServer.url}/api/verify`, {
          query: 'Find admins',
          verification_enabled: true,
        })
        
        expect(response.status).toBe(200)
        expect(response.data.verification_results).toBeDefined()
      })
  })
})
```

---

## Test Fixtures and Setup

### Testcontainers Setup

```python
# conftest.py
import pytest
from testcontainers.kafka import KafkaContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session")
def kafka_container():
    """Start Kafka container for integration tests."""
    with KafkaContainer(image="confluentinc/cp-kafka:7.9.0") as kafka:
        yield kafka

@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container."""
    with PostgresContainer("postgres:15") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def mongo_container():
    """Start MongoDB container."""
    with MongoDbContainer("mongo:7") as mongo:
        yield mongo

@pytest.fixture(scope="session")
def redis_container():
    """Start Redis container."""
    with RedisContainer("redis:7") as redis:
        yield redis
```

---

## Execution Strategy

### Local Development
```bash
# Run integration tests only
pytest tests/integration/ -v -m integration

# Run with Testcontainers
docker ps  # Verify Docker running
pytest tests/integration/ -v

# Run contract tests
pytest tests/contract/ -v -m contract
npm run test:contract
```

### CI/CD
```yaml
# GitHub Actions
jobs:
  integration-tests:
    runs-on: ubuntu-latest
    services:
      docker:
        image: docker:dind
    steps:
      - name: Run integration tests
        run: pytest tests/integration/ -v
      - name: Verify contracts
        run: |
          npm run test:contract
          pytest tests/contract/ -v
```

---

## Summary

| Test Suite | Test Count | Duration | Dependencies |
|-----------|-----------|----------|--------------|
| Kafka Flow | 10 | ~2 min | Testcontainers Kafka |
| Hupyy External API | 7 | ~1 min | VCR cassettes |
| NodeJS → Python | 8 | ~1 min | Both services running |
| Database | 5 | ~30s | Testcontainers DB |
| Contract Tests | 10 | ~30s | Pact |
| **Total** | **40** | **~5 min** | **Docker** |

These integration tests ensure that all service boundaries work correctly with real (or realistic) dependencies.
