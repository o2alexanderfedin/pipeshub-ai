# Hupyy-PipesHub SMT Verification Integration: Phase-by-Phase Implementation Plan

<confidence>High - Based on comprehensive research findings, verified codebase analysis, and established architecture patterns</confidence>

<dependencies>
- Research findings: .prompts/001-hupyy-integration-research/hupyy-integration-research.md
- PipesHub existing infrastructure: Kafka, Qdrant, ArangoDB, MongoDB, Docker Compose
- Hupyy API availability and SLA (99.5%+ uptime assumed)
- Python FastAPI development stack (existing backend)
- Node.js API layer (existing frontend integration)
- User decisions on: service architecture, verification timing, phase priorities
</dependencies>

<open_questions>
1. **Service Architecture Decision**: Deploy as separate microservice container or integrate into existing pipeshub-ai container?
   - **Recommended**: Separate microservice for fault isolation and independent scaling
   - Impact: Phase 0 infrastructure setup complexity

2. **Verification Timing**: Synchronous (blocking) or asynchronous (eventual consistency)?
   - **Recommended**: Asynchronous for better UX (lower latency)
   - Impact: UI must handle "verification in progress" state

3. **Verification Sampling Strategy**: What percentage of search results to verify?
   - **Option A**: All top-50 results (comprehensive, higher API load)
   - **Option B**: Top-10 only (lower cost, faster feedback)
   - **Option C**: Adaptive sampling (10-50 based on query confidence)
   - **Recommended**: Option C (adaptive)

4. **Migration Strategy for Existing Chunks**: On-demand verification or batch backfill?
   - **Recommended**: Hybrid - on-demand for retrieved chunks, batch backfill for frequently accessed docs
   - Impact: Phase 3 data migration timeline

5. **Shadow Mode Duration**: How long to run verification without affecting ranking before full activation?
   - **Recommended**: 2-4 weeks to validate accuracy and performance
   - Impact: Phase 4 timeline

6. **Canary Rollout Percentage**: Gradual rollout percentages per stage?
   - **Recommended**: 5% → 25% → 50% → 100% (1 week per stage)
   - Impact: Phase 5 deployment timeline
</open_questions>

<assumptions>
- Hupyy API maintains 99.5%+ uptime and <30s latency per architecture spec
- PipesHub has capacity for 1-5 MB/s additional Kafka throughput
- Docker Compose environment can allocate 2G RAM + 2 CPUs for verification service
- No Hupyy API rate limits or pricing tiers (requires confirmation)
- Existing Qdrant collections support real-time payload updates without re-indexing
- PageRank algorithm will be implemented as part of integration (not found in current codebase)
- Team has 1-2 engineers available for 16-week implementation timeline
- No breaking changes allowed to existing search API
</assumptions>

---

## Executive Summary

This plan outlines a **6-phase incremental rollout** strategy for integrating Hupyy's SMT verification service into PipesHub's search pipeline. The integration follows an **asynchronous event-driven architecture** using Kafka messaging, with feature flags at every phase to enable safe rollout and instant rollback.

**Key Objectives:**
1. Achieve **98% Precision@5** through formal verification-guided ranking
2. Maintain **<200ms query latency increase** via async verification processing
3. Enable **5-minute rollback** capability at any phase
4. Deliver **incremental value** at each phase (testable, observable, reversible)

**Timeline:** 16 weeks (4 months) from kickoff to full production deployment

**Risk Level:** Medium - Primary risks mitigated through circuit breakers, shadow mode validation, and gradual canary rollout

---

## Phase 0: Infrastructure Setup & Observability (Weeks 1-2)

### Objectives
- Establish monitoring, logging, and alerting infrastructure BEFORE feature development
- Create Kafka topics with appropriate partitioning and retention policies
- Implement feature flag system for progressive enablement
- Setup development environment and CI/CD pipelines
- Capture baseline metrics for quality and performance

### Deliverables

#### 1. Feature Flag System
**Implementation:**
- Add feature flag configuration to MongoDB `config` collection
- Flags to implement:
  ```json
  {
    "verification_enabled": false,           // Master kill switch
    "verification_async": true,              // Async vs sync mode
    "verification_shadow_mode": false,       // Run without affecting ranking
    "verification_sampling_rate": 0.0,       // 0.0-1.0, percentage of queries
    "verification_ranking_weight": 0.0,      // 0.0-0.15, gradual weight increase
    "verification_top_k": 10,                // How many results to verify
    "circuit_breaker_enabled": true,         // Enable circuit breaker
    "verification_rollout_percentage": 0     // 0-100, canary rollout
  }
  ```
- Configuration service integration (Node.js + Python)
- Real-time config refresh via ETCD (already available)

**Files to Create:**
- `/backend/nodejs/apps/src/libs/config/feature-flags.ts`
- `/backend/python/app/config/feature_flags.py`

**Tests:**
- Unit tests for feature flag retrieval
- Integration tests for config changes propagation

---

#### 2. Kafka Topic Creation
**Topics to Create:**

```bash
# Topic 1: verify_chunks
kafka-topics --create \
  --bootstrap-server kafka-1:9092 \
  --topic verify_chunks \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000  # 7 days

# Topic 2: verification_complete
kafka-topics --create \
  --bootstrap-server kafka-1:9092 \
  --topic verification_complete \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=2592000000  # 30 days

# Topic 3: verification_failed
kafka-topics --create \
  --bootstrap-server kafka-1:9092 \
  --topic verification_failed \
  --partitions 1 \
  --replication-factor 1 \
  --config retention.ms=2592000000  # 30 days

# Topic 4: pagerank_recalc
kafka-topics --create \
  --bootstrap-server kafka-1:9092 \
  --topic pagerank_recalc \
  --partitions 1 \
  --replication-factor 1 \
  --config retention.ms=86400000  # 1 day
```

**Verification Script:**
```bash
# List topics to confirm creation
kafka-topics --list --bootstrap-server kafka-1:9092

# Describe topics to verify configuration
kafka-topics --describe --bootstrap-server kafka-1:9092 --topic verify_chunks
```

---

#### 3. Monitoring Infrastructure Setup

**Prometheus Metrics to Expose:**
```python
# Verification service metrics
verification_requests_total = Counter('verification_requests_total', 'Total verification requests', ['status'])
verification_duration_seconds = Histogram('verification_duration_seconds', 'Verification duration')
verification_failure_mode = Counter('verification_failure_mode', 'Verification failures', ['mode'])
circuit_breaker_state = Gauge('circuit_breaker_state', 'Circuit breaker state', ['service'])
kafka_consumer_lag = Gauge('kafka_consumer_lag', 'Kafka consumer lag', ['topic', 'partition'])
qdrant_update_latency = Histogram('qdrant_update_latency_ms', 'Qdrant update latency')
hupyy_api_latency = Histogram('hupyy_api_latency_seconds', 'Hupyy API response time')

# Search quality metrics
search_precision_at_k = Gauge('search_precision_at_k', 'Precision@K metric', ['k'])
search_ndcg = Gauge('search_ndcg', 'NDCG metric', ['k'])
search_mrr = Gauge('search_mrr', 'Mean Reciprocal Rank')
```

**Grafana Dashboards:**
1. **Verification Service Health Dashboard**
   - Circuit breaker state (visual indicator: green/yellow/red)
   - Hupyy API latency (p50, p95, p99)
   - Verification throughput (chunks/sec)
   - Failure mode distribution (pie chart)
   - Kafka consumer lag

2. **Search Quality Metrics Dashboard**
   - Precision@5 trend (target: 98%)
   - NDCG@10 trend
   - Query latency impact (before/after verification)
   - Verification coverage (% of chunks verified)

3. **System Resource Dashboard**
   - Verification service CPU/RAM usage
   - Kafka queue depth
   - Qdrant update latency
   - ArangoDB update latency

**Alert Rules (Prometheus Alertmanager):**
```yaml
# Critical alerts (PagerDuty)
- alert: CircuitBreakerOpen
  expr: circuit_breaker_state{service="hupyy"} == 2
  for: 1m
  annotations:
    summary: "Hupyy API circuit breaker is OPEN"

- alert: SearchQualityDegradation
  expr: (search_precision_at_k{k="5"} - search_precision_at_k{k="5"} offset 1w) < -0.10
  for: 5m
  annotations:
    summary: "Search precision dropped >10% from last week"

- alert: VerificationSuccessRateLow
  expr: rate(verification_requests_total{status="success"}[5m]) / rate(verification_requests_total[5m]) < 0.50
  for: 10m
  annotations:
    summary: "Verification success rate <50%"

# Warning alerts (Slack)
- alert: KafkaConsumerLagHigh
  expr: kafka_consumer_lag > 1000
  for: 5m
  annotations:
    summary: "Kafka consumer lag >1000 messages"

- alert: QdrantUpdateLatencyHigh
  expr: histogram_quantile(0.95, qdrant_update_latency) > 100
  for: 5m
  annotations:
    summary: "Qdrant update latency p95 >100ms"
```

---

#### 4. Baseline Metrics Collection

**Baseline Script (Python):**
```python
# backend/python/scripts/collect_baseline_metrics.py
"""
Collect baseline search quality metrics before verification integration.
Run this for 1 week to establish performance baseline.
"""

import asyncio
from datetime import datetime
from app.modules.retrieval.retrieval_service import RetrievalService
from app.services.vector_db.qdrant.qdrant import QdrantService

async def collect_baseline():
    # Sample 100 random queries from recent search logs
    queries = await get_recent_queries(limit=100)

    metrics = {
        "ndcg@10": [],
        "mrr": [],
        "precision@5": [],
        "recall@50": [],
        "avg_latency_ms": []
    }

    for query in queries:
        start = datetime.now()
        results = await retrieval_service.search(query)
        latency = (datetime.now() - start).total_seconds() * 1000

        # Calculate metrics (requires ground truth labels)
        metrics["avg_latency_ms"].append(latency)
        # ... calculate quality metrics

    # Store baseline in MongoDB
    await store_baseline(metrics)

    print(f"Baseline NDCG@10: {sum(metrics['ndcg@10']) / len(metrics['ndcg@10']):.4f}")
    print(f"Baseline Precision@5: {sum(metrics['precision@5']) / len(metrics['precision@5']):.4f}")
    print(f"Baseline Latency: {sum(metrics['avg_latency_ms']) / len(metrics['avg_latency_ms']):.2f}ms")
```

**Run baseline collection:**
```bash
cd /Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig
python backend/python/scripts/collect_baseline_metrics.py
```

---

### Database Changes
**None** - This phase only creates infrastructure, no schema changes.

### Feature Flags
- All verification flags set to `false` or `0.0`
- Feature flag system operational

### Testing Strategy

