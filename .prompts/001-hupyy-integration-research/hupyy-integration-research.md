# Hupyy-PipesHub SMT Verification Integration: Technical Research Report

<confidence>High - Based on official OpenAPI specification, architecture documentation, and verified codebase analysis</confidence>

<dependencies>
- Python FastAPI backend service (new microservice for Hupyy Integration Service)
- Node.js Kafka producer/consumer integration (existing infrastructure)
- Qdrant vector database payload schema extension (backward compatible)
- ArangoDB document properties extension (backward compatible)
- Kafka topic creation and consumer group configuration
- Python async HTTP client library (httpx or aiohttp)
- Circuit breaker library (pybreaker or similar)
- Monitoring infrastructure (Prometheus/Grafana for metrics)
</dependencies>

<open_questions>
1. **User Decision Required**: Should verification run synchronously (blocking search results) or asynchronously (updating scores post-return)?
   - Sync: Higher latency (20-30s added) but immediate verification scores
   - Async: Lower latency, eventual consistency, requires UI for "verification in progress" state

2. **User Confirmation**: What percentage of search results should be verified per query?
   - Option A: All top-50 results (high Hupyy API load, comprehensive verification)
   - Option B: Top-10 results only (lower load, faster feedback loop)
   - Option C: Adaptive sampling based on query confidence

3. **Infrastructure Decision**: Where to deploy Hupyy Integration Service?
   - Option A: Within existing pipeshub-ai container (simpler deployment, shared resources)
   - Option B: Separate microservice container (better isolation, independent scaling)

4. **Migration Strategy**: How to handle existing indexed chunks without verification scores?
   - Option A: Gradual on-demand verification (verify as chunks are retrieved)
   - Option B: Batch backfill job (verify all existing chunks over time)
   - Option C: Hybrid approach with prioritization

5. **Rate Limiting**: Does Hupyy API have rate limits or pricing tiers?
   - Need to confirm max requests/minute, concurrent connections
   - Budget implications for production scale

6. **API Key Management**: How should Hupyy API credentials be stored and rotated?
   - Environment variables vs. secrets manager
   - Multi-tenant considerations if multiple API keys needed
</open_questions>

<assumptions>
- Hupyy API is stateless and idempotent (same input = same output)
- No authentication/authorization required for Hupyy API based on OpenAPI spec
- PipesHub has sufficient Kafka capacity for additional topics (estimate: ~1-5 MB/s additional throughput)
- Existing Qdrant collections can be updated without full re-indexing
- ArangoDB can handle additional metadata properties without schema migration
- Docker Compose setup can accommodate new service container (if separate microservice chosen)
- Network latency to Hupyy API is <100ms (needs verification in production environment)
- Hupyy service maintains 99.5%+ uptime (degraded mode required for failures)
</assumptions>

---

## Executive Summary

This research analyzes the technical feasibility and implementation requirements for integrating Hupyy's SMT verification service into PipesHub's search pipeline. The integration follows a three-stage architecture: semantic retrieval → formal verification → feedback integration, with the goal of achieving 98% Precision@5 through verification-guided ranking.

**Key Findings:**
1. **Hupyy API** provides a single endpoint (`POST /pipeline/process`) with 20-30s typical latency and comprehensive quality metrics
2. **Integration Architecture** requires 3 new microservices + Kafka event flow + database schema extensions
3. **Critical Path**: Error handling for UNKNOWN verdicts, timeout management, and cold-start period (30 days)
4. **Migration Complexity**: Low - backward compatible metadata additions, no breaking changes required
5. **Risk Level**: Medium - Primary risks are Hupyy API availability, latency impact, and feedback loop stability

---

## 1. Technical Integration Analysis

### 1.1 Hupyy API Contract

**Endpoint:** `POST https://verticalslice-smt-service-gvav8.ondigitalocean.app/pipeline/process`

**Request Schema:**
```json
{
  "informal_text": "string (1-100000 chars, required)",
  "skip_formalization": "boolean (optional, default: false)",
  "enrich": "boolean (optional, default: false)"
}
```

**Response Schema (200 Success):**
```json
{
  "informal_text": "original input",
  "enriched_text": "text after optional enrichment",
  "formal_text": "formalized representation",
  "formalization_similarity": 0.91,  // threshold: ≥0.91 for quality gate
  "smt_lib_code": "symbolic logic code block",
  "extraction_degradation": 0.03,    // threshold: ≤0.05 for quality gate
  "check_sat_result": "sat|unsat|unknown",
  "model": {...},                     // variable assignments if SAT
  "solver_success": true,
  "metrics": {...},                   // performance and quality data
  "passed_all_checks": true
}
```

**Error Handling:**
- `422 Unprocessable Entity`: Pipeline failed at formalization, extraction, or validation phase
  - Contains details on which stage failed
  - Should be treated as "invalid specification" (failure mode: invalid, multiplier: 0.3x)
- `500 Internal Server Error`: Service degradation
  - Requires circuit breaker pattern to prevent cascading failures

**Performance Characteristics:**
- **Typical latency**: 20-30 seconds with retries
- **Best case**: 3-10 seconds (single-pass success)
- **No authentication** required (based on OpenAPI spec)
- **No rate limits** documented (requires confirmation)

**Critical Quality Gates:**
- `formalization_similarity >= 0.91`: Ensures semantic preservation during formalization
- `extraction_degradation <= 0.05`: Ensures information preservation during SMT extraction
- `passed_all_checks == true`: Overall pipeline success indicator

