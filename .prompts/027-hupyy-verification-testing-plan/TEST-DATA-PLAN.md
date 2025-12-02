# Test Data Management Plan for Hupyy SMT Verification

**Date:** November 30, 2025
**Purpose:** Comprehensive test data strategy with factories, fixtures, and mock data

---

## 1. Factory Pattern Implementation

### Python Factories (factory_boy)

#### `tests/fixtures/factories.py`
```python
import factory
from factory import Faker, SubFactory
from app.verification.models import (
    VerificationRequest,
    VerificationResult,
    HupyyRequest,
    HupyyResponse,
    VerificationVerdict,
)

class VerificationRequestFactory(factory.Factory):
    class Meta:
        model = VerificationRequest
    
    request_id = Faker('uuid4')
    content = Faker('sentence', nb_words=10)
    chunk_index = 0
    total_chunks = 1
    nl_query = Faker('sentence', nb_words=6)
    source_document_id = Faker('uuid4')

class HupyyResponseFactory(factory.Factory):
    class Meta:
        model = HupyyResponse
    
    verdict = VerificationVerdict.SAT
    confidence = Faker('pyfloat', min_value=0.7, max_value=1.0)
    formalization_similarity = Faker('pyfloat', min_value=0.6, max_value=1.0)
    explanation = Faker('sentence')
    metadata = factory.LazyFunction(lambda: {
        "solver": "z3",
        "model_size": 42,
    })
    duration_ms = Faker('pyint', min_value=500, max_value=5000)

class VerificationResultFactory(factory.Factory):
    class Meta:
        model = VerificationResult
    
    request_id = Faker('uuid4')
    chunk_index = 0
    verdict = VerificationVerdict.SAT
    confidence = Faker('pyfloat', min_value=0.8, max_value=1.0)
    duration_seconds = Faker('pyfloat', min_value=30.0, max_value=120.0)
    cached = False
```

#### Usage in Tests
```python
def test_verification_with_factory():
    """Test using factory-generated data."""
    request = VerificationRequestFactory.create()
    result = VerificationResultFactory.create(request_id=request.request_id)
    
    assert result.request_id == request.request_id
```

---

### TypeScript Factories (Fishery)

#### `tests/shared/factories.ts`
```typescript
import { Factory } from 'fishery'

interface User {
  id: string
  email: string
  name: string
}

interface VerificationResult {
  request_id: string
  verdict: 'SAT' | 'UNSAT' | 'UNKNOWN'
  confidence: number
}

export const userFactory = Factory.define<User>(({ sequence }) => ({
  id: `user-${sequence}`,
  email: `user${sequence}@example.com`,
  name: `Test User ${sequence}`,
}))

export const verificationResultFactory = Factory.define<VerificationResult>(({ sequence }) => ({
  request_id: `req-${sequence}`,
  verdict: 'SAT',
  confidence: 0.95,
}))
```

#### Usage
```typescript
test('should display verification results', () => {
  const user = userFactory.build()
  const results = verificationResultFactory.buildList(3)
  
  expect(results).toHaveLength(3)
})
```

---

## 2. pytest Fixtures

### `tests/conftest.py`
```python
import pytest
from unittest.mock import AsyncMock, Mock
from app.verification.hupyy_client import HupyyClient
from app.infrastructure.cache import VerificationCache

@pytest.fixture
def mock_hupyy_client():
    """Mock Hupyy client."""
    client = Mock(spec=HupyyClient)
    client.verify = AsyncMock()
    client.verify_parallel = AsyncMock()
    client.close = AsyncMock()
    return client

@pytest.fixture
def mock_cache():
    """Mock verification cache."""
    cache = Mock(spec=VerificationCache)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache

@pytest.fixture
def sample_verification_request():
    """Sample verification request."""
    return VerificationRequest(
        request_id="req_test_123",
        content="All prime numbers greater than 2 are odd",
        nl_query="Verify prime statement",
    )

@pytest.fixture
def sample_sat_response():
    """Sample SAT response from Hupyy."""
    return {
        "check_sat_result": "SAT",
        "formalization_similarity": 0.92,
        "model": {"x": "3", "y": "7"},
        "proof": {"summary": "Formula is satisfiable"},
        "smt_lib_code": "(assert (= (+ x y) 10))",
    }
```

---

## 3. Mock Hupyy Responses

### `tests/fixtures/mock_data/hupyy_responses.json`
```json
{
  "sat_basic": {
    "check_sat_result": "SAT",
    "formalization_similarity": 0.92,
    "model": {"x": "3", "y": "7"},
    "proof": {"summary": "Formula is satisfiable"},
    "smt_lib_code": "(assert (= (+ x y) 10))",
    "formal_text": "x + y = 10",
    "informal_text": "Sum of x and y is 10",
    "solver_success": true,
    "passed_all_checks": true,
    "metrics": {"total_time_ms": 1250}
  },
  "unsat_basic": {
    "check_sat_result": "UNSAT",
    "formalization_similarity": 0.88,
    "proof": {"summary": "No solution exists"},
    "smt_lib_code": "(assert (and (= x 1) (= x 2)))",
    "formal_text": "x = 1 AND x = 2",
    "solver_success": true,
    "metrics": {"total_time_ms": 890}
  },
  "unknown_timeout": {
    "check_sat_result": "UNKNOWN",
    "formalization_similarity": 0.45,
    "explanation": "Solver timeout after 150 seconds"
  }
}
```