**Unit Tests:**
- Feature flag configuration retrieval
- Metrics export format validation
- Alert rule syntax validation

**Integration Tests:**
- Kafka topic creation and message publish/consume
- Prometheus metrics endpoint accessibility
- Grafana dashboard rendering
- Alert firing simulation (chaos testing)

**Manual Verification:**
- Grafana dashboards display correctly
- Alerts route to correct channels (Slack, PagerDuty)
- Feature flags update in real-time via ETCD

### Rollback Plan
**Not applicable** - No production changes, only monitoring infrastructure added.

### Success Criteria
- [ ] All 4 Kafka topics created and verified
- [ ] Feature flag system operational (config updates within 10s)
- [ ] Prometheus scraping metrics every 15s
- [ ] All 3 Grafana dashboards rendering
- [ ] Alert routing verified (test alert to Slack)
- [ ] Baseline metrics collected for 1 week
- [ ] No production impact (monitoring only)

### Estimated Effort
**Medium (2 weeks)** - 1 engineer full-time
- Week 1: Kafka topics, feature flags, Prometheus setup
- Week 2: Grafana dashboards, alert rules, baseline collection

---

## Phase 1: Hupyy Integration Service - Core Verification (Weeks 3-5)

### Objectives
- Build standalone Hupyy Integration Service with API client and resilience patterns
- Implement retry logic, timeout handling, and circuit breaker
- Create Kafka consumer for `verify_chunks` topic
- Implement failure mode classification logic
- Enable **shadow mode** verification (no ranking impact)

### Deliverables

#### 1. Hupyy Integration Service (Separate Microservice)

**Directory Structure:**
```
backend/python/hupyy-verification-service/
├── app/
│   ├── main.py                          # FastAPI application entry point
│   ├── config.py                        # Configuration (env vars, feature flags)
│   ├── api/
│   │   └── routes/
│   │       ├── health.py                # Health check endpoint
│   │       └── admin.py                 # Admin endpoints (circuit breaker reset, stats)
│   ├── services/
│   │   ├── hupyy_client.py              # Hupyy API client with retry/timeout
│   │   ├── circuit_breaker.py           # Circuit breaker implementation
│   │   └── verification_orchestrator.py # Main orchestration logic
│   ├── kafka/
│   │   ├── producer.py                  # Kafka producer for results
│   │   └── consumer.py                  # Kafka consumer for verify_chunks
│   ├── models/
│   │   ├── verification.py              # Pydantic models for verification
│   │   ├── failure_modes.py             # Failure mode enum and classification
│   │   └── hupyy_api.py                 # Hupyy API request/response models
│   └── utils/
│       ├── retry.py                     # Retry decorator utilities
│       ├── metrics.py                   # Prometheus metrics
│       └── logging_config.py            # Structured JSON logging
├── tests/
│   ├── unit/
│   │   ├── test_hupyy_client.py         # Mock Hupyy API tests
│   │   ├── test_failure_classification.py
│   │   └── test_circuit_breaker.py
│   ├── integration/
│   │   ├── test_kafka_flow.py           # End-to-end Kafka integration
│   │   └── test_verification_pipeline.py
│   └── fixtures/
│       └── hupyy_responses.json         # Sample Hupyy API responses
├── Dockerfile
├── pyproject.toml                       # Dependencies (httpx, tenacity, pybreaker, etc.)
└── README.md
```

---

#### 2. Hupyy API Client Implementation

**File:** `app/services/hupyy_client.py`

```python
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from app.config import settings
from app.models.hupyy_api import HupyyRequest, HupyyResponse
from app.services.circuit_breaker import hupyy_circuit_breaker
from app.utils.metrics import (
    hupyy_api_latency,
    hupyy_api_errors,
    circuit_breaker_state_metric
)

class HupyyClient:
    def __init__(self):
        self.base_url = settings.HUPYY_API_URL
        self.timeout = httpx.Timeout(
            connect=5.0,
            read=35.0,
            write=5.0,
            pool=5.0
        )
        self.client = httpx.AsyncClient(timeout=self.timeout)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True
    )
    @hupyy_circuit_breaker
    async def verify_chunk(self, chunk_content: str) -> HupyyResponse:
        """
        Call Hupyy API to verify chunk content.

        Raises:
            httpx.TimeoutException: Request exceeded 35s timeout
            httpx.HTTPStatusError: API returned 422 or 500
            CircuitBreakerError: Circuit breaker is OPEN
        """
        request = HupyyRequest(
            informal_text=chunk_content,
            skip_formalization=False,
            enrich=False
        )

        with hupyy_api_latency.time():
            try:
                response = await self.client.post(
                    f"{self.base_url}/pipeline/process",
                    json=request.dict()
                )
                response.raise_for_status()

                return HupyyResponse(**response.json())

            except httpx.HTTPStatusError as e:
                hupyy_api_errors.labels(status_code=e.response.status_code).inc()

                if e.response.status_code == 422:
                    # Unprocessable Entity - invalid specification (do NOT retry)
                    raise InvalidSpecificationError(e.response.text)
                elif e.response.status_code == 500:
                    # Server error - retryable
                    raise HupyyServiceError(e.response.text)
                else:
                    raise

            except httpx.TimeoutException as e:
                hupyy_api_errors.labels(status_code="timeout").inc()
                raise

    async def close(self):
        await self.client.aclose()
```

---

#### 3. Circuit Breaker Implementation

**File:** `app/services/circuit_breaker.py`

```python
from pybreaker import CircuitBreaker
from app.config import settings
from app.utils.metrics import circuit_breaker_state_metric

class HupyyCircuitBreaker(CircuitBreaker):
    def __init__(self):
        super().__init__(
            fail_max=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,  # 5
            timeout_duration=settings.CIRCUIT_BREAKER_TIMEOUT,     # 60s
            exclude=[InvalidSpecificationError],  # Don't count 422 as failures
            name="hupyy_api"
        )

    def call(self, func, *args, **kwargs):
        # Update metrics on state change
        state_map = {"closed": 0, "half_open": 1, "open": 2}
        circuit_breaker_state_metric.labels(service="hupyy").set(
            state_map.get(self.current_state, -1)
        )

        return super().call(func, *args, **kwargs)

hupyy_circuit_breaker = HupyyCircuitBreaker()
```

---

#### 4. Failure Mode Classification

**File:** `app/models/failure_modes.py`

```python
from enum import Enum
from dataclasses import dataclass
from app.models.hupyy_api import HupyyResponse

class FailureMode(Enum):
    VERIFIED_SAT = ("verified_sat", 1.8)
    INVALID = ("invalid", 0.3)
    AMBIGUOUS = ("ambiguous", 0.7)
    INCOMPLETE = ("incomplete", 0.8)
    TIMEOUT = ("timeout", 0.85)
    THEORY_INCOMPLETE = ("theory_incomplete", 1.0)
    SERVICE_UNAVAILABLE = ("service_unavailable", 1.0)
    NEVER_VERIFIED = ("never_verified", 1.0)

    @property
    def multiplier(self) -> float:
        return self.value[1]

def classify_failure_mode(response: HupyyResponse) -> FailureMode:
    """
    Classify verification result into failure mode based on decision tree.

    Decision tree (from architecture):
    - SAT:
      - Single consistent model → VERIFIED_SAT (1.8x)
      - Multiple models → AMBIGUOUS (0.7x)
      - >50% unconstrained vars → INCOMPLETE (0.8x)
    - UNSAT:
      - Core size ≤3 → INVALID (0.3x)
    - UNKNOWN:
      - Timeout reason → TIMEOUT (0.85x)
      - Quantifier/nonlinear reason → THEORY_INCOMPLETE (1.0x)
    """
    verdict = response.check_sat_result.upper()

    if verdict == "SAT":
        # Check for under-constrained specification
        if response.unconstrained_var_ratio and response.unconstrained_var_ratio > 0.5:
            return FailureMode.INCOMPLETE

        # Check for multiple models (ambiguous)
        # Note: Hupyy API doesn't expose this directly, simplified for now
        # Future: Run multiple solver invocations with different random seeds

        # Single consistent model
        return FailureMode.VERIFIED_SAT

    elif verdict == "UNSAT":
        # Small core = direct contradiction
        if response.unsat_core_size and response.unsat_core_size <= 3:
            return FailureMode.INVALID

        # Large core still problematic
        return FailureMode.INVALID

    elif verdict == "UNKNOWN":
        # Check failure reason
        failure_reason = response.failure_reason or ""

        if "timeout" in failure_reason.lower():
            return FailureMode.TIMEOUT
        elif any(keyword in failure_reason.lower() for keyword in ["quantifier", "nonlinear", "undecidable"]):
            return FailureMode.THEORY_INCOMPLETE
        else:
            # Default to timeout for generic UNKNOWN
            return FailureMode.TIMEOUT

    else:
        # Should never happen
        return FailureMode.NEVER_VERIFIED
```

---

#### 5. Verification Orchestrator

**File:** `app/services/verification_orchestrator.py`

```python
import asyncio
from typing import List
from app.services.hupyy_client import HupyyClient
from app.models.failure_modes import classify_failure_mode, FailureMode
from app.models.verification import VerificationRequest, VerificationResult
from app.kafka.producer import KafkaProducer
from app.utils.metrics import (
    verification_requests_total,
    verification_duration_seconds,
    verification_failure_mode_counter
)

class VerificationOrchestrator:
    def __init__(self):
        self.hupyy_client = HupyyClient()
        self.kafka_producer = KafkaProducer()
        self.max_concurrent = settings.MAX_CONCURRENT_VERIFICATIONS  # 10

    async def verify_chunk(self, request: VerificationRequest) -> VerificationResult:
        """
        Verify a single chunk and return classified result.
        """
        try:
            with verification_duration_seconds.time():
                # Call Hupyy API
                hupyy_response = await self.hupyy_client.verify_chunk(request.content)

                # Classify failure mode
                failure_mode = classify_failure_mode(hupyy_response)

                # Build result
                result = VerificationResult(
                    chunk_id=request.chunk_id,
                    verdict=hupyy_response.check_sat_result,
                    confidence=hupyy_response.formalization_similarity,
                    solve_time_ms=hupyy_response.metrics.solve_time_ms,
                    formal_spec=hupyy_response.smt_lib_code,
                    failure_mode=failure_mode.value[0],
                    multiplier=failure_mode.multiplier,
                    passed_all_checks=hupyy_response.passed_all_checks,
                    metadata=request.metadata
                )

                # Update metrics
                verification_requests_total.labels(status="success").inc()
                verification_failure_mode_counter.labels(mode=failure_mode.value[0]).inc()

                # Publish to Kafka
                await self.kafka_producer.publish_verification_complete(result)

                return result

        except InvalidSpecificationError as e:
            # 422 error - permanent failure
            verification_requests_total.labels(status="invalid").inc()

            result = VerificationResult(
                chunk_id=request.chunk_id,
                verdict="INVALID",
                failure_mode="invalid",
                multiplier=0.3,
                error=str(e)
            )

            await self.kafka_producer.publish_verification_failed(request, str(e))
            return result

        except CircuitBreakerError:
            # Circuit breaker open
            verification_requests_total.labels(status="circuit_open").inc()

            result = VerificationResult(
                chunk_id=request.chunk_id,
                verdict="UNKNOWN",
                failure_mode="service_unavailable",
                multiplier=1.0,  # Neutral - don't penalize for external service failure
                error="Circuit breaker open"
            )

            # Still publish to failed topic for monitoring
            await self.kafka_producer.publish_verification_failed(request, "Circuit breaker open")
            return result

        except Exception as e:
            # Unexpected error
            verification_requests_total.labels(status="error").inc()
            await self.kafka_producer.publish_verification_failed(request, str(e))
            raise

    async def verify_batch(self, requests: List[VerificationRequest]) -> List[VerificationResult]:
        """
        Verify multiple chunks in parallel (up to max_concurrent limit).
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def verify_with_limit(req):
            async with semaphore:
                return await self.verify_chunk(req)

        results = await asyncio.gather(*[verify_with_limit(req) for req in requests])
        return results
```