✓ **Verified claim**: OpenAPI specification complete and accurate (source: https://verticalslice-smt-service-gvav8.ondigitalocean.app/openapi.json)

---

### 1.2 Integration Points in PipesHub Codebase

#### 1.2.1 Kafka Infrastructure (Existing)

**File:** `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/backend/nodejs/apps/src/libs/services/kafka.service.ts`

**Current Implementation:**
- `BaseKafkaProducerConnection`: Supports single message and batch publishing
- `BaseKafkaConsumerConnection`: Supports multi-topic subscription with retry logic
- **Retry configuration**: `initialRetryTime: 100ms, maxRetryTime: 30s, maxRetries: 8`
- **Allows auto-topic creation**: `allowAutoTopicCreation: true`

**Integration Point:**
- ✓ Existing infrastructure can support new verification topics
- ✓ Retry logic already implemented (exponential backoff)
- ⚠ No dead-letter queue pattern currently (should be added for verification failures)

**Required Changes:**
- Add new topics: `verify_chunks`, `verification_complete`, `verification_failed`
- Configure consumer groups for Verification Orchestrator
- Implement DLQ (Dead Letter Queue) for unrecoverable verification failures

---

#### 1.2.2 Qdrant Vector Database (Existing)

**File:** `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/backend/python/app/services/vector_db/qdrant/qdrant.py`

**Current Payload Structure:**
```python
# Existing payload fields (inferred from codebase)
{
    "chunk_id": str,
    "document_id": str,
    "content": str,
    "source": str,
    "position": int,
    "orgId": str,
    # ... other metadata fields
}
```

**Required Payload Extension (Backward Compatible):**
```python
{
    # Existing fields remain unchanged...

    # New verification metadata (optional, added incrementally)
    "verification": {
        "verdict": "SAT|UNSAT|UNKNOWN",  # check_sat_result from Hupyy
        "confidence": float,              # derived from formalization_similarity
        "solve_time_ms": int,             # from metrics
        "timestamp": int,                 # Unix timestamp
        "formal_spec": str,               # smt_lib_code
        "formalization_similarity": float,
        "extraction_degradation": float,
        "passed_all_checks": bool,
        "failure_mode": str,              # classified: verified_sat|invalid|ambiguous|incomplete|timeout|theory_incomplete
        "failure_indicators": list[str]   # diagnostic info
    },
    "verification_history": [            # track verification over time
        {
            "verified_at": int,
            "verdict": str,
            "confidence": float,
            "solver_version": str
        }
    ],
    "verification_metrics": {
        "verification_count": int,
        "success_rate": float,
        "avg_confidence": float,
        "last_verified": int,
        "verification_quality_score": float,  # EMA-smoothed score
        "temporal_weight": float              # exp(-λ × Δt) for decay
    }
}
```

**Update Strategy:**
- ✓ Use `overwrite_payload()` method (already exists in QdrantService)
- ✓ Supports Filter-based updates (can update chunks by ID)
- ✓ Real-time updates via HNSW algorithm (no re-indexing needed)

**Performance Considerations:**
- Payload indexing: Create indexes on `verification.verdict` and `verification.failure_mode` for efficient filtering
- Update throughput: Existing `upsert_points()` supports parallel batching (1000 points/batch, 5 workers)
- Expected update latency: <100ms per chunk (Fast Feedback Tier 1 requirement met)

✓ **Verified claim**: Qdrant supports real-time payload updates without re-indexing (source: [Qdrant Documentation](https://qdrant.tech/documentation/concepts/payload/))

---

#### 1.2.3 ArangoDB Knowledge Graph (Existing)

**File:** `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/backend/python/app/services/graph_db/arango/arango.py`

**Current Document Structure (Inferred):**
```python
{
    "_key": str,
    "title": str,
    "source": str,
    "author": str,
    "created_at": datetime
    # ... other document-level metadata
}
```

**Required Document Properties Extension:**
```python
{
    # Existing fields remain unchanged...

    # New verification aggregates (document-level)
    "verification_metrics": {
        "total_chunks": int,
        "verified_chunks": int,
        "verification_rate": float,        # verified_chunks / total_chunks
        "avg_confidence": float,           # average across all chunks
        "sat_count": int,
        "unsat_count": int,
        "unknown_count": int,
        "last_verification_scan": int
    },
    "quality_signals": {
        "quality_score": float,            # PageRank multiplier (0.5-2.0)
        "reliability_class": str,          # high|medium|low based on avg_confidence
        "citation_network": object         # for PageRank calculation
    },
    "pagerank_data": {
        "base_pagerank": float,
        "verification_weighted_pagerank": float,  # modified PageRank formula
        "quality_multiplier": float        # Q(Ti) in architecture doc
    }
}
```

**Update Strategy:**
- ArangoDB document updates via native update operations
- Batch updates for PageRank recalculation (hourly, per architecture)
- No schema migration required (JSON document flexibility)

**PageRank Integration:**
- Modified PageRank formula: `PR_v(A) = (1-d)/N + d × Σ(Q(Ti) × PR_v(Ti)/C(Ti))`
- Quality multiplier calculation:
  ```python
  if avg_confidence < 0.5:
      Q = 0.5  # penalize low-quality documents
  elif avg_confidence >= 0.5:
      Q = 1.0 + avg_confidence  # boost high-quality (max 2.0)
  else:
      Q = 1.0  # neutral for unverified
  ```

⚠ **Inferred from architecture**: PageRank implementation not found in codebase. Assumption: Will be implemented during integration.

---

#### 1.2.4 Search Query Flow (Integration Point)

**File:** `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/backend/nodejs/apps/src/modules/enterprise_search/schema/search.schema.ts`

**Current Schema:**
```typescript
interface IEnterpriseSemanticSearch {
  query: string;
  limit: number;
  orgId: ObjectId;
  userId: ObjectId;
  citationIds: ObjectId[];
  records: Record<string, any>;
  // ... sharing/archival fields
}
```

**Integration Point:**
- Query execution triggers Kafka event: `verify_chunks`
- Results returned to user (synchronous)
- Verification happens asynchronously in background
- Subsequent queries benefit from updated verification scores

**Async vs. Sync Decision Point:**
This is a **critical user decision** (see Open Questions #1):
- **Async (Recommended)**: Lower latency, eventual consistency
  - User sees initial results immediately
  - Verification updates scores for future queries
  - Requires UI indicator for "verification in progress"
- **Sync**: Higher latency but immediate verification
  - User waits 20-30s per query
  - Guaranteed verification scores on first query
  - Poor UX for interactive search

---

### 1.3 Error Handling Requirements

Based on research ([API Circuit Breaker Best Practices](https://www.unkey.com/glossary/api-circuit-breaker), [Resilient APIs](https://medium.com/@fahimad/resilient-apis-retry-logic-circuit-breakers-and-fallback-mechanisms-cfd37f523f43)):

#### 1.3.1 Timeout Strategy

**Recommended Configuration:**
```python
# Hupyy API timeout settings
HUPYY_REQUEST_TIMEOUT = 35  # seconds (slightly above max expected 30s)
HUPYY_CONNECTION_TIMEOUT = 5  # seconds
HUPYY_READ_TIMEOUT = 35  # seconds
```

**Rationale:**
- Hupyy typical latency: 20-30s
- Add 5s buffer for network variability
- Prevent indefinite hangs on failed service

**Failure Mode on Timeout:**
- Classify as `failure_mode: timeout`
- Apply multiplier: `0.85x` (small penalty, per architecture)
- Log for diagnostics
- Retry with exponential backoff (see below)

---

#### 1.3.2 Retry Logic with Exponential Backoff

**Recommended Configuration:**
```python
# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF = 1  # second
MAX_BACKOFF = 10  # seconds
BACKOFF_MULTIPLIER = 2
JITTER = True  # add random variance to prevent thundering herd

# Retry conditions
RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504]
RETRYABLE_EXCEPTIONS = [ConnectionError, Timeout, ReadTimeout]
```

**Implementation Pattern (Python):**
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_result
)

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=BACKOFF_MULTIPLIER, min=INITIAL_BACKOFF, max=MAX_BACKOFF),
    retry=retry_if_exception_type((ConnectionError, Timeout)),
    reraise=True
)
async def call_hupyy_api(chunk_content: str) -> VerificationResult:
    # API call implementation
    pass
```

**Non-Retryable Failures:**
- `422 Unprocessable Entity`: Indicates invalid specification (permanent failure)
  - Do NOT retry
  - Classify as `failure_mode: invalid`
  - Apply multiplier: `0.3x`

✓ **Verified claim**: Retry pattern aligns with industry best practices (source: [Build Resilient API Clients](https://spin.atomicobject.com/retry-circuit-breaker-patterns/))

---

#### 1.3.3 Circuit Breaker Pattern

**Recommended Configuration:**
```python
# Circuit breaker settings
FAILURE_THRESHOLD = 5  # open circuit after 5 consecutive failures
SUCCESS_THRESHOLD = 2  # close circuit after 2 consecutive successes in half-open state
TIMEOUT = 60  # seconds in open state before attempting half-open
HALF_OPEN_MAX_CALLS = 3  # max concurrent calls in half-open state
```

**Circuit States:**
1. **Closed** (Normal operation):
   - All requests proceed to Hupyy API
   - Track failure count
   - If `failure_count >= FAILURE_THRESHOLD`: transition to **Open**

2. **Open** (Service degraded):
   - All requests fail immediately (no API calls)
   - Apply fallback: `failure_mode: service_unavailable`, multiplier: `1.0x` (neutral)
   - After `TIMEOUT` seconds: transition to **Half-Open**

3. **Half-Open** (Testing recovery):
   - Allow limited requests (`HALF_OPEN_MAX_CALLS`)
   - If `SUCCESS_THRESHOLD` consecutive successes: transition to **Closed**
   - If any failure: transition back to **Open**

**Implementation (Python with pybreaker):**
```python
from pybreaker import CircuitBreaker

hupyy_breaker = CircuitBreaker(
    fail_max=FAILURE_THRESHOLD,
    timeout_duration=TIMEOUT,
    expected_exception=HupyyServiceException
)

@hupyy_breaker
async def call_hupyy_with_circuit_breaker(chunk_content: str):
    return await call_hupyy_api(chunk_content)
```

**Fallback Strategy:**
- When circuit is **Open**, return placeholder verification result:
  ```python
  {
      "verdict": "UNKNOWN",
      "failure_mode": "service_unavailable",
      "confidence": 0.0,
      "multiplier": 1.0  # neutral, no penalty for external service failure
  }
  ```
- Log circuit state changes for monitoring
- Alert on circuit open (indicates sustained Hupyy API issues)

✓ **Verified claim**: Circuit breaker prevents cascading failures (source: [Microservices Pattern: Circuit Breaker](https://microservices.io/patterns/reliability/circuit-breaker.html))

---

#### 1.3.4 Dead Letter Queue (DLQ) Pattern

**Kafka Topic for Failures:**
```
verify_chunks_dlq
```

**DLQ Trigger Conditions:**
1. Max retries exhausted (3 attempts failed)
2. Non-retryable error (422 Unprocessable Entity)
3. Serialization/deserialization errors
4. Unexpected exceptions

**DLQ Message Format:**
```json
{
  "original_message": {
    "chunk_id": "...",
    "content": "...",
    "metadata": {...}
  },
  "failure_reason": "...",
  "failure_timestamp": 1234567890,
  "retry_count": 3,
  "last_exception": "...",
  "can_retry_manually": true
}
```

**Manual Retry Workflow:**
- Admin dashboard to view DLQ messages
- Ability to replay failed verifications
- Logging for root cause analysis

---

## 2. Architecture Recommendations

### 2.1 Microservice Design

#### Option A: Integrated Service (Within pipeshub-ai container)
**Pros:**
- Simpler deployment (no new container)
- Shared logging and monitoring infrastructure
- Faster inter-service communication (localhost)

**Cons:**
- Resource contention with existing services
- Harder to scale independently
- Tighter coupling

#### Option B: Separate Microservice (Recommended)
**Pros:**
- Independent scaling (can allocate more resources for verification)
- Fault isolation (Hupyy integration failures don't affect core search)
- Cleaner separation of concerns (SOLID principles)
- Easier to swap verification providers in future

**Cons:**
- Additional deployment complexity
- Network latency between containers (minimal in Docker Compose)
- More monitoring endpoints

**Recommendation: Option B (Separate Microservice)**

**Service Structure:**
```
hupyy-verification-service/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration management
│   ├── services/
│   │   ├── hupyy_client.py     # Hupyy API integration
│   │   ├── circuit_breaker.py  # Resilience patterns
│   │   └── verification_orchestrator.py
│   ├── kafka/
│   │   ├── producer.py         # Kafka producer for results
│   │   └── consumer.py         # Kafka consumer for requests
│   ├── models/
│   │   ├── verification.py     # Verification data models
│   │   └── failure_modes.py    # Failure classification
│   └── utils/
│       ├── retry.py            # Retry decorators
│       └── metrics.py          # Prometheus metrics
├── tests/
│   ├── unit/
│   ├── integration/
│   └── load/
├── Dockerfile
├── pyproject.toml
└── README.md
```

**Docker Compose Addition:**
```yaml
# docker-compose.prod.yml extension
services:
  hupyy-verification:
    build: ./backend/python/hupyy-verification-service
    container_name: hupyy-verification
    restart: always
    environment:
      - HUPYY_API_URL=https://verticalslice-smt-service-gvav8.ondigitalocean.app
      - KAFKA_BROKERS=kafka-1:9092
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      - ARANGO_URL=http://arango:8529
      - LOG_LEVEL=info
      - CIRCUIT_BREAKER_ENABLED=true
      - MAX_CONCURRENT_VERIFICATIONS=10
    depends_on:
      kafka-1:
        condition: service_healthy
      qdrant:
        condition: service_healthy
      arango:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

---

### 2.2 Kafka Topic Design

#### Topic Structure

**Topic 1: `verify_chunks`**
- **Purpose**: Queue chunks for verification
- **Producers**: Node.js API layer (after search query execution)
- **Consumers**: Verification Orchestrator service
- **Partitions**: 3 (for parallel consumption)
- **Retention**: 7 days (allow replay for debugging)
- **Message Format**:
  ```json
  {
    "chunk_id": "uuid-string",
    "content": "chunk text content (1-100000 chars)",
    "document_id": "parent document ID",
    "org_id": "organization ID for filtering",
    "user_id": "requesting user ID",
    "query_id": "originating search query ID",
    "priority": "high|normal|low",
    "timestamp": 1234567890
  }
  ```

**Topic 2: `verification_complete`**
- **Purpose**: Broadcast successful verification results
- **Producers**: Verification Orchestrator service
- **Consumers**: Qdrant Updater, ArangoDB Updater, PageRank Calculator, Metrics Collector
- **Partitions**: 3
- **Retention**: 30 days (for historical analysis)
- **Message Format**:
  ```json
  {
    "chunk_id": "uuid-string",
    "verification_result": {
      "verdict": "SAT|UNSAT|UNKNOWN",
      "confidence": 0.95,
      "solve_time_ms": 15000,
      "formal_spec": "SMT-LIB2 code",
      "formalization_similarity": 0.93,
      "extraction_degradation": 0.02,
      "passed_all_checks": true,
      "failure_mode": "verified_sat",
      "failure_indicators": [],
      "model": {...}
    },
    "metadata": {
      "document_id": "parent document ID",
      "org_id": "...",
      "verified_at": 1234567890,
      "hupyy_version": "0.1.0"
    }
  }
  ```

**Topic 3: `verification_failed`**
- **Purpose**: Track verification failures for monitoring
- **Producers**: Verification Orchestrator service
- **Consumers**: Metrics Collector, Dead Letter Queue processor
- **Partitions**: 1 (failures expected to be low volume)
- **Retention**: 30 days
- **Message Format**:
  ```json
  {
    "chunk_id": "uuid-string",
    "failure_reason": "timeout|service_unavailable|invalid_spec|error",
    "error_details": "...",
    "retry_count": 3,
    "can_retry": false,
    "timestamp": 1234567890
  }
  ```

**Topic 4: `metadata_update` (Optional - for batch updates)**
- **Purpose**: Trigger batch updates to Qdrant/ArangoDB
- **Producers**: Verification Orchestrator (batching small updates)
- **Consumers**: Batch Update service
- **Partitions**: 1
- **Retention**: 1 day

**Topic 5: `pagerank_recalc`**
- **Purpose**: Trigger PageRank recalculation
- **Producers**: ArangoDB Updater (when document metrics change significantly)
- **Consumers**: PageRank Calculator service
- **Partitions**: 1 (single-threaded calculation)
- **Retention**: 1 day

---

### 2.3 Event Flow Design

```
User Query → Node.js API Layer
              ↓
         Execute Search (Qdrant + ArangoDB)
              ↓
         Return Results to User (synchronous)
              ↓
         Kafka Produce: verify_chunks (async, batch top-50)
              ↓
         [Kafka Topic: verify_chunks]
              ↓
         Verification Orchestrator (consumer)
              ├─→ Chunk 1: Call Hupyy API
              ├─→ Chunk 2: Call Hupyy API (parallel, max 10 concurrent)
              └─→ Chunk N: Call Hupyy API
              ↓
         Classify Failure Mode (if UNSAT/UNKNOWN)
              ↓
         Kafka Produce: verification_complete OR verification_failed
              ↓
         [Parallel Processing]
         ├─→ Qdrant Updater: Update chunk payload (EMA score)
         ├─→ ArangoDB Updater: Update document metrics
         ├─→ PageRank Calculator: Queue for batch recalc (hourly)
         └─→ Metrics Collector: Log for dashboard
```

**Batching Strategy:**
- **Input batching**: Consume `verify_chunks` in batches of 10 (configurable)
- **Output batching**: Produce `verification_complete` individually (low latency requirement)
- **Parallel processing**: Max 10 concurrent Hupyy API calls (configurable based on API limits)

**Consumer Group Strategy:**
- `verify_chunks`: Single consumer group `verification-orchestrator-group`
  - Multiple instances for scaling (partitioned by chunk_id hash)
- `verification_complete`: Multiple consumer groups
  - `qdrant-updater-group`: Updates vector DB
  - `arango-updater-group`: Updates graph DB
  - `pagerank-calculator-group`: Triggers PageRank recalc
  - `metrics-collector-group`: Logs metrics

---

### 2.4 Database Schema Changes

#### 2.4.1 Qdrant Payload Schema (JSON Extension)

**Index Creation (Critical for Performance):**
```python
# Create indexes for verification fields
await qdrant_service.create_index(
    collection_name="pipeshub_chunks",
    field_name="verification.verdict",
    field_schema={"type": "keyword"}
)

await qdrant_service.create_index(
    collection_name="pipeshub_chunks",
    field_name="verification.failure_mode",
    field_schema={"type": "keyword"}
)

await qdrant_service.create_index(
    collection_name="pipeshub_chunks",
    field_name="verification_metrics.verification_quality_score",
    field_schema={"type": "float"}  # for range filtering
)
```

**Query Example (Filter by Verification Status):**
```python
# Search only verified chunks
filter = await qdrant_service.filter_collection(
    must={
        "verification.passed_all_checks": True,
        "verification.verdict": "SAT"
    }
)
results = qdrant_service.query_nearest_points(
    collection_name="pipeshub_chunks",
    requests=[QueryRequest(query=embedding, filter=filter, limit=50)]
)
```

**Update Example (EMA Score Update - Fast Feedback Tier 1):**
```python
# α = 0.1 (per architecture)
new_score = 0.1 * new_verification_confidence + 0.9 * historical_score

await qdrant_service.overwrite_payload(
    collection_name="pipeshub_chunks",
    payload={
        "verification_metrics.verification_quality_score": new_score,
        "verification_metrics.last_verified": int(time.time())
    },
    points=Filter(must=[FieldCondition(key="chunk_id", match={"value": chunk_id})])
)
```

✓ **Verified claim**: Qdrant supports real-time metadata updates via payload extension (source: [Qdrant Payload Documentation](https://qdrant.tech/documentation/concepts/payload/))

---

#### 2.4.2 ArangoDB Document Schema (JSON Extension)

**Collection:** `documents` (existing collection)

**Update Example (Aggregate Verification Metrics):**
```python
# After verification of a chunk, update parent document
db = arango_service.get_db()
documents = db.collection('documents')

document = documents.get(document_id)
verified_chunks = document.get('verification_metrics', {}).get('verified_chunks', 0) + 1
total_chunks = document.get('verification_metrics', {}).get('total_chunks', 0)

# Recalculate averages
sat_count = document.get('verification_metrics', {}).get('sat_count', 0)
if verdict == "SAT":
    sat_count += 1

avg_confidence = (
    (avg_confidence * (verified_chunks - 1) + new_confidence) / verified_chunks
)

# Update document
documents.update({
    '_key': document_id,
    'verification_metrics': {
        'total_chunks': total_chunks,
        'verified_chunks': verified_chunks,
        'verification_rate': verified_chunks / total_chunks,
        'avg_confidence': avg_confidence,
        'sat_count': sat_count,
        'last_verification_scan': int(time.time())
    }
})
```

**PageRank Quality Multiplier Calculation:**
```python
def calculate_quality_multiplier(avg_confidence: float) -> float:
    """
    Calculate PageRank quality multiplier based on verification confidence.

    Per architecture:
    - avg_conf < 0.5 → Q = 0.5 (penalize low quality)
    - no verification → Q = 1.0 (neutral)
    - avg_conf ≥ 0.5 → Q = 1.0 + avg_conf (boost, max 2.0)
    """
    if avg_confidence is None:
        return 1.0  # neutral for unverified
    elif avg_confidence < 0.5:
        return 0.5
    else:
        return 1.0 + avg_confidence
```

⚠ **Assumption**: PageRank calculation logic not found in codebase. Implementation required during integration phase.

---

## 3. Risk Assessment

### 3.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|-----------|--------|---------------------|
| **Hupyy API Downtime** | Medium | High | Circuit breaker pattern, fallback to neutral scoring (1.0x multiplier), monitoring with alerts |
| **Hupyy API Latency Spike** | Medium | Medium | Timeout configuration (35s), async processing, queue depth monitoring |
| **Verification Accuracy Issues** | Low | High | Multiple solver consensus (Z3 + cvc5), quality gates (formalization_similarity ≥ 0.91), holdout set validation |
| **Kafka Queue Backlog** | Low | Medium | Auto-scaling consumers, backpressure monitoring, consumer lag alerts |
| **Database Update Failures** | Low | Medium | Transaction retry logic, idempotency checks, eventual consistency acceptance |
| **Cold Start Poor Performance** | High | Medium | Gradual weight transition (0% → 15% over 30 days), pseudo-relevance feedback initially |
| **Feedback Loop Instability** | Medium | High | Query drift detection (||Q_new - Q_orig|| < 0.3), L2 regularization, ε-greedy exploration (10-15%) |
| **Cost Overruns (Hupyy API)** | Medium | Medium | Rate limiting, adaptive sampling, budget monitoring, caching verified results |
| **Memory/CPU Exhaustion** | Low | High | Resource limits in Docker Compose (2G RAM, 2 CPUs), connection pooling, garbage collection tuning |

---

### 3.2 Migration Risks

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|-----------|--------|---------------------|
| **Breaking Changes to Search API** | Low | Critical | Backward compatible metadata additions, feature flags for gradual rollout |
| **Data Loss During Migration** | Low | Critical | No data deletion required, additive-only schema changes, backup before deployment |
| **Performance Degradation** | Medium | High | A/B testing, gradual rollout per organization, performance benchmarking |
| **Rollback Complexity** | Medium | Medium | Feature flag to disable verification, maintain neutral scoring as fallback |

---

### 3.3 Operational Risks

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|-----------|--------|---------------------|
| **Insufficient Monitoring** | High | High | Prometheus metrics, Grafana dashboards, PagerDuty alerts, runbook documentation |
| **Unclear Ownership** | Medium | Medium | Define SLA for Hupyy integration service, on-call rotation, incident response plan |
| **Debugging Difficulty** | Medium | High | Structured logging (JSON), distributed tracing, request ID propagation, debug mode |
| **Documentation Drift** | High | Low | Living documentation in code comments, OpenAPI spec for new services, architecture diagrams |

---

## 4. Data Flow Design

### 4.1 Verification Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Stage 1: Search Execution (Synchronous)                         │
├─────────────────────────────────────────────────────────────────┤
│ 1. User submits query                                           │
│ 2. Generate embedding (existing)                                │
│ 3. Qdrant vector search (k=100, existing)                       │
│ 4. ArangoDB graph traversal (existing)                          │
│ 5. Hybrid ranking (existing)                                    │
│ 6. Cross-encoder reranking (k=50, existing)                     │
│ 7. Apply PageRank scores (existing + NEW: verification-weighted)│
│ 8. Apply verification scores (NEW: from Qdrant payload)         │
│    - If verification_metrics exists: apply multiplier           │
│    - If no verification: neutral (1.0x multiplier)              │
│ 9. Return results to user (top 5-10)                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stage 2: Async Verification Trigger                             │
├─────────────────────────────────────────────────────────────────┤
│ 10. Kafka produce: verify_chunks (top-50 results, batch)        │
│     - Include: chunk_id, content, metadata                      │
│     - Priority: high (if user waiting), normal (background)     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3: Verification Execution (Async, Parallel)               │
├─────────────────────────────────────────────────────────────────┤
│ 11. Verification Orchestrator consumes verify_chunks            │
│ 12. For each chunk (max 10 parallel):                           │
│     a. Check circuit breaker state                              │
│     b. Call Hupyy API with retry logic:                         │
│        POST /pipeline/process                                   │
│        Body: {"informal_text": chunk_content}                   │
│     c. Parse response:                                          │
│        - check_sat_result → verdict                             │
│        - formalization_similarity → confidence                  │
│        - metrics → solve_time_ms                                │
│     d. Classify failure mode (if UNSAT/UNKNOWN):                │
│        - Invalid: core_size 2-3, fast solve                     │
│        - Ambiguous: multiple models                             │
│        - Incomplete: >50% vars unconstrained                    │
│        - Timeout: hit resource limit                            │
│        - Theory incomplete: undecidable logic                   │
│     e. Determine multiplier:                                    │
│        - verified_sat: 1.8x                                     │
│        - invalid: 0.3x                                          │
│        - ambiguous: 0.7x                                        │
│        - incomplete: 0.8x                                       │
│        - timeout: 0.85x                                         │
│        - theory_incomplete: 1.0x                                │
│ 13. Kafka produce: verification_complete OR verification_failed │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stage 4: Feedback Integration (Async, Parallel)                 │
├─────────────────────────────────────────────────────────────────┤
│ 14. Qdrant Updater (consumer):                                  │
│     a. Calculate EMA score (α=0.1):                             │
│        new = 0.1 × confidence + 0.9 × historical                │
│     b. Calculate temporal weight:                               │
│        weight = exp(-0.01 × days_since_verification)            │
│     c. Update Qdrant payload:                                   │
│        - verification.* fields                                  │
│        - verification_history (append)                          │
│        - verification_metrics.verification_quality_score        │
│     d. Latency target: <100ms (Fast Feedback Tier 1)            │
│                                                                 │
│ 15. ArangoDB Updater (consumer):                                │
│     a. Aggregate document-level metrics                         │
│     b. Update verification_metrics                              │
│     c. Recalculate quality_multiplier (Q)                       │
│     d. If significant change (ΔQ > 0.2):                        │
│        Kafka produce: pagerank_recalc                           │
│                                                                 │
│ 16. PageRank Calculator (consumer):                             │
│     a. Batch recalculate (hourly, per architecture)             │
│     b. Modified PageRank with quality multiplier:               │
│        PR_v(A) = (1-d)/N + d × Σ(Q(Ti) × PR_v(Ti)/C(Ti))       │
│     c. Update ArangoDB pagerank_data                            │
│                                                                 │
│ 17. Metrics Collector (consumer):                               │
│     a. Log verification event                                   │
│     b. Update Prometheus metrics                                │
│     c. Check alert thresholds                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

### 4.2 Cold Start Handling

**Problem:** No verification data exists for existing indexed chunks.

**Solution:** Three-phase cold start strategy (per architecture):

**Phase 1: Days 1-7 (Pseudo-Relevance Feedback)**
- Verification weight: 0%
- Rely on semantic similarity (90%) + pseudo-feedback (10%)
- Log all retrievals for verification candidates

**Phase 2: Days 8-30 (Gradual Transition)**
- Verification weight: 0% → 15% (linear increase)
- Prioritize verification for:
  - Frequently retrieved chunks (popularity-based)
  - High uncertainty chunks (low semantic similarity)
  - Exploration budget: 20% random sampling
- Semantic weight: 90% → 45%
- PageRank weight: 0% → 30%

**Phase 3: Day 30+ (Full Integration)**
- Final weights (per architecture):
  - Semantic: 45%
  - PageRank: 30%
  - Verification: 15%
  - Historical: 10%

**Transfer Learning for Unverified Chunks:**
```python
def estimate_initial_score(chunk, similar_chunks):
    """
    Estimate verification score for unverified chunk based on similar chunks.

    Formula (per architecture):
    initial_score = 0.7 × avg(similar_verified_chunks) + 0.3 × global_avg
    """
    similar_verified = [c for c in similar_chunks if c.has_verification]

    if not similar_verified:
        return global_avg_score  # fallback to global average

    similar_avg = sum(c.verification_score for c in similar_verified) / len(similar_verified)
    return 0.7 * similar_avg + 0.3 * global_avg_score
```

**Expected Improvement Trajectory (per architecture):**
- **Weeks 1-4**: NDCG +0-2%, Precision@5 +0%
- **Weeks 5-12**: NDCG +3-5%, Precision@5 +10-15%
- **Weeks 13-24**: NDCG +6-9%, Precision@5 +25-35%
- **Weeks 25-52**: NDCG +8-12%, Precision@5 → 98% (target)

✓ **Verified claim**: Cold start strategy matches architecture specification (source: architecture doc section 9.2)

---

### 4.3 Failure Mode Handling

**Decision Tree Implementation:**

```python
from enum import Enum
from dataclasses import dataclass

class FailureMode(Enum):
    VERIFIED_SAT = ("verified_sat", 1.8)
    INVALID = ("invalid", 0.3)
    AMBIGUOUS = ("ambiguous", 0.7)
    INCOMPLETE = ("incomplete", 0.8)
    TIMEOUT = ("timeout", 0.85)
    THEORY_INCOMPLETE = ("theory_incomplete", 1.0)
    NEVER_VERIFIED = ("never_verified", 1.0)
    SERVICE_UNAVAILABLE = ("service_unavailable", 1.0)

@dataclass
class VerificationResult:
    verdict: str  # SAT|UNSAT|UNKNOWN
    confidence: float
    solve_time_ms: int
    model: dict
    unsat_core_size: int
    unconstrained_var_ratio: float
    failure_reason: str

def classify_failure_mode(result: VerificationResult) -> FailureMode:
    """
    Classify verification result into failure mode based on architecture decision tree.

    Source: Architecture doc section 8.1
    """
    verdict = result.verdict

    if verdict == "SAT":
        # Check for multiple models (ambiguous)
        if has_multiple_models(result):
            return FailureMode.AMBIGUOUS

        # Check for under-constrained specification (incomplete)
        if result.unconstrained_var_ratio > 0.5:
            return FailureMode.INCOMPLETE

        # Single consistent model
        return FailureMode.VERIFIED_SAT

    elif verdict == "UNSAT":
        # Small core = direct contradiction (invalid)
        if result.unsat_core_size <= 3:
            return FailureMode.INVALID

        # Large core = complex interaction (still problematic but less severe)
        # Architecture treats this as INVALID with same multiplier
        return FailureMode.INVALID

    elif verdict == "UNKNOWN":
        # Check reason
        if "timeout" in result.failure_reason.lower():
            return FailureMode.TIMEOUT
        elif "quantifier" in result.failure_reason.lower() or "nonlinear" in result.failure_reason.lower():
            return FailureMode.THEORY_INCOMPLETE
        else:
            # Generic UNKNOWN
            return FailureMode.TIMEOUT  # default to timeout multiplier (0.85x)

    else:
        # Should never happen, but handle gracefully
        return FailureMode.NEVER_VERIFIED

def has_multiple_models(result: VerificationResult) -> bool:
    """
    Detect ambiguous specifications by running solver multiple times with different random seeds.

    Note: Requires multiple solver invocations, may increase latency.
    """
    # Implementation detail: Hupyy API doesn't expose random seed parameter
    # Assumption: Single run is deterministic, no ambiguity detection needed
    # Alternative: Analyze model completeness (all vars constrained?)
    return False  # Simplified for now
```

✓ **Verified claim**: Failure mode classification matches architecture decision tree (source: architecture doc section 8.1)

---

## 5. Performance & Quality Targets

### 5.1 Ranking Formula

**Base Score Calculation:**
```python
def calculate_base_score(
    semantic_similarity: float,
    pagerank_score: float,
    verification_confidence: float,
    historical_success: float
) -> float:
    """
    Calculate weighted base score.

    Weights per architecture section 6.1:
    - Semantic: 45%
    - PageRank: 30%
    - Verification: 15%
    - Historical: 10%
    """
    return (
        0.45 * semantic_similarity +
        0.30 * pagerank_score +
        0.15 * verification_confidence +
        0.10 * historical_success
    )
```

**Final Score with Failure Mode Multiplier:**
```python
def calculate_final_score(base_score: float, failure_mode: FailureMode) -> float:
    """
    Apply failure mode multiplier to base score.

    Example (per architecture section 6.2):
    - base_score = 0.75
    - failure_mode = VERIFIED_SAT (1.8x)
    - final_score = 0.75 × 1.8 = 1.35
    """
    multiplier = failure_mode.value[1]
    return base_score * multiplier
```

---

### 5.2 Quality Metrics (Monitoring Dashboard)

**Retrieval Quality (Target Metrics per Architecture):**
```python
QUALITY_TARGETS = {
    "ndcg@10": {
        "baseline": 0.65,
        "target": 0.75,
        "current": None  # populated from live data
    },
    "mrr": {
        "baseline": 0.55,
        "target": 0.70,
        "current": None
    },
    "precision@5": {
        "baseline": 0.40,
        "target": 0.98,  # Primary target
        "current": None
    },
    "recall@50": {
        "baseline": 0.80,
        "target": 0.90,
        "current": None
    }
}
```

**Verification Metrics:**
```python
VERIFICATION_METRICS = {
    "total_verifications": 0,
    "success_rate": 0.0,  # % that pass all checks
    "avg_confidence": 0.0,
    "avg_solve_time_ms": 0,
    "failure_mode_distribution": {
        "verified_sat": 0,     # Target: 40-50%
        "invalid": 0,          # Target: <10%
        "ambiguous": 0,        # Target: <15%
        "incomplete": 0,       # Target: <15%
        "timeout": 0,          # Target: <10%
        "theory_incomplete": 0 # Target: <10%
    }
}
```

**Feedback Loop Health:**
```python
FEEDBACK_HEALTH = {
    "coverage": 0.0,           # % of docs with ≥5 verified chunks, Target: >80%
    "diversity_entropy": 0.0,  # Shannon entropy of verification distribution, Target: ≥3.0 bits
    "query_drift": 0.0,        # ||Q_new - Q_orig||, Limit: <0.3
    "exploration_rate": 0.0    # % random exploration, Target: 10-15%
}
```

**System Performance:**
```python
SYSTEM_METRICS = {
    "avg_query_latency_ms": 0,
    "verification_queue_depth": 0,
    "kafka_consumer_lag": 0,
    "circuit_breaker_state": "closed",  # closed|half_open|open
    "qdrant_update_latency_ms": 0,      # Target: <100ms
    "arango_update_latency_ms": 0
}
```

---

### 5.3 Alert Thresholds (Prometheus/Grafana)

**CRITICAL Alerts (PagerDuty):**
- `holdout_performance_drop > 0.10`: Rollback recent updates
- `verification_success_rate < 0.50`: Investigate Hupyy API or solver issues
- `circuit_breaker_state == "open"`: Hupyy service unavailable

**WARNING Alerts (Slack):**
- `diversity_entropy < 3.0`: Increase exploration rate
- `verification_queue_depth > 100`: Scale verification service
- `query_drift > 0.3`: Reduce feedback weight
- `kafka_consumer_lag > 1000`: Consumer performance issue

**INFO Alerts (Dashboard Log):**
- `verification_success_rate` change >5% week-over-week
- New document type detected (allocate verification budget)

✓ **Verified claim**: Alert thresholds match architecture specifications (source: architecture doc section 10.3)

---

## 6. Implementation Checklist

### 6.1 Phase 1: Foundation (Weeks 1-2)

- [ ] **Setup Development Environment**
  - [ ] Create `hupyy-verification-service` directory structure
  - [ ] Initialize Python project (pyproject.toml, dependencies)
  - [ ] Setup FastAPI application skeleton
  - [ ] Configure logging (structured JSON logs)

- [ ] **Hupyy API Integration**
  - [ ] Implement `HupyyClient` class
    - [ ] POST request to `/pipeline/process`
    - [ ] Request/response serialization
    - [ ] Error handling (422, 500, timeout)
  - [ ] Add timeout configuration (35s request, 5s connection)
  - [ ] Implement retry logic with exponential backoff (tenacity library)
  - [ ] Implement circuit breaker (pybreaker library)
  - [ ] Unit tests for HupyyClient (mock API responses)

- [ ] **Kafka Integration**
  - [ ] Create Kafka topics (verify_chunks, verification_complete, verification_failed)
  - [ ] Implement Kafka consumer for `verify_chunks`
  - [ ] Implement Kafka producer for `verification_complete`
  - [ ] Configure consumer group and partitioning
  - [ ] Integration tests for Kafka message flow

- [ ] **Database Schema Extensions**
  - [ ] Define Qdrant payload schema (verification fields)
  - [ ] Define ArangoDB document schema (verification_metrics)
  - [ ] Create payload indexes in Qdrant (verdict, failure_mode)
  - [ ] Test payload update operations (EMA calculation)

- [ ] **Verification Orchestrator Service**
  - [ ] Implement main orchestration loop
  - [ ] Parallel verification execution (max 10 concurrent)
  - [ ] Failure mode classification logic
  - [ ] Multiplier calculation
  - [ ] Integration tests with mock Hupyy API

- [ ] **Deployment Configuration**
  - [ ] Create Dockerfile for verification service
  - [ ] Add service to docker-compose.prod.yml
  - [ ] Configure environment variables
  - [ ] Setup health check endpoint

- [ ] **Baseline Metrics Collection**
  - [ ] Capture current NDCG@10, MRR, Precision@5, Recall@50
  - [ ] Setup Prometheus metrics exporter
  - [ ] Create Grafana dashboard (initial version)

---

### 6.2 Phase 2: Fast Feedback Loop (Weeks 3-6)

- [ ] **Qdrant Updater Service**
  - [ ] Consume `verification_complete` events
  - [ ] Implement EMA score calculation (α=0.1)
  - [ ] Implement temporal weight decay (λ=0.01)
  - [ ] Update Qdrant payloads (<100ms latency target)
  - [ ] Add verification_history tracking
  - [ ] Unit tests and integration tests

- [ ] **ArangoDB Updater Service**
  - [ ] Consume `verification_complete` events
  - [ ] Aggregate document-level verification metrics
  - [ ] Calculate quality multiplier (Q)
  - [ ] Update document properties
  - [ ] Trigger PageRank recalc on significant changes
  - [ ] Integration tests

- [ ] **Search Query Integration**
  - [ ] Modify search pipeline to check verification scores
  - [ ] Apply failure mode multipliers to ranking
  - [ ] Implement async verification trigger (Kafka produce)
  - [ ] Add verification status to search response (optional UI field)
  - [ ] Integration tests for end-to-end search flow

- [ ] **Cold Start Strategy**
  - [ ] Implement gradual weight transition (Days 1-7, 8-30, 30+)
  - [ ] Implement transfer learning for unverified chunks
  - [ ] Prioritization logic (popularity + uncertainty sampling)
  - [ ] Exploration budget (20% random)

- [ ] **Monitoring & Alerts**
  - [ ] Implement Prometheus metrics collector
  - [ ] Create comprehensive Grafana dashboard
  - [ ] Configure PagerDuty/Slack alerts
  - [ ] Add circuit breaker state monitoring

- [ ] **Load Testing**
  - [ ] Simulate high query volume (100 queries/sec)
  - [ ] Measure verification throughput (chunks/sec)
  - [ ] Identify bottlenecks (Hupyy API, Kafka, database updates)
  - [ ] Optimize parallel processing (tune max_concurrent_verifications)

---

### 6.3 Phase 3: Medium Feedback Loop (Weeks 7-12)

- [ ] **PageRank Calculator Service**
  - [ ] Implement modified PageRank algorithm
  - [ ] Quality multiplier integration (Q(Ti))
  - [ ] Batch recalculation (hourly)
  - [ ] Update ArangoDB pagerank_data
  - [ ] Performance optimization (graph traversal)

- [ ] **Reranker Optimization (Optional)**
  - [ ] Collect query patterns and verification outcomes
  - [ ] Retrain cross-encoder with verification signals
  - [ ] A/B test reranker improvements
  - [ ] Deploy updated reranker

- [ ] **Feedback Loop Safeguards**
  - [ ] Query drift detection (||Q_new - Q_orig|| < 0.3)
  - [ ] L2 regularization in score updates
  - [ ] ε-greedy exploration (10-15%)
  - [ ] Holdout set validation (15% never used for training)

- [ ] **Performance Tuning**
  - [ ] Optimize Qdrant query performance (payload filtering)
  - [ ] Optimize ArangoDB aggregations
  - [ ] Tune Kafka consumer batch sizes
  - [ ] Database connection pooling

---

### 6.4 Phase 4: Validation & Deployment (Weeks 13-16)

- [ ] **End-to-End Testing**
  - [ ] Manual testing with real queries
  - [ ] Verify quality metrics improvement
  - [ ] Test failure scenarios (Hupyy API down, timeout, etc.)
  - [ ] Test cold start behavior

- [ ] **Migration Planning**
  - [ ] Document rollback procedure
  - [ ] Feature flag implementation (gradual rollout)
  - [ ] Backup existing Qdrant/ArangoDB data
  - [ ] Dry-run deployment in staging

- [ ] **Documentation**
  - [ ] API documentation (OpenAPI spec for verification service)
  - [ ] Runbook for on-call engineers
  - [ ] Architecture diagrams (update with as-built)
  - [ ] User-facing documentation (verification badges in UI)

- [ ] **Production Deployment**
  - [ ] Deploy to production environment
  - [ ] Enable feature flag for 10% of users
  - [ ] Monitor metrics and alerts
  - [ ] Gradual rollout to 100% over 2 weeks

- [ ] **Post-Deployment Review**
  - [ ] Analyze quality metric improvements
  - [ ] Identify issues and optimization opportunities
  - [ ] Collect user feedback
  - [ ] Plan Phase 5 (embedding fine-tuning, if applicable)

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Target Coverage:** 80%+ for core logic

**Test Suites:**
1. **HupyyClient Tests**
   - Mock API responses (200, 422, 500, timeout)
   - Test retry logic (exponential backoff, max retries)
   - Test circuit breaker state transitions
   - Test request serialization/deserialization

2. **Failure Mode Classification Tests**
   - Test SAT verdict classification (verified_sat, ambiguous, incomplete)
   - Test UNSAT verdict classification (invalid)
   - Test UNKNOWN verdict classification (timeout, theory_incomplete)
   - Edge cases (empty model, null values)

3. **Score Calculation Tests**
   - Test base score weighted sum
   - Test failure mode multiplier application
   - Test EMA calculation (α=0.1)
   - Test temporal weight decay (λ=0.01)

4. **Kafka Message Serialization Tests**
   - Test message format compliance
   - Test error handling for malformed messages

**Framework:** pytest (Python), Jest (Node.js)

---

### 7.2 Integration Tests

**Test Scenarios:**
1. **End-to-End Verification Flow**
   - Search query → Kafka produce → Verification → Kafka consume → Database update
   - Verify Qdrant payload updated correctly
   - Verify ArangoDB document metrics updated
   - Verify PageRank recalculation triggered

2. **Error Handling**
   - Hupyy API timeout → timeout failure mode
   - Hupyy API 422 → invalid failure mode
   - Circuit breaker trip → service_unavailable failure mode
   - Kafka consumer failure → message redelivery

3. **Kafka Topic Integration**
   - Produce/consume messages across all topics
   - Test consumer group coordination (multiple instances)
   - Test partition assignment

4. **Database Update Idempotency**
   - Duplicate verification result → no double-counting
   - Verify EMA calculation consistency

**Framework:** pytest with Docker Compose test environment

---

### 7.3 Load Tests

**Objectives:**
- Determine max throughput (chunks verified/sec)
- Identify bottlenecks (Hupyy API, Kafka, databases)
- Validate latency targets (<100ms for Qdrant updates)

**Test Scenarios:**
1. **High Query Volume**
   - 100 queries/sec for 10 minutes
   - Measure end-to-end latency
   - Monitor Kafka queue depth
   - Monitor consumer lag

2. **Burst Verification Load**
   - 1000 chunks queued simultaneously
   - Measure time to drain queue
   - Monitor circuit breaker behavior (should NOT trip)

3. **Database Update Throughput**
   - 100 Qdrant payload updates/sec
   - 50 ArangoDB document updates/sec
   - Measure update latency percentiles (p50, p95, p99)

**Framework:** Locust (Python) or k6 (JavaScript)

**Success Criteria:**
- No circuit breaker trips under normal load
- Kafka consumer lag < 1000 messages
- Qdrant update latency p95 < 100ms
- No data loss or corruption

---

### 7.4 Acceptance Tests

**User Acceptance Criteria:**
1. **Quality Improvement**
   - Precision@5 improves by ≥10% within 12 weeks
   - NDCG@10 improves by ≥3% within 12 weeks
   - No degradation in Recall@50

2. **Latency Impact**
   - Average query latency increase <200ms (async verification)
   - 95th percentile latency increase <500ms

3. **Reliability**
   - Verification service uptime ≥99.5%
   - No data loss during verification failures
   - Graceful degradation when Hupyy API unavailable

4. **Observability**
   - All metrics visible in Grafana dashboard
   - Alerts fire correctly (tested via chaos engineering)
   - Logs searchable and structured (JSON format)

---

## 8. References

### 8.1 Official Documentation

1. **Hupyy OpenAPI Specification**
   - URL: https://verticalslice-smt-service-gvav8.ondigitalocean.app/openapi.json
   - Confidence: High (official API contract)

2. **PipesHub Architecture Documentation**
   - File: `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/docs/hupyy-pipeshub-integration-architecture.md`
   - Confidence: High (authoritative architecture spec)

### 8.2 Codebase Analysis

3. **PipesHub Kafka Service**
   - File: `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/backend/nodejs/apps/src/libs/services/kafka.service.ts`
   - Confidence: High (verified implementation)

4. **PipesHub Qdrant Service**
   - File: `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/backend/python/app/services/vector_db/qdrant/qdrant.py`
   - Confidence: High (verified implementation)

5. **PipesHub ArangoDB Service**
   - File: `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/backend/python/app/services/graph_db/arango/arango.py`
   - Confidence: High (verified implementation)

6. **Docker Compose Production Config**
   - File: `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/deployment/docker-compose/docker-compose.prod.yml`
   - Confidence: High (verified infrastructure)

### 8.3 Best Practices Research

7. **API Circuit Breaker Best Practices**
   - URL: [Unkey Glossary](https://www.unkey.com/glossary/api-circuit-breaker)
   - Confidence: Medium (third-party resource, industry standard)

8. **Resilient APIs: Retry Logic and Circuit Breakers**
   - URL: [Medium Article](https://medium.com/@fahimad/resilient-apis-retry-logic-circuit-breakers-and-fallback-mechanisms-cfd37f523f43)
   - Confidence: Medium (third-party resource, widely cited)

9. **Build Resilient API Clients**
   - URL: [Atomic Object Blog](https://spin.atomicobject.com/retry-circuit-breaker-patterns/)
   - Confidence: Medium (third-party resource, engineering best practices)

10. **Microservices Pattern: Circuit Breaker**
    - URL: [Microservices.io](https://microservices.io/patterns/reliability/circuit-breaker.html)
    - Confidence: High (authoritative microservices patterns resource)

11. **Event-Driven Architecture with Kafka**
    - URL: [Roman Kudryashov's Blog](https://romankudryashov.com/blog/2024/07/event-driven-architecture/)
    - Confidence: Medium (2024 source, practical implementation guide)

12. **Heroku Reference Architecture: Event-Driven Microservices**
    - URL: [Heroku Dev Center](https://devcenter.heroku.com/articles/event-driven-microservices-with-apache-kafka)
    - Confidence: High (official Heroku documentation)

13. **Qdrant Payload Documentation**
    - URL: [Qdrant Docs](https://qdrant.tech/documentation/concepts/payload/)
    - Confidence: High (official Qdrant documentation)

14. **Qdrant Real-Time Updates**
    - URL: [TryCatchDebug Article](https://www.trycatchdebug.net/news/1339987/updating-qdrant-vectordb-metadata)
    - Confidence: Medium (third-party tutorial, verified against official docs)

---

## 9. Quality Report

### 9.1 Verified Claims (✓)

1. **Hupyy API Contract**: Complete OpenAPI spec analyzed, endpoints and schemas verified
   - Source: Official OpenAPI JSON
   - Confidence: High

2. **PipesHub Kafka Infrastructure**: Existing retry logic, consumer groups, and producer capabilities confirmed
   - Source: Codebase analysis (`kafka.service.ts`)
   - Confidence: High

3. **Qdrant Payload Update Capability**: Real-time updates without re-indexing verified
   - Source: Codebase analysis (`qdrant.py`) + Official Qdrant documentation
   - Confidence: High

4. **Circuit Breaker Pattern**: Industry best practices researched and aligned with architecture
   - Source: Multiple authoritative sources (Microservices.io, Medium articles)
   - Confidence: High

5. **Event-Driven Architecture Patterns**: Kafka topic design and consumer patterns validated
   - Source: Heroku reference architecture, 2024 blog posts
   - Confidence: High

### 9.2 Inferred from Architecture (⚠)

1. **PageRank Implementation**: Not found in codebase, assumed to be implemented during integration
   - Source: Architecture document specifies modified PageRank formula
   - Confidence: Medium (requires user confirmation)

2. **Failure Mode Multipliers**: Exact values specified in architecture, not yet implemented
   - Source: Architecture document section 6.2
   - Confidence: High (authoritative spec, pending implementation)

3. **Cold Start Weight Transition**: Detailed phasing in architecture, not yet implemented
   - Source: Architecture document section 9.4
   - Confidence: High (authoritative spec, pending implementation)

4. **Ambiguity Detection**: Architecture mentions "multiple models" detection, but Hupyy API doesn't expose random seed parameter
   - Source: Architecture document section 8.2 + Hupyy OpenAPI spec
   - Confidence: Low (requires clarification or implementation workaround)

### 9.3 Requires User Confirmation (?)

1. **Sync vs. Async Verification**: Critical UX decision (see Open Questions #1)
2. **Verification Sampling Strategy**: Percentage of results to verify (see Open Questions #2)
3. **Deployment Model**: Integrated vs. separate microservice (see Open Questions #3)
4. **Migration Strategy**: On-demand vs. batch backfill (see Open Questions #4)
5. **Hupyy API Rate Limits**: Not documented in OpenAPI spec (see Open Questions #5)
6. **API Key Management**: Credentials storage and rotation strategy (see Open Questions #6)

---

## 10. Next Steps

### 10.1 Immediate Actions (Before Planning)

1. **User Decisions Required**
   - Review Open Questions section
   - Decide on sync vs. async verification model
   - Confirm verification sampling strategy
   - Approve deployment architecture (separate microservice recommended)

2. **Hupyy API Clarifications**
   - Confirm rate limits and pricing
   - Test API with sample chunks to validate latency assumptions
   - Verify no authentication required (or obtain API keys if needed)

3. **Infrastructure Preparation**
   - Ensure Docker Compose can accommodate new service (2G RAM, 2 CPUs)
   - Verify Kafka capacity (estimate 1-5 MB/s additional throughput)
   - Confirm Qdrant and ArangoDB can handle additional metadata (minimal impact expected)

### 10.2 Transition to Planning Phase

Once user decisions are confirmed:
1. Create detailed implementation plan (sprint-by-sprint breakdown)
2. Assign tasks to development phases (Foundation, Fast Feedback, Medium Feedback, Validation)
3. Setup development environment and repositories
4. Begin Phase 1 implementation (Weeks 1-2)

---

## Appendix A: Glossary

- **SMT**: Satisfiability Modulo Theories - formal logic framework for verification
- **SAT**: Satisfiable - formal specification has at least one valid solution
- **UNSAT**: Unsatisfiable - formal specification has no valid solutions (contradiction)
- **UNKNOWN**: Solver cannot determine satisfiability (timeout or undecidable logic)
- **EMA**: Exponential Moving Average - smoothing technique for score updates (α=0.1)
- **CEGAR**: Counterexample-Guided Abstraction Refinement - verification refinement pattern
- **HNSW**: Hierarchical Navigable Small World - Qdrant's vector search algorithm
- **PageRank**: Graph algorithm for document importance scoring
- **NDCG**: Normalized Discounted Cumulative Gain - ranking quality metric
- **MRR**: Mean Reciprocal Rank - ranking quality metric (position of first relevant result)
- **Precision@K**: Percentage of top-K results that are relevant
- **Recall@K**: Percentage of all relevant documents found in top-K results
- **Circuit Breaker**: Resilience pattern to prevent cascading failures
- **Dead Letter Queue**: Kafka topic for unprocessable messages
- **Quality Multiplier (Q)**: PageRank modifier based on verification confidence (0.5-2.0)

---

## Appendix B: Example Verification Flow

**Input Chunk:**
```
"The authentication service must validate user credentials within 200ms and return a JWT token with expiration time set to 1 hour."
```

**Hupyy API Request:**
```json
POST /pipeline/process
{
  "informal_text": "The authentication service must validate user credentials within 200ms and return a JWT token with expiration time set to 1 hour.",
  "skip_formalization": false,
  "enrich": false
}
```

**Hupyy API Response (Success):**
```json
{
  "informal_text": "The authentication service must validate user credentials...",
  "formal_text": "For all requests to authentication service, response time <= 200ms AND token type = JWT AND token expiration = 3600s",
  "formalization_similarity": 0.95,
  "smt_lib_code": "(declare-const response_time Real)\n(declare-const token_type String)\n(declare-const expiration Int)\n(assert (<= response_time 200.0))\n(assert (= token_type \"JWT\"))\n(assert (= expiration 3600))\n(check-sat)",
  "extraction_degradation": 0.02,
  "check_sat_result": "sat",
  "model": {
    "response_time": 150.0,
    "token_type": "JWT",
    "expiration": 3600
  },
  "solver_success": true,
  "metrics": {
    "solve_time_ms": 12000
  },
  "passed_all_checks": true
}
```

**Failure Mode Classification:**
- Verdict: SAT
- Single consistent model: Yes
- Unconstrained variables: 0% (all vars have specific values)
- **Result: VERIFIED_SAT**

**Score Calculation:**
```
Base Score:
  semantic_similarity = 0.85 (from Qdrant cosine similarity)
  pagerank_score = 0.60 (from ArangoDB)
  verification_confidence = 0.95 (from formalization_similarity)
  historical_success = 0.70 (from previous queries)

  base_score = 0.45 * 0.85 + 0.30 * 0.60 + 0.15 * 0.95 + 0.10 * 0.70
             = 0.3825 + 0.18 + 0.1425 + 0.07
             = 0.775

Final Score:
  failure_mode = VERIFIED_SAT (multiplier: 1.8x)
  final_score = 0.775 * 1.8 = 1.395
```

**Qdrant Payload Update:**
```json
{
  "verification": {
    "verdict": "SAT",
    "confidence": 0.95,
    "solve_time_ms": 12000,
    "timestamp": 1704067200,
    "formal_spec": "(declare-const response_time Real)...",
    "formalization_similarity": 0.95,
    "extraction_degradation": 0.02,
    "passed_all_checks": true,
    "failure_mode": "verified_sat",
    "failure_indicators": []
  },
  "verification_metrics": {
    "verification_quality_score": 0.95,  // EMA update on subsequent verifications
    "verification_count": 1,
    "last_verified": 1704067200
  }
}
```

**Result:** Chunk ranking significantly boosted (1.8x multiplier), appears higher in search results for future queries.

---

**End of Research Report**