---

## 4. VCR Cassettes

### `tests/fixtures/cassettes/hupyy_sat_prime.yaml`
```yaml
version: 1
interactions:
- request:
    body: '{"informal_text": "All prime numbers greater than 2 are odd", "skip_formalization": false, "enrich": false}'
    headers:
      Content-Type: [application/json]
    method: POST
    uri: https://verticalslice-smt-service-gvav8.ondigitalocean.app/pipeline/process
  response:
    body: {string: '{"check_sat_result": "SAT", "formalization_similarity": 0.92, "model": {}, "proof": {"summary": "Valid mathematical statement"}}'}
    headers:
      Content-Type: [application/json]
    status: {code: 200, message: OK}
```

### Usage
```python
@pytest.mark.vcr(cassette_library_dir='tests/fixtures/cassettes')
async def test_hupyy_with_vcr():
    """Test using VCR recorded response."""
    client = HupyyClient(api_url="https://verticalslice-smt-service-gvav8.ondigitalocean.app")
    request = VerificationRequestFactory.create(content="All prime numbers > 2 are odd")
    result = await client.verify(request)
    assert result.verdict == VerificationVerdict.SAT
```

---

## 5. Test Queries

### `tests/fixtures/mock_data/test_queries.json`
```json
{
  "satisfiable": [
    "All prime numbers greater than 2 are odd",
    "The sum of two even numbers is even",
    "Every positive integer can be expressed as a sum of powers of 2"
  ],
  "unsatisfiable": [
    "2 + 2 = 5",
    "There exists a largest prime number",
    "x = 1 AND x = 2"
  ],
  "complex": [
    "For all x, y: if x < y then there exists z such that x < z < y",
    "The halting problem is decidable"
  ]
}
```

---

## 6. Synthetic Data (Faker)

### Python
```python
from faker import Faker

fake = Faker()
fake.seed_instance(12345)  # Reproducible data

# Generate test queries
queries = [fake.sentence(nb_words=8) for _ in range(10)]

# Generate user data
users = [
    {"id": fake.uuid4(), "email": fake.email(), "name": fake.name()}
    for _ in range(5)
]
```

### TypeScript
```typescript
import { faker } from '@faker-js/faker'

faker.seed(12345)  // Reproducible

const testUser = {
  id: faker.string.uuid(),
  email: faker.internet.email(),
  name: faker.person.fullName(),
}
```

---

## 7. Database Seeding

### Development Seed Script
```python
# scripts/seed_test_data.py
from faker import Faker
from app.database import get_db
from app.models import User, VerificationResult

fake = Faker()
fake.seed_instance(12345)

async def seed_test_data():
    """Seed database with test data."""
    db = await get_db()
    
    # Create test users
    for i in range(10):
        user = User(
            id=fake.uuid4(),
            email=fake.email(),
            name=fake.name(),
        )
        await db.users.insert_one(user.dict())
    
    # Create verification results
    for i in range(50):
        result = VerificationResult(
            request_id=fake.uuid4(),
            chunk_index=0,
            verdict=fake.random_element(['SAT', 'UNSAT', 'UNKNOWN']),
            confidence=fake.pyfloat(min_value=0.5, max_value=1.0),
            duration_seconds=fake.pyfloat(min_value=30.0, max_value=120.0),
        )
        await db.verification_results.insert_one(result.dict())

if __name__ == "__main__":
    asyncio.run(seed_test_data())
```

---

## 8. Data Cleanup Strategy

### Unit Tests
- **No cleanup needed** (no persistent state)

### Integration Tests
```python
@pytest.fixture(scope="function")
async def clean_database(mongo_container):
    """Ensure clean database for each test."""
    client = AsyncIOMotorClient(mongo_container.get_connection_url())
    db = client['test_db']
    
    # Clear before test
    await db.verification_results.delete_many({})
    
    yield db
    
    # Clear after test
    await db.verification_results.delete_many({})
```

### E2E Tests
```bash
# docker-compose.test.yml
services:
  mongo:
    volumes:
      - test_mongo_data:/data/db  # Named volume

# Cleanup script
docker-compose down -v  # Remove volumes
```

---

## Summary

| Strategy | Use Case | Tools | Reproducible? |
|----------|----------|-------|---------------|
| Factories | Complex objects | factory_boy, fishery | Yes (with seed) |
| Fixtures | Reusable test data | pytest, Jest | Yes |
| Mock Data | Static responses | JSON files | Yes |
| VCR | External API | vcrpy | Yes |
| Faker | Synthetic data | Faker | Yes (with seed) |
| Seeding | Development DB | Custom scripts | Yes |

This plan ensures **maintainable, reproducible, realistic test data** across all test layers.