---

#### 6. Kafka Consumer for verify_chunks

**File:** `app/kafka/consumer.py`

```python
from aiokafka import AIOKafkaConsumer
from app.config import settings
from app.services.verification_orchestrator import VerificationOrchestrator
from app.models.verification import VerificationRequest

class VerifyChunksConsumer:
    def __init__(self):
        self.consumer = AIOKafkaConsumer(
            "verify_chunks",
            bootstrap_servers=settings.KAFKA_BROKERS,
            group_id="verification-orchestrator-group",
            auto_offset_reset="earliest",
            enable_auto_commit=False,  # Manual commit for reliability
            max_poll_records=10  # Batch size
        )
        self.orchestrator = VerificationOrchestrator()

    async def start(self):
        await self.consumer.start()
        logger.info("✅ Kafka consumer started for verify_chunks")

        try:
            async for message in self.consumer:
                # Deserialize message
                request = VerificationRequest(**json.loads(message.value))

                # Verify chunk
                result = await self.orchestrator.verify_chunk(request)

                # Commit offset after successful processing
                await self.consumer.commit()

        finally:
            await self.consumer.stop()
```

---

#### 7. Docker Compose Integration

**Update:** `deployment/docker-compose/docker-compose.prod.yml`

Add new service:

```yaml
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
      - QDRANT_API_KEY=${QDRANT_API_KEY}
      - ARANGO_URL=http://arango:8529
      - ARANGO_USERNAME=root
      - ARANGO_PASSWORD=${ARANGO_PASSWORD}
      - MONGO_URI=mongodb://${MONGO_USERNAME:-admin}:${MONGO_PASSWORD:-password}@mongodb:27017/?authSource=admin
      - LOG_LEVEL=info
      - CIRCUIT_BREAKER_ENABLED=true
      - CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
      - CIRCUIT_BREAKER_TIMEOUT=60
      - MAX_CONCURRENT_VERIFICATIONS=10
      - VERIFICATION_ENABLED=false  # Start disabled
    depends_on:
      kafka-1:
        condition: service_healthy
      qdrant:
        condition: service_healthy
      arango:
        condition: service_healthy
      mongodb:
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
    ports:
      - "8002:8000"  # Expose for debugging
```

---

### Database Changes
**None** - This phase only creates the verification service, no database schema changes yet.

### Feature Flags
Enable for testing:
```json
{
  "verification_enabled": true,
  "verification_shadow_mode": true,  // Run verification but don't affect ranking
  "verification_sampling_rate": 0.01  // 1% of queries for testing
}
```

### Testing Strategy

**Unit Tests:**
- Hupyy API client with mocked responses (200, 422, 500, timeout)
- Retry logic (exponential backoff, max retries)
- Circuit breaker state transitions (closed → open → half-open → closed)
- Failure mode classification (all 8 modes)
- Kafka message serialization/deserialization

**Integration Tests:**
- End-to-end verification flow: Kafka consume → Hupyy API call → Kafka produce
- Circuit breaker integration (trigger open state, verify fallback behavior)
- Concurrent verification (10 parallel requests)
- Error handling (invalid spec, timeout, service unavailable)

**Load Tests:**
- 100 verification requests/minute for 10 minutes
- Monitor: Hupyy API latency, circuit breaker state, Kafka consumer lag
- Target: No circuit breaker trips, consumer lag <100 messages

### Rollback Plan
**Instant Rollback:**
1. Set `verification_enabled = false` in feature flags
2. Stop `hupyy-verification` container: `docker-compose stop hupyy-verification`
3. Kafka messages will accumulate in `verify_chunks` topic (7-day retention)
4. Can resume later without data loss

**Rollback Triggers:**
- Circuit breaker remains OPEN for >10 minutes
- Verification success rate <30%
- Hupyy API latency p95 >60s

### Success Criteria
- [ ] Hupyy Integration Service deployed and healthy
- [ ] Successfully processes 100 test chunks from Kafka
- [ ] Failure mode classification accurate (validated against test dataset)
- [ ] Circuit breaker trips and recovers correctly (chaos test)
- [ ] No crashes or memory leaks after 24h continuous operation
- [ ] Prometheus metrics exporting correctly
- [ ] Shadow mode enabled: verification runs but ranking unchanged

### Estimated Effort
**Large (3 weeks)** - 1-2 engineers
- Week 3: Hupyy client, circuit breaker, failure classification
- Week 4: Verification orchestrator, Kafka integration
- Week 5: Testing (unit, integration, load), Docker deployment

---

## Phase 2: Verification Orchestrator - Event-Driven Coordination (Weeks 6-8)

### Objectives
- Integrate verification trigger into search pipeline (Node.js API layer)
- Implement Kafka producer in Node.js to publish `verify_chunks` events
- Enable adaptive sampling strategy (10-50 results based on query confidence)
- Add verification metadata to Qdrant payload schema (backward compatible)
- Implement Qdrant Updater service to consume `verification_complete` events

### Deliverables

#### 1. Search Pipeline Integration (Node.js)

**File:** `backend/nodejs/apps/src/modules/enterprise_search/services/verification-trigger.service.ts`

```typescript
import { Injectable } from '@nestjs/common';
import { BaseKafkaProducerConnection } from '@libs/services/kafka.service';
import { FeatureFlagService } from '@libs/config/feature-flags.service';

interface VerificationRequest {
  chunk_id: string;
  content: string;
  document_id: string;
  org_id: string;
  user_id: string;
  query_id: string;
  priority: 'high' | 'normal' | 'low';
  timestamp: number;
}

@Injectable()
export class VerificationTriggerService {
  constructor(
    private kafkaProducer: BaseKafkaProducerConnection,
    private featureFlags: FeatureFlagService
  ) {}

  async triggerVerification(
    searchResults: any[],
    queryMetadata: {
      query: string;
      org_id: string;
      user_id: string;
      query_id: string;
    }
  ): Promise<void> {
    // Check if verification is enabled
    const config = await this.featureFlags.getVerificationConfig();

    if (!config.verification_enabled) {
      return; // Verification disabled
    }

    // Adaptive sampling: determine how many results to verify
    const topK = this.determineTopK(config, searchResults);

    // Filter chunks that need verification
    const chunksToVerify = searchResults
      .slice(0, topK)
      .filter(chunk => !this.hasRecentVerification(chunk));

    if (chunksToVerify.length === 0) {
      return; // All chunks already verified
    }

    // Build verification requests
    const requests: VerificationRequest[] = chunksToVerify.map(chunk => ({
      chunk_id: chunk.id,
      content: chunk.content,
      document_id: chunk.document_id,
      org_id: queryMetadata.org_id,
      user_id: queryMetadata.user_id,
      query_id: queryMetadata.query_id,
      priority: this.determinePriority(chunk),
      timestamp: Date.now()
    }));

    // Publish to Kafka (batch)
    await this.kafkaProducer.sendBatch('verify_chunks', requests);

    console.log(`✅ Triggered verification for ${requests.length} chunks`);
  }

  private determineTopK(config: any, results: any[]): number {
    // Adaptive sampling strategy
    const { verification_top_k, verification_sampling_rate } = config;

    // Option A: Fixed top-K (e.g., 10)
    if (verification_sampling_rate === 1.0) {
      return verification_top_k;
    }

    // Option B: Percentage-based sampling
    const sampledK = Math.floor(results.length * verification_sampling_rate);
    return Math.min(sampledK, verification_top_k);
  }

  private hasRecentVerification(chunk: any): boolean {
    // Check if chunk was verified in last 7 days
    const verification = chunk.verification_metrics;

    if (!verification || !verification.last_verified) {
      return false;
    }

    const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
    return verification.last_verified > sevenDaysAgo;
  }

  private determinePriority(chunk: any): 'high' | 'normal' | 'low' {
    // High priority: Never verified OR high semantic similarity
    if (!chunk.verification_metrics || chunk.score > 0.9) {
      return 'high';
    }

    // Low priority: Recently verified AND low similarity
    if (chunk.verification_metrics.last_verified && chunk.score < 0.7) {
      return 'low';
    }

    return 'normal';
  }
}
```

**Integrate into search route:**

```typescript
// backend/nodejs/apps/src/modules/enterprise_search/services/search.service.ts

import { VerificationTriggerService } from './verification-trigger.service';

async search(query: string, filters: any, userId: string, orgId: string): Promise<any> {
  // Existing search logic...
  const results = await this.retrievalService.search(query, filters);

  // Trigger async verification (fire-and-forget)
  const queryId = uuidv4();
  this.verificationTriggerService.triggerVerification(results, {
    query,
    org_id: orgId,
    user_id: userId,
    query_id: queryId
  }).catch(err => {
    // Log error but don't fail search request
    console.error('⚠️ Verification trigger failed:', err);
  });

  // Return results immediately (async verification in background)
  return results;
}
```

---

#### 2. Qdrant Payload Schema Extension

**Extend Qdrant payload structure (backward compatible):**

```python
# backend/python/app/services/vector_db/qdrant/schema.py

from typing import Optional, List
from pydantic import BaseModel

class VerificationMetadata(BaseModel):
    verdict: str  # SAT|UNSAT|UNKNOWN
    confidence: float
    solve_time_ms: int
    timestamp: int
    formal_spec: str
    formalization_similarity: float
    extraction_degradation: float
    passed_all_checks: bool
    failure_mode: str
    failure_indicators: List[str] = []

class VerificationHistory(BaseModel):
    verified_at: int
    verdict: str
    confidence: float
    solver_version: str

class VerificationMetrics(BaseModel):
    verification_count: int = 0
    success_rate: float = 0.0
    avg_confidence: float = 0.0
    last_verified: Optional[int] = None
    verification_quality_score: float = 0.0  # EMA-smoothed score
    temporal_weight: float = 1.0  # exp(-λ × Δt)

class QdrantChunkPayload(BaseModel):
    # Existing fields (unchanged)
    chunk_id: str
    document_id: str
    content: str
    source: str
    position: int
    org_id: str

    # New verification fields (optional, backward compatible)
    verification: Optional[VerificationMetadata] = None
    verification_history: List[VerificationHistory] = []
    verification_metrics: Optional[VerificationMetrics] = None
```

**Create indexes for verification fields:**

```python
# backend/python/scripts/create_verification_indexes.py

from app.services.vector_db.qdrant.qdrant import QdrantService

async def create_verification_indexes():
    qdrant = QdrantService()

    collection_name = "pipeshub_chunks"

    # Index for filtering by verdict
    await qdrant.create_payload_index(
        collection_name=collection_name,
        field_name="verification.verdict",
        field_schema="keyword"
    )

    # Index for filtering by failure mode
    await qdrant.create_payload_index(
        collection_name=collection_name,
        field_name="verification.failure_mode",
        field_schema="keyword"
    )

    # Index for filtering by quality score
    await qdrant.create_payload_index(
        collection_name=collection_name,
        field_name="verification_metrics.verification_quality_score",
        field_schema="float"
    )

    print("✅ Verification indexes created")
```

---

#### 3. Qdrant Updater Service

**File:** `backend/python/hupyy-verification-service/app/services/qdrant_updater.py`

```python
import asyncio
import time
from aiokafka import AIOKafkaConsumer
from app.services.vector_db.qdrant.qdrant import QdrantService
from app.models.verification import VerificationResult
from app.config import settings

class QdrantUpdater:
    def __init__(self):
        self.consumer = AIOKafkaConsumer(
            "verification_complete",
            bootstrap_servers=settings.KAFKA_BROKERS,
            group_id="qdrant-updater-group",
            auto_offset_reset="earliest"
        )
        self.qdrant = QdrantService()
        self.alpha = 0.1  # EMA smoothing factor
        self.lambda_decay = 0.01  # Temporal decay rate (per day)

    async def start(self):
        await self.consumer.start()
        logger.info("✅ Qdrant Updater started")

        try:
            async for message in self.consumer:
                result = VerificationResult(**json.loads(message.value))
                await self.update_chunk_metadata(result)
                await self.consumer.commit()

        finally:
            await self.consumer.stop()

    async def update_chunk_metadata(self, result: VerificationResult):
        """
        Update Qdrant chunk payload with verification results.
        Target latency: <100ms (Fast Feedback Tier 1)
        """
        start_time = time.time()

        # Fetch existing payload
        existing = await self.qdrant.get_payload(
            collection_name="pipeshub_chunks",
            point_id=result.chunk_id
        )

        # Calculate EMA score
        historical_score = existing.get("verification_metrics", {}).get("verification_quality_score", 0.5)
        new_score = self.alpha * result.confidence + (1 - self.alpha) * historical_score

        # Calculate temporal weight (decay over time)
        days_since_last = 0
        if existing.get("verification_metrics", {}).get("last_verified"):
            last_verified = existing["verification_metrics"]["last_verified"]
            days_since_last = (time.time() - last_verified) / 86400

        temporal_weight = math.exp(-self.lambda_decay * days_since_last)

        # Build update payload
        update = {
            "verification": {
                "verdict": result.verdict,
                "confidence": result.confidence,
                "solve_time_ms": result.solve_time_ms,
                "timestamp": int(time.time()),
                "formal_spec": result.formal_spec,
                "formalization_similarity": result.formalization_similarity,
                "extraction_degradation": result.extraction_degradation,
                "passed_all_checks": result.passed_all_checks,
                "failure_mode": result.failure_mode,
                "failure_indicators": result.failure_indicators
            },
            "verification_metrics": {
                "verification_count": existing.get("verification_metrics", {}).get("verification_count", 0) + 1,
                "verification_quality_score": new_score,
                "last_verified": int(time.time()),
                "temporal_weight": temporal_weight
            }
        }

        # Append to verification history (keep last 10)
        verification_history = existing.get("verification_history", [])
        verification_history.append({
            "verified_at": int(time.time()),
            "verdict": result.verdict,
            "confidence": result.confidence,
            "solver_version": "hupyy-v0.1.0"
        })
        update["verification_history"] = verification_history[-10:]  # Keep last 10

        # Update Qdrant
        await self.qdrant.update_payload(
            collection_name="pipeshub_chunks",
            point_id=result.chunk_id,
            payload=update
        )

        # Log latency
        latency_ms = (time.time() - start_time) * 1000
        qdrant_update_latency.observe(latency_ms)

        if latency_ms > 100:
            logger.warning(f"⚠️ Qdrant update latency {latency_ms:.2f}ms exceeded target 100ms")

        logger.debug(f"✅ Updated chunk {result.chunk_id} with verification score {new_score:.4f}")
```

---

### Database Changes

**Qdrant:**
- Add optional `verification`, `verification_history`, `verification_metrics` fields to payload
- Create 3 indexes (verdict, failure_mode, quality_score)
- **Backward compatible**: Existing chunks without verification metadata continue to work

**Migration Script:**
```python
# No migration needed - fields are optional
# Existing chunks will be updated incrementally as they are verified
```

### Feature Flags
```json
{
  "verification_enabled": true,
  "verification_shadow_mode": true,  // Still in shadow mode
  "verification_sampling_rate": 0.05,  // 5% of queries
  "verification_top_k": 10,
  "verification_ranking_weight": 0.0  // Not affecting ranking yet
}
```

### Testing Strategy

**Unit Tests:**
- Verification trigger service (adaptive sampling logic)
- Qdrant updater (EMA calculation, temporal weight decay)
- Payload schema validation (backward compatibility)

**Integration Tests:**
- End-to-end flow: Search → Kafka produce → Hupyy verify → Kafka consume → Qdrant update
- Verify Qdrant payload updated correctly
- Verify search results still return without verification delay (async)
- Test with and without existing verification metadata (backward compatibility)

**Load Tests:**
- 50 search queries/minute for 1 hour
- Monitor: Kafka consumer lag, Qdrant update latency, verification throughput
- Target: Qdrant update latency p95 <100ms, consumer lag <500

### Rollback Plan
**Gradual Rollback:**
1. Reduce `verification_sampling_rate` to 0.01 (1%) or 0 (disabled)
2. If Qdrant performance degrades:
   - Remove verification indexes
   - Stop Qdrant updater service
   - Kafka messages retained for 30 days (can replay later)

**Rollback Triggers:**
- Qdrant update latency p95 >200ms sustained
- Kafka consumer lag >1000 messages for >10 minutes
- Search query latency increased >100ms (should be unchanged due to async)

### Success Criteria
- [ ] Search pipeline triggers verification for 5% of queries
- [ ] Qdrant payloads updated with verification metadata
- [ ] Qdrant update latency p95 <100ms
- [ ] Search query latency unchanged (async verification confirmed)
- [ ] Verification coverage reaches 10% of chunks after 1 week
- [ ] No production search failures or errors

### Estimated Effort
**Large (3 weeks)** - 1-2 engineers
- Week 6: Node.js verification trigger, Kafka producer integration
- Week 7: Qdrant schema extension, Qdrant updater service
- Week 8: Testing (integration, load), monitoring validation

---

## Phase 3: Feedback Integration - ArangoDB & PageRank (Weeks 9-11)

### Objectives
- Extend ArangoDB document schema with verification aggregates
- Implement ArangoDB Updater service to consume `verification_complete` events
- Implement PageRank calculation with verification quality multiplier
- Enable document-level verification metrics
- Continue shadow mode (no ranking impact yet)

### Deliverables

#### 1. ArangoDB Document Schema Extension

**Extend document properties (backward compatible):**

```python
# backend/python/app/services/graph_db/arango/schema.py

from typing import Optional
from pydantic import BaseModel

class VerificationMetricsDoc(BaseModel):
    total_chunks: int = 0
    verified_chunks: int = 0
    verification_rate: float = 0.0  # verified_chunks / total_chunks
    avg_confidence: float = 0.0
    sat_count: int = 0
    unsat_count: int = 0
    unknown_count: int = 0
    last_verification_scan: Optional[int] = None

class QualitySignals(BaseModel):
    quality_score: float = 1.0  # PageRank multiplier (0.5-2.0)
    reliability_class: str = "unverified"  # high|medium|low|unverified

class PageRankData(BaseModel):
    base_pagerank: float = 0.0
    verification_weighted_pagerank: float = 0.0
    quality_multiplier: float = 1.0  # Q(Ti) in formula

class ArangoDocument(BaseModel):
    _key: str
    title: str
    source: str
    author: Optional[str]
    created_at: int

    # New fields (optional, backward compatible)
    verification_metrics: Optional[VerificationMetricsDoc] = None
    quality_signals: Optional[QualitySignals] = None
    pagerank_data: Optional[PageRankData] = None
```

---

#### 2. ArangoDB Updater Service

**File:** `backend/python/hupyy-verification-service/app/services/arango_updater.py`

```python
from aiokafka import AIOKafkaConsumer
from app.services.graph_db.arango.arango import ArangoService
from app.models.verification import VerificationResult
from app.kafka.producer import KafkaProducer

class ArangoUpdater:
    def __init__(self):
        self.consumer = AIOKafkaConsumer(
            "verification_complete",
            bootstrap_servers=settings.KAFKA_BROKERS,
            group_id="arango-updater-group",
            auto_offset_reset="earliest"
        )
        self.arango = ArangoService()
        self.kafka_producer = KafkaProducer()

    async def start(self):
        await self.consumer.start()
        logger.info("✅ ArangoDB Updater started")

        try:
            async for message in self.consumer:
                result = VerificationResult(**json.loads(message.value))
                await self.update_document_metrics(result)
                await self.consumer.commit()

        finally:
            await self.consumer.stop()

    async def update_document_metrics(self, result: VerificationResult):
        """
        Update document-level aggregates based on chunk verification.
        """
        document_id = result.metadata["document_id"]

        # Fetch existing document
        db = self.arango.get_db()
        documents = db.collection('documents')
        doc = documents.get(document_id)

        if not doc:
            logger.warning(f"⚠️ Document {document_id} not found")
            return

        # Update verification counts
        metrics = doc.get('verification_metrics', {
            'total_chunks': 0,
            'verified_chunks': 0,
            'sat_count': 0,
            'unsat_count': 0,
            'unknown_count': 0
        })

        metrics['verified_chunks'] += 1

        if result.verdict == "SAT":
            metrics['sat_count'] += 1
        elif result.verdict == "UNSAT":
            metrics['unsat_count'] += 1
        else:
            metrics['unknown_count'] += 1

        # Recalculate averages (incremental mean)
        n = metrics['verified_chunks']
        old_avg = metrics.get('avg_confidence', 0.0)
        metrics['avg_confidence'] = old_avg + (result.confidence - old_avg) / n

        # Calculate verification rate (need total_chunks from elsewhere)
        # Assumption: total_chunks is set during document indexing
        total = metrics.get('total_chunks', n)
        metrics['verification_rate'] = metrics['verified_chunks'] / total if total > 0 else 0.0

        metrics['last_verification_scan'] = int(time.time())

        # Calculate quality multiplier
        quality_multiplier = self.calculate_quality_multiplier(metrics['avg_confidence'])

        # Update quality signals
        quality_signals = {
            'quality_score': quality_multiplier,
            'reliability_class': self.classify_reliability(metrics['avg_confidence'])
        }

        # Update document
        documents.update({
            '_key': document_id,
            'verification_metrics': metrics,
            'quality_signals': quality_signals
        })

        # Check if significant change (ΔQ > 0.2) → trigger PageRank recalc
        old_multiplier = doc.get('quality_signals', {}).get('quality_score', 1.0)
        if abs(quality_multiplier - old_multiplier) > 0.2:
            logger.info(f"📊 Significant quality change for doc {document_id}: {old_multiplier:.2f} → {quality_multiplier:.2f}")

            # Trigger PageRank recalculation
            await self.kafka_producer.publish_pagerank_trigger({
                'document_id': document_id,
                'old_multiplier': old_multiplier,
                'new_multiplier': quality_multiplier,
                'reason': 'verification_update'
            })

        logger.debug(f"✅ Updated document {document_id} metrics: {metrics}")

    def calculate_quality_multiplier(self, avg_confidence: float) -> float:
        """
        Calculate PageRank quality multiplier Q(Ti).

        Per architecture:
        - avg_conf < 0.5 → Q = 0.5 (penalize low quality)
        - no verification → Q = 1.0 (neutral)
        - avg_conf ≥ 0.5 → Q = 1.0 + avg_conf (boost, max 2.0)
        """
        if avg_confidence is None:
            return 1.0
        elif avg_confidence < 0.5:
            return 0.5
        else:
            return min(1.0 + avg_confidence, 2.0)

    def classify_reliability(self, avg_confidence: float) -> str:
        """Classify document reliability based on verification confidence."""
        if avg_confidence is None:
            return "unverified"
        elif avg_confidence >= 0.8:
            return "high"
        elif avg_confidence >= 0.6:
            return "medium"
        else:
            return "low"
```

---

#### 3. PageRank Calculator Service

**File:** `backend/python/hupyy-verification-service/app/services/pagerank_calculator.py`

```python
import asyncio
from aiokafka import AIOKafkaConsumer
from app.services.graph_db.arango.arango import ArangoService

class PageRankCalculator:
    def __init__(self):
        self.consumer = AIOKafkaConsumer(
            "pagerank_recalc",
            bootstrap_servers=settings.KAFKA_BROKERS,
            group_id="pagerank-calculator-group",
            auto_offset_reset="earliest"
        )
        self.arango = ArangoService()
        self.damping_factor = 0.85  # Standard PageRank damping factor (d)
        self.batch_interval = 3600  # Batch recalculation every hour
        self.pending_docs = set()

    async def start(self):
        await self.consumer.start()
        logger.info("✅ PageRank Calculator started")

        # Start batch processor
        asyncio.create_task(self.batch_processor())

        try:
            async for message in self.consumer:
                trigger = json.loads(message.value)
                self.pending_docs.add(trigger['document_id'])
                await self.consumer.commit()

        finally:
            await self.consumer.stop()

    async def batch_processor(self):
        """
        Batch process PageRank recalculation every hour.
        """
        while True:
            await asyncio.sleep(self.batch_interval)

            if not self.pending_docs:
                logger.debug("⏭️ No pending documents for PageRank recalc")
                continue

            logger.info(f"🔄 Recalculating PageRank for {len(self.pending_docs)} documents")

            # Recalculate PageRank for all documents (global recalculation)
            await self.recalculate_pagerank()

            self.pending_docs.clear()

    async def recalculate_pagerank(self):
        """
        Calculate verification-weighted PageRank for all documents.

        Modified PageRank formula (per architecture):
        PR_v(A) = (1-d)/N + d × Σ(Q(Ti) × PR_v(Ti) / C(Ti))

        Where:
        - d = damping factor (0.85)
        - N = total number of documents
        - Q(Ti) = quality multiplier for document Ti (0.5-2.0)
        - C(Ti) = out-degree of document Ti (number of outgoing links)
        """
        db = self.arango.get_db()
        documents = db.collection('documents')

        # Fetch all documents
        all_docs = [doc for doc in documents.all()]
        N = len(all_docs)

        if N == 0:
            return

        # Build adjacency graph (citation network)
        graph = self.build_citation_graph(all_docs)

        # Initialize PageRank values
        pagerank = {doc['_key']: 1.0 / N for doc in all_docs}

        # Iterative PageRank calculation (power iteration)
        max_iterations = 100
        convergence_threshold = 1e-6

        for iteration in range(max_iterations):
            new_pagerank = {}

            for doc in all_docs:
                doc_id = doc['_key']

                # Base PageRank component: (1-d)/N
                rank = (1 - self.damping_factor) / N

                # Sum contributions from incoming links
                for source_id in graph.get('incoming', {}).get(doc_id, []):
                    source_doc = next(d for d in all_docs if d['_key'] == source_id)

                    # Get quality multiplier Q(Ti)
                    Q = source_doc.get('quality_signals', {}).get('quality_score', 1.0)

                    # Get out-degree C(Ti)
                    C = len(graph.get('outgoing', {}).get(source_id, []))
                    if C == 0:
                        C = 1  # Avoid division by zero

                    # Add contribution: Q(Ti) × PR_v(Ti) / C(Ti)
                    rank += self.damping_factor * (Q * pagerank[source_id] / C)

                new_pagerank[doc_id] = rank

            # Check convergence
            max_diff = max(abs(new_pagerank[doc_id] - pagerank[doc_id]) for doc_id in pagerank)

            pagerank = new_pagerank

            if max_diff < convergence_threshold:
                logger.info(f"✅ PageRank converged after {iteration + 1} iterations")
                break

        # Update ArangoDB with new PageRank values
        for doc in all_docs:
            doc_id = doc['_key']

            # Calculate base PageRank (without verification)
            base_pr = self.calculate_base_pagerank(doc_id, all_docs, graph)

            documents.update({
                '_key': doc_id,
                'pagerank_data': {
                    'base_pagerank': base_pr,
                    'verification_weighted_pagerank': pagerank[doc_id],
                    'quality_multiplier': doc.get('quality_signals', {}).get('quality_score', 1.0)
                }
            })

        logger.info(f"✅ PageRank recalculated for {N} documents")

    def build_citation_graph(self, documents):
        """
        Build citation network from document metadata.

        Note: Assumes citation data exists in ArangoDB.
        If not, this will be implemented as part of integration.
        """
        graph = {
            'outgoing': {},  # doc_id → [cited_doc_ids]
            'incoming': {}   # doc_id → [citing_doc_ids]
        }

        for doc in documents:
            doc_id = doc['_key']
            citations = doc.get('citations', [])

            graph['outgoing'][doc_id] = citations

            for cited_id in citations:
                if cited_id not in graph['incoming']:
                    graph['incoming'][cited_id] = []
                graph['incoming'][cited_id].append(doc_id)

        return graph

    def calculate_base_pagerank(self, doc_id, all_docs, graph):
        """
        Calculate base PageRank without verification (Q = 1.0 for all).
        Used for comparison metrics.
        """
        # Simplified calculation (same formula with Q = 1.0)
        # Implementation omitted for brevity
        return 1.0 / len(all_docs)
```

---

### Database Changes

**ArangoDB:**
- Add optional `verification_metrics`, `quality_signals`, `pagerank_data` fields to documents
- **Backward compatible**: Existing documents without verification continue to work
- No migration needed - fields added incrementally during verification

### Feature Flags
```json
{
  "verification_enabled": true,
  "verification_shadow_mode": true,  // Still in shadow mode
  "verification_sampling_rate": 0.10,  // Increase to 10%
  "verification_ranking_weight": 0.0  // Not affecting ranking yet
}
```

### Testing Strategy

**Unit Tests:**
- ArangoDB updater (aggregate calculation, quality multiplier)
- PageRank calculator (modified formula, convergence)
- Citation graph construction

**Integration Tests:**
- End-to-end flow: Verification → Qdrant update → ArangoDB update → PageRank trigger
- Verify document metrics updated correctly
- Verify PageRank recalculation triggered on significant quality change
- Test with documents that have citations vs. no citations

**Performance Tests:**
- PageRank calculation for 1000 documents
- Measure convergence time (target: <60s for 1000 docs)
- Monitor ArangoDB query performance

### Rollback Plan
**Gradual Rollback:**
1. Stop ArangoDB updater and PageRank calculator services
2. Kafka messages retained for 30 days
3. Document metadata remains (no harm, just unused)
4. Can resume later without data loss

**Rollback Triggers:**
- PageRank calculation takes >5 minutes
- ArangoDB performance degrades (query latency >500ms)

### Success Criteria
- [ ] ArangoDB documents updated with verification aggregates
- [ ] PageRank recalculation completes within 60s for full corpus
- [ ] Quality multipliers correctly applied (Q range: 0.5-2.0)
- [ ] Verification coverage reaches 30% of documents after 1 week
- [ ] No ArangoDB performance degradation

### Estimated Effort
**Large (3 weeks)** - 1-2 engineers
- Week 9: ArangoDB schema extension, ArangoDB updater service
- Week 10: PageRank calculator implementation
- Week 11: Testing (integration, performance), validation

---

## Phase 4: Enhanced Ranking with Verification Scores (Weeks 12-13)

### Objectives
- Integrate verification scores into search ranking formula
- Implement gradual weight transition (0% → 15% over 2 weeks)
- Enable A/B testing framework
- **Exit shadow mode**: Verification scores affect ranking
- Monitor quality metrics (Precision@5, NDCG@10)

### Deliverables

#### 1. Ranking Formula Integration

**File:** `backend/python/app/modules/retrieval/ranking/verification_ranking.py`

```python
from typing import List, Dict
from app.config.feature_flags import get_verification_config

class VerificationRanker:
    def __init__(self):
        self.config = get_verification_config()

    def calculate_final_score(
        self,
        semantic_similarity: float,
        pagerank_score: float,
        verification_confidence: float,
        historical_success: float,
        failure_mode_multiplier: float
    ) -> float:
        """
        Calculate weighted base score with verification.

        Weights (from architecture):
        - Semantic: 45%
        - PageRank: 30%
        - Verification: 15% (gradually increased from 0%)
        - Historical: 10%

        Final score = base_score × failure_mode_multiplier
        """
        # Get current verification weight (gradual transition)
        verification_weight = self.config['verification_ranking_weight']

        # Adjust other weights proportionally if verification weight < 15%
        if verification_weight < 0.15:
            # Redistribute weight from semantic similarity
            semantic_weight = 0.45 + (0.15 - verification_weight)
            pagerank_weight = 0.30
            historical_weight = 0.10
        else:
            # Final weights
            semantic_weight = 0.45
            pagerank_weight = 0.30
            verification_weight = 0.15
            historical_weight = 0.10

        # Calculate base score
        base_score = (
            semantic_weight * semantic_similarity +
            pagerank_weight * pagerank_score +
            verification_weight * verification_confidence +
            historical_weight * historical_success
        )

        # Apply failure mode multiplier
        final_score = base_score * failure_mode_multiplier

        return final_score

    def rank_results(self, results: List[Dict]) -> List[Dict]:
        """
        Re-rank search results with verification scores.
        """
        for result in results:
            # Extract scores
            semantic_similarity = result.get('score', 0.0)  # From Qdrant cosine similarity

            pagerank_score = result.get('pagerank_data', {}).get('verification_weighted_pagerank', 0.0)

            verification_confidence = result.get('verification_metrics', {}).get('verification_quality_score', 0.5)

            historical_success = result.get('historical_success', 0.5)  # From user feedback/clicks

            failure_mode_multiplier = self.get_failure_mode_multiplier(result)

            # Calculate final score
            final_score = self.calculate_final_score(
                semantic_similarity,
                pagerank_score,
                verification_confidence,
                historical_success,
                failure_mode_multiplier
            )

            result['final_score'] = final_score
            result['ranking_breakdown'] = {
                'semantic': semantic_similarity,
                'pagerank': pagerank_score,
                'verification': verification_confidence,
                'historical': historical_success,
                'failure_multiplier': failure_mode_multiplier
            }

        # Sort by final score (descending)
        results.sort(key=lambda x: x['final_score'], reverse=True)

        return results

    def get_failure_mode_multiplier(self, result: Dict) -> float:
        """
        Get failure mode multiplier from verification metadata.
        """
        verification = result.get('verification', {})

        if not verification:
            return 1.0  # Neutral for unverified chunks

        failure_mode = verification.get('failure_mode', 'never_verified')

        # Multiplier mapping (from architecture)
        multipliers = {
            'verified_sat': 1.8,
            'invalid': 0.3,
            'ambiguous': 0.7,
            'incomplete': 0.8,
            'timeout': 0.85,
            'theory_incomplete': 1.0,
            'service_unavailable': 1.0,
            'never_verified': 1.0
        }

        return multipliers.get(failure_mode, 1.0)
```

**Integrate into retrieval service:**

```python
# backend/python/app/modules/retrieval/retrieval_service.py

from app.modules.retrieval.ranking.verification_ranking import VerificationRanker

class RetrievalService:
    def __init__(self):
        self.verification_ranker = VerificationRanker()

    async def search_with_filters(self, queries, org_id, user_id, limit, filter_groups, arango_service, knowledge_search=True):
        # Existing retrieval logic...
        results = await self.qdrant_service.search(queries, limit=100)

        # Apply reranking (existing cross-encoder)
        reranked = await self.reranker.rerank(results, queries)

        # Apply verification ranking (NEW)
        config = await get_verification_config()

        if config['verification_enabled'] and not config['verification_shadow_mode']:
            # Verification affects ranking
            reranked = self.verification_ranker.rank_results(reranked)

        # Return top K
        return reranked[:limit]
```

---

#### 2. Gradual Weight Transition

**Implementation:**

```python
# backend/python/scripts/gradual_weight_transition.py
"""
Gradually increase verification_ranking_weight from 0% to 15% over 2 weeks.
Run this script daily via cron job.
"""

import asyncio
from datetime import datetime, timedelta
from app.config.feature_flags import update_verification_config

async def update_verification_weight():
    config = await get_verification_config()

    # Define transition schedule
    start_date = datetime(2025, 1, 1)  # Phase 4 start date
    end_date = start_date + timedelta(days=14)  # 2 weeks
    current_date = datetime.now()

    if current_date < start_date:
        # Not started yet
        target_weight = 0.0
    elif current_date >= end_date:
        # Fully ramped up
        target_weight = 0.15
    else:
        # Linear ramp-up
        days_elapsed = (current_date - start_date).days
        target_weight = 0.15 * (days_elapsed / 14.0)

    # Update config
    await update_verification_config({
        'verification_ranking_weight': target_weight
    })

    print(f"✅ Updated verification_ranking_weight to {target_weight:.4f}")

if __name__ == "__main__":
    asyncio.run(update_verification_weight())
```

**Cron job (run daily):**
```bash
0 0 * * * cd /app && python scripts/gradual_weight_transition.py
```

---

#### 3. A/B Testing Framework

**File:** `backend/nodejs/apps/src/libs/services/ab-testing.service.ts`

```typescript
import { Injectable } from '@nestjs/common';

@Injectable()
export class ABTestingService {
  /**
   * Determine if user should see verification-enhanced ranking.
   *
   * Uses consistent hashing to ensure same user always in same group.
   */
  isInVerificationGroup(userId: string, rolloutPercentage: number): boolean {
    // Hash user ID to number 0-99
    const hash = this.hashUserId(userId);

    // User is in treatment group if hash < rolloutPercentage
    return hash < rolloutPercentage;
  }

  private hashUserId(userId: string): number {
    // Simple hash function (consistent for same userId)
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      hash = ((hash << 5) - hash) + userId.charCodeAt(i);
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash) % 100;
  }
}
```

**Integrate into search service:**

```typescript
// backend/nodejs/apps/src/modules/enterprise_search/services/search.service.ts

import { ABTestingService } from '@libs/services/ab-testing.service';

async search(query: string, filters: any, userId: string): Promise<any> {
  const config = await this.featureFlags.getVerificationConfig();

  // Determine if user is in verification group
  const inVerificationGroup = this.abTestingService.isInVerificationGroup(
    userId,
    config.verification_rollout_percentage
  );

  // Pass flag to Python retrieval service
  const results = await this.retrievalService.search(query, filters, {
    useVerificationRanking: inVerificationGroup && config.verification_enabled
  });

  return results;
}
```

---

### Database Changes
**None** - Only ranking logic changes, no schema modifications.

### Feature Flags
```json
{
  "verification_enabled": true,
  "verification_shadow_mode": false,  // EXIT shadow mode
  "verification_sampling_rate": 0.20,  // Increase to 20%
  "verification_ranking_weight": 0.0,  // Gradually increase to 0.15 over 2 weeks
  "verification_rollout_percentage": 10  // Start with 10% of users
}
```

### Testing Strategy

**Unit Tests:**
- Ranking formula calculation (all weight combinations)
- Failure mode multiplier application
- A/B testing hash consistency (same user always same group)

**Integration Tests:**
- End-to-end search with verification ranking
- Verify score breakdown returned in response
- Test gradual weight transition (mock date changes)

**A/B Testing:**
- Split traffic: 10% verification group, 90% control
- Collect metrics: Precision@5, NDCG@10, user engagement (click-through rate)
- Compare groups after 1 week
- Target: Verification group shows +10% Precision@5 improvement

**Load Tests:**
- 100 search queries/minute for 1 hour
- Monitor: Ranking latency, search quality metrics
- Target: Ranking adds <10ms latency

### Rollback Plan
**Instant Rollback (Emergency):**
1. Set `verification_shadow_mode = true` (disables ranking impact)
2. OR set `verification_ranking_weight = 0.0` (removes weight)
3. Rollback takes effect immediately (config refresh <10s)

**Gradual Rollback:**
1. Reduce `verification_rollout_percentage` from 10% → 5% → 0%
2. Monitor metrics at each step
3. Full rollback if Precision@5 drops >5%

**Rollback Triggers:**
- Precision@5 drops >5% compared to baseline
- NDCG@10 drops >3%
- User complaints spike (qualitative signal)
- Ranking latency >100ms p95

### Success Criteria
- [ ] Verification ranking enabled for 10% of users
- [ ] Precision@5 improves by ≥5% in verification group (A/B test)
- [ ] NDCG@10 improves by ≥2% in verification group
- [ ] Ranking latency impact <10ms
- [ ] Gradual weight transition completes (0% → 15% over 2 weeks)
- [ ] No production incidents or rollbacks

### Estimated Effort
**Medium (2 weeks)** - 1-2 engineers
- Week 12: Ranking formula integration, A/B testing framework
- Week 13: Gradual weight transition, monitoring, validation

---

## Phase 5: Canary Rollout & Optimization (Weeks 14-16)

### Objectives
- Gradual rollout to 100% of users (5% → 25% → 50% → 100%)
- Optimize verification throughput and cost
- Implement cold start backfill strategy
- Monitor and optimize feedback loop stability
- Achieve 98% Precision@5 target

### Deliverables

#### 1. Canary Rollout Strategy

**Rollout Schedule:**

```
Week 14:
  Day 1-2: 5% of users (validation)
  Day 3-4: 25% of users
  Day 5-7: 50% of users

Week 15:
  Day 1-3: 75% of users
  Day 4-7: 100% of users (full rollout)

Week 16:
  Monitoring and optimization
```

**Rollout Script:**

```python
# backend/python/scripts/canary_rollout.py
"""
Gradual rollout of verification to all users.
Manual execution at each milestone.
"""

import asyncio
from app.config.feature_flags import update_verification_config

async def rollout_to_percentage(percentage: int):
    print(f"🚀 Rolling out verification to {percentage}% of users...")

    await update_verification_config({
        'verification_rollout_percentage': percentage
    })

    print(f"✅ Rollout complete. Monitor metrics for 24-48 hours before next stage.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python canary_rollout.py <percentage>")
        sys.exit(1)

    percentage = int(sys.argv[1])

    if percentage not in [5, 25, 50, 75, 100]:
        print("❌ Invalid percentage. Use: 5, 25, 50, 75, or 100")
        sys.exit(1)

    asyncio.run(rollout_to_percentage(percentage))
```

**Execution:**
```bash
# Week 14, Day 1
python scripts/canary_rollout.py 5

# Week 14, Day 3 (after monitoring)
python scripts/canary_rollout.py 25

# Week 14, Day 5
python scripts/canary_rollout.py 50

# Week 15, Day 1
python scripts/canary_rollout.py 75

# Week 15, Day 4
python scripts/canary_rollout.py 100
```

---

#### 2. Cold Start Backfill Strategy

**Objective:** Verify frequently accessed chunks to improve coverage.

**File:** `backend/python/scripts/cold_start_backfill.py`

```python
"""
Backfill verification for unverified chunks.
Prioritize:
1. Frequently retrieved chunks (high access count)
2. High uncertainty chunks (low semantic similarity in recent queries)
3. Random exploration (20% budget)
"""

import asyncio
from app.services.vector_db.qdrant.qdrant import QdrantService
from app.kafka.producer import KafkaProducer

async def backfill_verification():
    qdrant = QdrantService()
    kafka_producer = KafkaProducer()

    # Find unverified chunks
    unverified_chunks = await qdrant.scroll(
        collection_name="pipeshub_chunks",
        scroll_filter={
            "must_not": [
                {"key": "verification_metrics.last_verified", "match": {"any": True}}
            ]
        },
        limit=1000  # Process 1000 chunks per batch
    )

    if not unverified_chunks:
        print("✅ All chunks verified!")
        return

    # Prioritize by access count (fetch from analytics DB)
    # Simplified: assume access_count is in payload
    chunks_by_priority = sorted(
        unverified_chunks,
        key=lambda c: c.payload.get('access_count', 0),
        reverse=True
    )

    # Add 20% random exploration
    num_exploration = int(len(chunks_by_priority) * 0.2)
    random_chunks = random.sample(unverified_chunks, num_exploration)

    # Combine prioritized + random
    chunks_to_verify = chunks_by_priority[:800] + random_chunks[:200]

    # Publish to Kafka
    for chunk in chunks_to_verify:
        await kafka_producer.publish_verify_chunk({
            'chunk_id': chunk.id,
            'content': chunk.payload['content'],
            'document_id': chunk.payload['document_id'],
            'priority': 'low'  # Background job
        })

    print(f"📤 Queued {len(chunks_to_verify)} chunks for backfill verification")

if __name__ == "__main__":
    asyncio.run(backfill_verification())
```

**Cron job (run daily during off-peak hours):**
```bash
0 2 * * * cd /app && python scripts/cold_start_backfill.py
```

---

#### 3. Feedback Loop Stability Monitoring

**File:** `backend/python/scripts/monitor_feedback_loop.py`

```python
"""
Monitor feedback loop health metrics:
- Coverage: % of docs with ≥5 verified chunks
- Diversity: Shannon entropy of verification distribution
- Query drift: ||Q_new - Q_orig||
- Exploration rate: % random exploration
"""

import asyncio
from app.services.vector_db.qdrant.qdrant import QdrantService
from app.services.graph_db.arango.arango import ArangoService
from app.utils.metrics import (
    feedback_coverage,
    feedback_diversity_entropy,
    feedback_query_drift,
    feedback_exploration_rate
)

async def monitor_feedback_health():
    qdrant = QdrantService()
    arango = ArangoService()

    # Calculate coverage
    db = arango.get_db()
    documents = db.collection('documents')

    total_docs = documents.count()
    docs_with_coverage = sum(
        1 for doc in documents.all()
        if doc.get('verification_metrics', {}).get('verified_chunks', 0) >= 5
    )

    coverage = docs_with_coverage / total_docs if total_docs > 0 else 0.0
    feedback_coverage.set(coverage)

    # Calculate diversity (Shannon entropy)
    failure_mode_counts = await get_failure_mode_distribution(qdrant)
    entropy = calculate_shannon_entropy(failure_mode_counts)
    feedback_diversity_entropy.set(entropy)

    # Calculate query drift (compare queries this week vs. last week)
    # Requires query log analysis
    drift = await calculate_query_drift()
    feedback_query_drift.set(drift)

    # Log health status
    print(f"📊 Feedback Loop Health:")
    print(f"  Coverage: {coverage:.2%} (target: >80%)")
    print(f"  Diversity: {entropy:.2f} bits (target: ≥3.0)")
    print(f"  Query Drift: {drift:.4f} (limit: <0.3)")

    # Alert if unhealthy
    if coverage < 0.80:
        print("⚠️ Coverage below target!")
    if entropy < 3.0:
        print("⚠️ Diversity below target! Increase exploration rate.")
    if drift > 0.3:
        print("⚠️ Query drift exceeds limit! Reduce feedback weight.")

async def get_failure_mode_distribution(qdrant):
    # Query Qdrant for failure mode counts
    # Simplified implementation
    return {
        'verified_sat': 450,
        'invalid': 50,
        'ambiguous': 100,
        'incomplete': 100,
        'timeout': 50,
        'theory_incomplete': 50
    }

def calculate_shannon_entropy(counts):
    total = sum(counts.values())
    entropy = 0.0

    for count in counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    return entropy

if __name__ == "__main__":
    asyncio.run(monitor_feedback_health())
```

---

#### 4. Cost Optimization

**Strategies:**
1. **Caching:** Cache verification results for identical chunks (deduplication)
2. **Rate limiting:** Limit Hupyy API calls to budget (e.g., 10,000 verifications/day)
3. **Adaptive sampling:** Reduce verification for low-priority chunks

**File:** `backend/python/hupyy-verification-service/app/services/cache.py`

```python
from redis import asyncio as aioredis
import hashlib

class VerificationCache:
    def __init__(self):
        self.redis = aioredis.from_url("redis://redis:6379")
        self.ttl = 30 * 24 * 60 * 60  # 30 days

    def get_cache_key(self, content: str) -> str:
        """Generate cache key from content hash."""
        return f"verification:{hashlib.sha256(content.encode()).hexdigest()}"

    async def get(self, content: str) -> Optional[VerificationResult]:
        """Retrieve cached verification result."""
        key = self.get_cache_key(content)
        data = await self.redis.get(key)

        if data:
            return VerificationResult(**json.loads(data))
        return None

    async def set(self, content: str, result: VerificationResult):
        """Cache verification result."""
        key = self.get_cache_key(content)
        await self.redis.setex(key, self.ttl, result.json())
```

**Integrate into orchestrator:**
```python
async def verify_chunk(self, request: VerificationRequest) -> VerificationResult:
    # Check cache first
    cached_result = await self.cache.get(request.content)
    if cached_result:
        logger.info(f"✅ Cache hit for chunk {request.chunk_id}")
        verification_requests_total.labels(status="cache_hit").inc()
        return cached_result

    # Call Hupyy API (existing logic)
    result = await self.hupyy_client.verify_chunk(request.content)

    # Cache result
    await self.cache.set(request.content, result)

    return result
```

---

### Database Changes
**None** - Only optimization and monitoring enhancements.

### Feature Flags
```json
{
  "verification_enabled": true,
  "verification_shadow_mode": false,
  "verification_sampling_rate": 0.30,  // Increase to 30%
  "verification_ranking_weight": 0.15,  // Full weight
  "verification_rollout_percentage": 100  // Full rollout by end of week 15
}
```

### Testing Strategy

**Canary Testing:**
- Monitor metrics at each rollout percentage (5%, 25%, 50%, 75%, 100%)
- Compare: Precision@5, NDCG@10, query latency, error rate
- Halt rollout if any metric degrades >5%

**Load Testing:**
- Simulate peak load: 200 queries/minute for 2 hours
- Monitor: Verification throughput, Kafka lag, circuit breaker state
- Target: No service degradation

**Cost Analysis:**
- Track Hupyy API call volume and cost
- Measure cache hit rate (target: >40%)
- Optimize sampling rate to stay within budget

### Rollback Plan
**Gradual Rollback:**
1. Reduce `verification_rollout_percentage` to previous stage
2. If issues persist, reduce to 0% (disable for all users)
3. Investigate and fix issues
4. Resume rollout after validation

**Rollback Triggers (Automated):**
- Precision@5 drops >5% for any rollout cohort
- Error rate >1% for verification service
- Circuit breaker remains open >15 minutes

### Success Criteria
- [ ] 100% of users on verification-enhanced ranking
- [ ] Precision@5 ≥ 98% (target achieved)
- [ ] NDCG@10 ≥ 0.75 (10-point improvement from baseline)
- [ ] Verification coverage ≥ 80% of documents
- [ ] Feedback loop stable (coverage >80%, diversity >3.0 bits, drift <0.3)
- [ ] Cache hit rate ≥ 40% (cost optimization)
- [ ] No production incidents during rollout

### Estimated Effort
**Large (3 weeks)** - 1-2 engineers
- Week 14: Canary rollout (5% → 50%), monitoring
- Week 15: Full rollout (100%), cold start backfill
- Week 16: Optimization, feedback loop tuning, final validation

---

## Critical Path & Dependencies

### Phase Dependencies

```
Phase 0 (Weeks 1-2): Infrastructure
  ↓
Phase 1 (Weeks 3-5): Hupyy Integration Service
  ↓ (depends on Kafka topics)
Phase 2 (Weeks 6-8): Verification Orchestrator
  ↓ (depends on Hupyy service)
Phase 3 (Weeks 9-11): ArangoDB & PageRank
  ↓ (parallel with Phase 2, depends on verification data)
Phase 4 (Weeks 12-13): Enhanced Ranking
  ↓ (depends on Phase 2 + 3)
Phase 5 (Weeks 14-16): Canary Rollout
  (depends on Phase 4)
```

**Critical Path:**
Phase 0 → Phase 1 → Phase 2 → Phase 4 → Phase 5 (16 weeks total)

**Phase 3 can partially overlap with Phase 2** (weeks 8-11) to compress timeline.

### External Dependencies
1. **Hupyy API availability**: Uptime ≥99.5%, latency <30s
2. **Infrastructure capacity**: Docker Compose can allocate 2G RAM + 2 CPUs
3. **Team bandwidth**: 1-2 engineers full-time for 16 weeks
4. **User decisions**: Service architecture, verification timing, sampling strategy (Phase 0)

---

## Data Migration Plan

### Existing Chunks (Cold Start Problem)

**Strategy:** Gradual on-demand verification + batch backfill

**Timeline:**
- **Weeks 1-4 (Phase 0-1):** No migration needed (shadow mode, testing only)
- **Weeks 5-8 (Phase 2):** Incremental verification as chunks are retrieved
  - Expected coverage: 10-20% of chunks after 3 weeks
- **Weeks 9-16 (Phase 3-5):** Batch backfill for frequently accessed chunks
  - Daily backfill job (2am cron)
  - Target: 80% coverage by week 16

**Migration Script:** `cold_start_backfill.py` (see Phase 5)

**Rollback:** No data deletion required. Unverified chunks continue to work with neutral multiplier (1.0x).

---

## Monitoring & Observability

### Key Metrics to Monitor

**System Health:**
- Circuit breaker state (Hupyy API)
- Kafka consumer lag (all topics)
- Qdrant update latency (p95 <100ms)
- ArangoDB query latency (p95 <500ms)
- Verification service CPU/RAM usage

**Search Quality:**
- Precision@5 (target: 98%)
- NDCG@10 (target: 0.75)
- MRR (Mean Reciprocal Rank)
- Recall@50

**Verification Metrics:**
- Verification success rate (target: >50%)
- Failure mode distribution
- Hupyy API latency (p50, p95, p99)
- Verification coverage (% of chunks verified)

**Feedback Loop Health:**
- Coverage (% of docs with ≥5 verified chunks, target: >80%)
- Diversity (Shannon entropy, target: ≥3.0 bits)
- Query drift (||Q_new - Q_orig||, limit: <0.3)
- Exploration rate (target: 10-15%)

**Cost Metrics:**
- Hupyy API call volume (daily)
- Cache hit rate (target: >40%)
- Verification cost per query

### Alert Thresholds

**CRITICAL (PagerDuty):**
- Circuit breaker open >10 minutes
- Precision@5 drops >10% from baseline
- Verification success rate <30%
- Kafka consumer lag >5000 messages

**WARNING (Slack):**
- Qdrant update latency p95 >100ms
- Feedback diversity <3.0 bits
- Query drift >0.3
- Kafka consumer lag >1000 messages

**INFO (Dashboard):**
- Verification success rate change >5% week-over-week
- New failure mode detected

---

## Rollback Procedures

### Emergency Rollback (Instant - <5 minutes)

**Trigger:** Critical production issue (Precision drop >10%, service outage, etc.)

**Procedure:**
1. Update feature flags in MongoDB:
   ```json
   {
     "verification_enabled": false
   }
   ```
2. Config propagates via ETCD within 10 seconds
3. Search reverts to pre-verification ranking
4. Verification service can be stopped: `docker-compose stop hupyy-verification`

**Verification:** Search quality returns to baseline within 1 minute.

---

### Gradual Rollback (Controlled - 1-3 days)

**Trigger:** Non-critical issue (quality degradation <10%, cost overrun, etc.)

**Procedure:**
1. Reduce rollout percentage:
   ```json
   {
     "verification_rollout_percentage": 50  // Reduce from 100%
   }
   ```
2. Monitor metrics for 24 hours
3. If issue persists, reduce further: 25% → 10% → 0%
4. Investigate root cause in isolated environment
5. Fix and re-deploy
6. Resume rollout

---

### Phase-Specific Rollback

**Phase 1 Rollback:**
- Stop `hupyy-verification` container
- Kafka messages retained for 7 days (can resume later)

**Phase 2 Rollback:**
- Set `verification_sampling_rate = 0.0`
- Stop Qdrant updater
- Existing verification metadata remains (harmless)

**Phase 3 Rollback:**
- Stop ArangoDB updater and PageRank calculator
- Document metadata remains (unused)

**Phase 4 Rollback:**
- Set `verification_shadow_mode = true` OR `verification_ranking_weight = 0.0`
- Ranking reverts to pre-verification formula

**Phase 5 Rollback:**
- Reduce `verification_rollout_percentage` to safe level
- Full rollback: set to 0%

---

## Success Metrics

### Per-Phase Metrics

**Phase 0:**
- Infrastructure healthy (all services green in Grafana)
- Baseline metrics collected (1 week of data)

**Phase 1:**
- Verification success rate >50%
- Circuit breaker functional (tested via chaos engineering)
- No Hupyy API errors >5%

**Phase 2:**
- Qdrant update latency p95 <100ms
- Verification coverage 10% after 1 week
- Search query latency unchanged (async verification confirmed)

**Phase 3:**
- ArangoDB document metrics updated correctly
- PageRank recalculation completes <60s
- Verification coverage 30% after 1 week

**Phase 4:**
- Precision@5 improves ≥5% in A/B test
- NDCG@10 improves ≥2%
- Ranking latency impact <10ms

**Phase 5:**
- 100% rollout achieved
- Precision@5 ≥ 98% (target)
- NDCG@10 ≥ 0.75
- Verification coverage ≥ 80%

### Overall Success Criteria

- [ ] **Precision@5 = 98%** (primary target)
- [ ] NDCG@10 ≥ 0.75 (10-point improvement)
- [ ] Query latency increase <200ms average
- [ ] Verification coverage ≥ 80% of documents
- [ ] Feedback loop stable (coverage >80%, diversity >3.0, drift <0.3)
- [ ] No production incidents or rollbacks during deployment
- [ ] Cost within budget (<$X per month, to be defined)
- [ ] Uptime ≥ 99.9% (existing SLA maintained)

---

## Appendices

### Appendix A: File Structure

```
backend/
├── nodejs/
│   └── apps/
│       └── src/
│           ├── libs/
│           │   ├── config/
│           │   │   ├── feature-flags.ts           # Feature flag service (NEW)
│           │   │   └── feature-flags.service.ts   # (NEW)
│           │   └── services/
│           │       └── ab-testing.service.ts      # A/B testing (NEW)
│           └── modules/
│               └── enterprise_search/
│                   └── services/
│                       └── verification-trigger.service.ts  # (NEW)
├── python/
│   ├── hupyy-verification-service/                # NEW MICROSERVICE
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── api/
│   │   │   ├── services/
│   │   │   │   ├── hupyy_client.py
│   │   │   │   ├── circuit_breaker.py
│   │   │   │   ├── verification_orchestrator.py
│   │   │   │   ├── qdrant_updater.py
│   │   │   │   ├── arango_updater.py
│   │   │   │   ├── pagerank_calculator.py
│   │   │   │   └── cache.py
│   │   │   ├── kafka/
│   │   │   ├── models/
│   │   │   └── utils/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   └── app/
│       ├── config/
│       │   └── feature_flags.py                   # (NEW)
│       ├── modules/
│       │   └── retrieval/
│       │       └── ranking/
│       │           └── verification_ranking.py    # (NEW)
│       └── services/
│           ├── vector_db/
│           │   └── qdrant/
│           │       └── schema.py                  # UPDATED
│           └── graph_db/
│               └── arango/
│                   └── schema.py                  # UPDATED
└── scripts/
    ├── collect_baseline_metrics.py                # Phase 0
    ├── create_verification_indexes.py             # Phase 2
    ├── gradual_weight_transition.py               # Phase 4
    ├── canary_rollout.py                          # Phase 5
    ├── cold_start_backfill.py                     # Phase 5
    └── monitor_feedback_loop.py                   # Phase 5

deployment/
└── docker-compose/
    └── docker-compose.prod.yml                    # UPDATED (add hupyy-verification service)

.prompts/
└── 002-hupyy-integration-plan/
    ├── hupyy-integration-plan.md                  # THIS DOCUMENT
    └── SUMMARY.md                                 # Executive summary
```

### Appendix B: Configuration Examples

**Feature Flags (MongoDB `config` collection):**

```json
{
  "_id": "verification_config",
  "verification_enabled": true,
  "verification_shadow_mode": false,
  "verification_async": true,
  "verification_sampling_rate": 0.20,
  "verification_ranking_weight": 0.15,
  "verification_top_k": 10,
  "circuit_breaker_enabled": true,
  "circuit_breaker_failure_threshold": 5,
  "circuit_breaker_timeout": 60,
  "max_concurrent_verifications": 10,
  "verification_rollout_percentage": 100,
  "updated_at": "2025-11-27T12:00:00Z"
}
```

**Environment Variables (Docker Compose):**

```bash
# Hupyy API
HUPYY_API_URL=https://verticalslice-smt-service-gvav8.ondigitalocean.app

# Kafka
KAFKA_BROKERS=kafka-1:9092

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_API_KEY=your_qdrant_secret_api_key

# ArangoDB
ARANGO_URL=http://arango:8529
ARANGO_USERNAME=root
ARANGO_PASSWORD=your_password

# Circuit Breaker
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60

# Verification
MAX_CONCURRENT_VERIFICATIONS=10
VERIFICATION_ENABLED=true
```

### Appendix C: Testing Checklists

**Phase 0 Testing Checklist:**
- [ ] All Kafka topics created and accessible
- [ ] Feature flag system updates within 10s
- [ ] Prometheus metrics endpoint returns 200
- [ ] All Grafana dashboards render without errors
- [ ] Test alert fires and routes to Slack
- [ ] Baseline metrics collected for 1 week

**Phase 1 Testing Checklist:**
- [ ] Hupyy API client handles 200, 422, 500, timeout responses
- [ ] Retry logic triggers on network errors (max 3 retries)
- [ ] Circuit breaker trips after 5 consecutive failures
- [ ] Circuit breaker recovers in half-open state
- [ ] Kafka consumer processes messages without crashes
- [ ] Failure mode classification accurate (all 8 modes tested)
- [ ] Docker container healthy after 24h continuous operation

**Phase 2 Testing Checklist:**
- [ ] Search pipeline triggers verification for sampled queries
- [ ] Qdrant payload updated with verification metadata
- [ ] Qdrant update latency p95 <100ms
- [ ] Search query latency unchanged (async verification)
- [ ] Backward compatibility: unverified chunks still work
- [ ] Verification coverage reaches 10% after 1 week

**Phase 3 Testing Checklist:**
- [ ] ArangoDB document metrics updated correctly
- [ ] PageRank recalculation completes <60s for 1000 docs
- [ ] Quality multiplier in range [0.5, 2.0]
- [ ] PageRank trigger fires on significant quality change (ΔQ >0.2)
- [ ] No ArangoDB performance degradation

**Phase 4 Testing Checklist:**
- [ ] Ranking formula produces correct scores
- [ ] Failure mode multipliers applied correctly
- [ ] A/B testing assigns users consistently
- [ ] Gradual weight transition increases linearly
- [ ] Precision@5 improves ≥5% in A/B test
- [ ] Ranking latency impact <10ms

**Phase 5 Testing Checklist:**
- [ ] Canary rollout completes without incidents
- [ ] 100% of users on verification ranking
- [ ] Precision@5 ≥ 98%
- [ ] Cache hit rate ≥ 40%
- [ ] Feedback loop stable (coverage >80%, diversity >3.0, drift <0.3)
- [ ] Cost within budget

---

**END OF IMPLEMENTATION PLAN**
