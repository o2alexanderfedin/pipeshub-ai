# Unit Test Specifications for Hupyy SMT Verification Integration

**Date:** November 30, 2025
**Project:** PipesHub AI - Hupyy SMT Verification Integration
**Purpose:** Detailed file-by-file specifications for all unit tests

---

## Executive Summary

This document provides comprehensive specifications for **60-90 unit tests** across Python, TypeScript, and React codebases. Unit tests form **70% of our test suite** and are designed to be fast (<100ms per test), isolated (mocked dependencies), and comprehensive (≥90% code coverage).

**Test Distribution:**
- **Python Backend**: ~50 tests (models, client, orchestrator)
- **TypeScript Backend**: ~15 tests (controllers, validators)
- **Frontend React**: ~10 tests (components, hooks)
- **Utilities**: ~10 tests (shared functions)

**Coverage Goals:**
- Line Coverage: ≥90%
- Branch Coverage: ≥85%
- Function Coverage: ≥95%

---

## 1. Python Backend Tests

### 1.1 File: `backend/python/app/tests/verification/test_models.py`

**Purpose:** Test Pydantic model validation, serialization, and business logic

**Test Count:** 15 tests

**Dependencies to Mock:** None (pure Pydantic models)

---

#### Test Suite: HupyyRequest Model

**Test 1: test_hupyy_request_valid_construction**
```python
def test_hupyy_request_valid_construction():
    """Test valid HupyyRequest creation."""
    request = HupyyRequest(
        informal_text="Find all users with admin privileges",
        skip_formalization=False,
        enrich=False,
    )

    assert request.informal_text == "Find all users with admin privileges"
    assert request.skip_formalization is False
    assert request.enrich is False
```

**Expected Behavior:** Model created successfully with provided values

---

**Test 2: test_hupyy_request_default_values**
```python
def test_hupyy_request_default_values():
    """Test default values for optional fields."""
    request = HupyyRequest(informal_text="Test query")

    assert request.skip_formalization is False
    assert request.enrich is False  # Always forced to False by validator
```

**Expected Behavior:** Default values set correctly

---

**Test 3: test_hupyy_request_empty_text_validation**
```python
def test_hupyy_request_empty_text_validation():
    """Test that empty informal_text raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        HupyyRequest(informal_text="")

    assert "Informal text cannot be empty" in str(exc_info.value)
```

**Expected Behavior:** ValidationError raised for empty text

---

**Test 4: test_hupyy_request_whitespace_only_text**
```python
def test_hupyy_request_whitespace_only_text():
    """Test that whitespace-only text raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        HupyyRequest(informal_text="   \n\t   ")

    assert "Informal text cannot be empty" in str(exc_info.value)
```

**Expected Behavior:** ValidationError raised for whitespace-only text

---

**Test 5: test_hupyy_request_enrich_forced_false**
```python
def test_hupyy_request_enrich_forced_false():
    """Test that enrich is always forced to False."""
    request = HupyyRequest(informal_text="Test", enrich=True)

    assert request.enrich is False  # Forced by validator
```

**Expected Behavior:** enrich always False regardless of input

---

**Test 6: test_hupyy_request_text_trimming**
```python
def test_hupyy_request_text_trimming():
    """Test that informal_text is trimmed."""
    request = HupyyRequest(informal_text="  Test query  ")

    assert request.informal_text == "Test query"
```

**Expected Behavior:** Leading/trailing whitespace removed

---

#### Test Suite: HupyyResponse Model

**Test 7: test_from_hupyy_process_response_sat**
```python
def test_from_hupyy_process_response_sat():
    """Test parsing SAT response from Hupyy."""
    response_data = {
        "check_sat_result": "SAT",
        "formalization_similarity": 0.92,
        "model": {"x": "3", "y": "7"},
        "proof": {"summary": "Formula is satisfiable"},
        "smt_lib_code": "(assert (= (+ x y) 10))",
        "formal_text": "x + y = 10",
        "informal_text": "Sum of x and y is 10",
        "solver_success": True,
        "passed_all_checks": True,
        "metrics": {"total_time_ms": 1250},
    }

    response = HupyyResponse.from_hupyy_process_response(response_data)

    assert response.verdict == VerificationVerdict.SAT
    assert response.confidence == 0.92
    assert response.formalization_similarity == 0.92
    assert response.explanation == "Formula is satisfiable"
    assert response.metadata["model"] == {"x": "3", "y": "7"}
    assert response.metadata["smt_lib_code"] == "(assert (= (+ x y) 10))"
    assert response.duration_ms == 1250
```

**Expected Behavior:** SAT response parsed correctly

---

**Test 8: test_from_hupyy_process_response_unsat**
```python
def test_from_hupyy_process_response_unsat():
    """Test parsing UNSAT response from Hupyy."""
    response_data = {
        "check_sat_result": "UNSAT",
        "formalization_similarity": 0.88,
        "proof": {"summary": "No solution exists"},
    }

    response = HupyyResponse.from_hupyy_process_response(response_data)

    assert response.verdict == VerificationVerdict.UNSAT
    assert response.confidence == 0.88
    assert response.explanation == "No solution exists"
```

**Expected Behavior:** UNSAT response parsed correctly

---

**Test 9: test_from_hupyy_process_response_unknown**
```python
def test_from_hupyy_process_response_unknown():
    """Test parsing UNKNOWN response (timeout, etc.)."""
    response_data = {
        "check_sat_result": "UNKNOWN",
        "formalization_similarity": 0.45,
    }

    response = HupyyResponse.from_hupyy_process_response(response_data)

    assert response.verdict == VerificationVerdict.UNKNOWN
    assert response.confidence == 0.45
```

**Expected Behavior:** UNKNOWN verdict for non-SAT/UNSAT results

---

**Test 10: test_from_hupyy_process_response_missing_fields**
```python
def test_from_hupyy_process_response_missing_fields():
    """Test parsing response with minimal fields."""
    response_data = {"check_sat_result": "SAT"}

    response = HupyyResponse.from_hupyy_process_response(response_data)

    assert response.verdict == VerificationVerdict.SAT
    assert response.confidence == 0.5  # Default
    assert response.formalization_similarity is None
    assert response.explanation is None
    assert response.duration_ms is None
```

**Expected Behavior:** Defaults used for missing fields

---

**Test 11: test_from_hupyy_process_response_metadata_none_filtering**
```python
def test_from_hupyy_process_response_metadata_none_filtering():
    """Test that None values are filtered from metadata."""
    response_data = {
        "check_sat_result": "SAT",
        "formalization_similarity": 0.9,
        "model": {"x": "5"},
        "proof": None,  # Should be filtered
        "smt_lib_code": None,  # Should be filtered
    }

    response = HupyyResponse.from_hupyy_process_response(response_data)

    assert "model" in response.metadata
    assert "proof" not in response.metadata
    assert "smt_lib_code" not in response.metadata
```

**Expected Behavior:** None values removed from metadata

---

#### Test Suite: VerificationRequest Model

**Test 12: test_verification_request_valid_construction**
```python
def test_verification_request_valid_construction():
    """Test valid VerificationRequest creation."""
    request = VerificationRequest(
        request_id="req_123",
        content="Test content",
        chunk_index=0,
        total_chunks=1,
        nl_query="Find admins",
        source_document_id="doc_456",
    )

    assert request.request_id == "req_123"
    assert request.content == "Test content"
    assert request.chunk_index == 0
    assert request.total_chunks == 1
```

**Expected Behavior:** Model created successfully

---

**Test 13: test_verification_request_content_size_validation**
```python
def test_verification_request_content_size_validation():
    """Test that content exceeding 10KB raises ValidationError."""
    large_content = "x" * (10 * 1024 + 1)  # 10KB + 1 byte

    with pytest.raises(ValidationError) as exc_info:
        VerificationRequest(
            request_id="req_123",
            content=large_content,
            nl_query="Test",
        )

    assert "exceeds maximum size" in str(exc_info.value)
```

**Expected Behavior:** ValidationError for oversized content

---

#### Test Suite: VerificationResult Model

**Test 14: test_verification_result_valid_construction**
```python
def test_verification_result_valid_construction():
    """Test valid VerificationResult creation."""
    result = VerificationResult(
        request_id="req_123",
        chunk_index=0,
        verdict=VerificationVerdict.SAT,
        confidence=0.95,
        formalization_similarity=0.88,
        explanation="Test explanation",
        duration_seconds=62.5,
        cached=False,
    )

    assert result.verdict == VerificationVerdict.SAT
    assert result.confidence == 0.95
    assert result.duration_seconds == 62.5
    assert result.cached is False
```

**Expected Behavior:** Model created successfully

---

#### Test Suite: VerificationStats Model

**Test 15: test_verification_stats_success_rate_calculation**
```python
def test_verification_stats_success_rate_calculation():
    """Test success rate calculation."""
    stats = VerificationStats(
        total_requests=100,
        successful_verifications=85,
        failed_verifications=15,
    )

    stats.update_success_rate()

    assert stats.success_rate == 0.85
```

**Expected Behavior:** Success rate calculated correctly

---

### 1.2 File: `backend/python/app/tests/verification/test_hupyy_client.py`

**Purpose:** Test HupyyClient HTTP interactions, caching, and error handling

**Test Count:** 20 tests

**Dependencies to Mock:**
- `httpx.AsyncClient` - HTTP requests
- `VerificationCache` - Caching layer
- `CircuitBreaker` - Circuit breaker protection
- `VerificationMetrics` - Metrics collection

---

#### Test Suite: HupyyClient Initialization

**Test 16: test_hupyy_client_initialization**
```python
def test_hupyy_client_initialization():
    """Test HupyyClient initialization with defaults."""
    client = HupyyClient(api_url="https://hupyy.example.com")

    assert client.api_url == "https://hupyy.example.com"
    assert client.timeout_seconds == 150
    assert client.http_client is not None
```

**Expected Behavior:** Client initialized with defaults

---

**Test 17: test_hupyy_client_url_trailing_slash_removal**
```python
def test_hupyy_client_url_trailing_slash_removal():
    """Test that trailing slash is removed from API URL."""
    client = HupyyClient(api_url="https://hupyy.example.com/")

    assert client.api_url == "https://hupyy.example.com"
```

**Expected Behavior:** Trailing slash removed

---

**Test 18: test_hupyy_client_custom_timeout**
```python
def test_hupyy_client_custom_timeout():
    """Test custom timeout configuration."""
    client = HupyyClient(
        api_url="https://hupyy.example.com", timeout_seconds=300
    )

    assert client.timeout_seconds == 300
```

**Expected Behavior:** Custom timeout set

---

#### Test Suite: verify() Method

**Test 19: test_verify_cache_hit**
```python
@pytest.mark.asyncio
async def test_verify_cache_hit(mock_cache):
    """Test verification with cache hit."""
    # Setup cache to return result
    mock_cache.get.return_value = {
        "verdict": "SAT",
        "confidence": 0.95,
        "formalization_similarity": 0.88,
        "explanation": "Cached result",
        "metadata": {},
    }

    client = HupyyClient(api_url="https://hupyy.example.com", cache=mock_cache)

    request = VerificationRequest(
        request_id="req_123",
        content="Test content",
        nl_query="Find admins",
    )

    result = await client.verify(request)

    assert result.verdict == VerificationVerdict.SAT
    assert result.cached is True
    assert result.confidence == 0.95
    mock_cache.get.assert_called_once_with("Test content")
```

**Expected Behavior:** Cached result returned, no HTTP call made

---

**Test 20: test_verify_cache_miss**
```python
@pytest.mark.asyncio
async def test_verify_cache_miss(mock_cache, mock_http_client):
    """Test verification with cache miss."""
    # Setup cache miss
    mock_cache.get.return_value = None

    # Setup HTTP response
    mock_response = {
        "check_sat_result": "SAT",
        "formalization_similarity": 0.92,
    }
    mock_http_client.post.return_value = AsyncMock(
        status_code=200, json=lambda: mock_response
    )

    client = HupyyClient(
        api_url="https://hupyy.example.com",
        cache=mock_cache,
    )
    client.http_client = mock_http_client

    request = VerificationRequest(
        request_id="req_123",
        content="Test content",
        nl_query="Find admins",
    )

    result = await client.verify(request)

    assert result.verdict == VerificationVerdict.SAT
    assert result.cached is False
    mock_cache.get.assert_called_once()
    mock_http_client.post.assert_called_once()
```

**Expected Behavior:** HTTP call made, result cached

---

**Test 21: test_verify_timeout**
```python
@pytest.mark.asyncio
async def test_verify_timeout(mock_http_client):
    """Test timeout handling during verification."""
    # Setup timeout
    mock_http_client.post.side_effect = asyncio.TimeoutError()

    client = HupyyClient(api_url="https://hupyy.example.com")
    client.http_client = mock_http_client

    request = VerificationRequest(
        request_id="req_123",
        content="Test content",
        nl_query="Find admins",
    )

    result = await client.verify(request)

    assert result.verdict == VerificationVerdict.UNKNOWN
    assert result.failure_mode == FailureMode.TIMEOUT
    assert result.confidence == 0.0
    assert result.cached is False
```

**Expected Behavior:** UNKNOWN verdict with TIMEOUT failure mode

---

**Test 22: test_verify_http_error**
```python
@pytest.mark.asyncio
async def test_verify_http_error(mock_http_client):
    """Test HTTP error handling (404, 500, etc.)."""
    # Setup HTTP error
    mock_http_client.post.side_effect = httpx.HTTPStatusError(
        "Not Found", request=Mock(), response=Mock(status_code=404)
    )

    client = HupyyClient(api_url="https://hupyy.example.com")
    client.http_client = mock_http_client

    request = VerificationRequest(
        request_id="req_123",
        content="Test content",
        nl_query="Find admins",
    )

    result = await client.verify(request)

    assert result.verdict == VerificationVerdict.ERROR
    assert result.failure_mode == FailureMode.NETWORK_ERROR
```

**Expected Behavior:** ERROR verdict with NETWORK_ERROR failure mode

---

**Test 23: test_verify_network_error**
```python
@pytest.mark.asyncio
async def test_verify_network_error(mock_http_client):
    """Test network error handling."""
    mock_http_client.post.side_effect = httpx.NetworkError("Connection failed")

    client = HupyyClient(api_url="https://hupyy.example.com")
    client.http_client = mock_http_client

    request = VerificationRequest(
        request_id="req_123",
        content="Test content",
        nl_query="Find admins",
    )

    result = await client.verify(request)

    assert result.verdict == VerificationVerdict.ERROR
    assert result.failure_mode == FailureMode.NETWORK_ERROR
```

**Expected Behavior:** ERROR verdict for network failures

---

#### Test Suite: _make_api_call() Method

**Test 24: test_make_api_call_request_format**
```python
@pytest.mark.asyncio
async def test_make_api_call_request_format(mock_http_client):
    """Test API request format."""
    mock_response = {"check_sat_result": "SAT", "formalization_similarity": 0.9}
    mock_http_client.post.return_value = AsyncMock(
        status_code=200, json=lambda: mock_response
    )

    client = HupyyClient(api_url="https://hupyy.example.com")
    client.http_client = mock_http_client

    request = VerificationRequest(
        request_id="req_123",
        content="Test query",
        nl_query="Find admins",
    )

    await client._make_api_call(request)

    # Verify request format
    mock_http_client.post.assert_called_once()
    call_args = mock_http_client.post.call_args

    assert call_args[0][0] == "https://hupyy.example.com/pipeline/process"
    assert call_args[1]["json"]["informal_text"] == "Test query"
    assert call_args[1]["json"]["skip_formalization"] is False
    assert call_args[1]["json"]["enrich"] is False
    assert call_args[1]["headers"]["Content-Type"] == "application/json"
```

**Expected Behavior:** Correct HTTP request format to /pipeline/process

---

**Test 25: test_make_api_call_response_parsing**
```python
@pytest.mark.asyncio
async def test_make_api_call_response_parsing(mock_http_client):
    """Test response parsing."""
    mock_response = {
        "check_sat_result": "SAT",
        "formalization_similarity": 0.92,
        "model": {"x": "5"},
    }
    mock_http_client.post.return_value = AsyncMock(
        status_code=200, json=lambda: mock_response
    )

    client = HupyyClient(api_url="https://hupyy.example.com")
    client.http_client = mock_http_client

    request = VerificationRequest(
        request_id="req_123",
        content="Test query",
        nl_query="Find admins",
    )

    response = await client._make_api_call(request)

    assert isinstance(response, HupyyResponse)
    assert response.verdict == VerificationVerdict.SAT
    assert response.confidence == 0.92
```

**Expected Behavior:** Response parsed into HupyyResponse

---

#### Test Suite: verify_parallel() Method

**Test 26: test_verify_parallel_multiple_requests**
```python
@pytest.mark.asyncio
async def test_verify_parallel_multiple_requests(mock_http_client):
    """Test parallel verification of multiple requests."""
    # Setup responses for 3 requests
    responses = [
        {"check_sat_result": "SAT", "formalization_similarity": 0.9},
        {"check_sat_result": "UNSAT", "formalization_similarity": 0.85},
        {"check_sat_result": "SAT", "formalization_similarity": 0.92},
    ]

    mock_http_client.post.side_effect = [
        AsyncMock(status_code=200, json=lambda r=r: r) for r in responses
    ]

    client = HupyyClient(api_url="https://hupyy.example.com")
    client.http_client = mock_http_client

    requests = [
        VerificationRequest(
            request_id=f"req_{i}",
            content=f"Content {i}",
            nl_query="Test",
        )
        for i in range(3)
    ]

    results = await client.verify_parallel(requests, max_concurrency=2)

    assert len(results) == 3
    assert results[0].verdict == VerificationVerdict.SAT
    assert results[1].verdict == VerificationVerdict.UNSAT
    assert results[2].verdict == VerificationVerdict.SAT
```

**Expected Behavior:** All requests verified in parallel

---

**Test 27: test_verify_parallel_concurrency_limit**
```python
@pytest.mark.asyncio
async def test_verify_parallel_concurrency_limit():
    """Test concurrency limiting in parallel verification."""
    # Track concurrent calls
    concurrent_calls = []
    max_concurrent = 0

    async def mock_verify(request):
        concurrent_calls.append(1)
        current = len(concurrent_calls)
        nonlocal max_concurrent
        max_concurrent = max(max_concurrent, current)

        await asyncio.sleep(0.01)  # Simulate work

        concurrent_calls.pop()

        return VerificationResult(
            request_id=request.request_id,
            chunk_index=0,
            verdict=VerificationVerdict.SAT,
            confidence=0.9,
            duration_seconds=0.01,
            cached=False,
        )

    client = HupyyClient(api_url="https://hupyy.example.com")
    client.verify = mock_verify

    requests = [
        VerificationRequest(
            request_id=f"req_{i}",
            content=f"Content {i}",
            nl_query="Test",
        )
        for i in range(10)
    ]

    await client.verify_parallel(requests, max_concurrency=3)

    assert max_concurrent <= 3
```

**Expected Behavior:** Concurrency limited to specified value

---

#### Test Suite: chunk_content() Method

**Test 28: test_chunk_content_single_chunk**
```python
def test_chunk_content_single_chunk():
    """Test chunking when content fits in single chunk."""
    client = HupyyClient(api_url="https://hupyy.example.com")

    content = "Small content"
    chunks = client.chunk_content(
        content=content,
        request_id="req_123",
        nl_query="Test query",
    )

    assert len(chunks) == 1
    assert chunks[0].content == content
    assert chunks[0].chunk_index == 0
    assert chunks[0].total_chunks == 1
```

**Expected Behavior:** Single chunk for small content

---

**Test 29: test_chunk_content_multiple_chunks**
```python
def test_chunk_content_multiple_chunks():
    """Test chunking large content."""
    client = HupyyClient(
        api_url="https://hupyy.example.com",
        chunking_config=ChunkingConfig(max_chunk_size_bytes=100, overlap_chars=10),
    )

    content = "x" * 250  # 250 bytes
    chunks = client.chunk_content(
        content=content,
        request_id="req_123",
        nl_query="Test query",
    )

    assert len(chunks) > 1
    assert all(chunk.total_chunks == len(chunks) for chunk in chunks)
    assert all(
        chunk.chunk_index == i for i, chunk in enumerate(chunks)
    )
```

**Expected Behavior:** Content split into multiple chunks

---

**Test 30: test_chunk_content_overlap**
```python
def test_chunk_content_overlap():
    """Test that chunks have overlap."""
    client = HupyyClient(
        api_url="https://hupyy.example.com",
        chunking_config=ChunkingConfig(max_chunk_size_bytes=100, overlap_chars=20),
    )

    content = "abcdefghijklmnopqrstuvwxyz" * 10  # 260 chars
    chunks = client.chunk_content(
        content=content,
        request_id="req_123",
        nl_query="Test query",
    )

    # Check overlap between consecutive chunks
    if len(chunks) > 1:
        chunk1_end = chunks[0].content[-20:]
        chunk2_start = chunks[1].content[:20]
        assert chunk1_end == chunk2_start
```

**Expected Behavior:** Chunks overlap as configured

---

#### Test Suite: Caching Integration

**Test 31: test_caching_sat_unsat_results**
```python
@pytest.mark.asyncio
async def test_caching_sat_unsat_results(mock_cache, mock_http_client):
    """Test that SAT and UNSAT results are cached."""
    mock_cache.get.return_value = None
    mock_response = {"check_sat_result": "SAT", "formalization_similarity": 0.9}
    mock_http_client.post.return_value = AsyncMock(
        status_code=200, json=lambda: mock_response
    )

    client = HupyyClient(
        api_url="https://hupyy.example.com",
        cache=mock_cache,
    )
    client.http_client = mock_http_client

    request = VerificationRequest(
        request_id="req_123",
        content="Test content",
        nl_query="Find admins",
    )

    await client.verify(request)

    # Verify cache set was called
    mock_cache.set.assert_called_once()
    call_args = mock_cache.set.call_args[0]
    assert call_args[0] == "Test content"
    assert call_args[1]["verdict"] == "SAT"
```

**Expected Behavior:** SAT/UNSAT results cached

---

**Test 32: test_not_caching_unknown_results**
```python
@pytest.mark.asyncio
async def test_not_caching_unknown_results(mock_cache, mock_http_client):
    """Test that UNKNOWN results are not cached."""
    mock_cache.get.return_value = None
    mock_response = {"check_sat_result": "UNKNOWN", "formalization_similarity": 0.4}
    mock_http_client.post.return_value = AsyncMock(
        status_code=200, json=lambda: mock_response
    )

    client = HupyyClient(
        api_url="https://hupyy.example.com",
        cache=mock_cache,
    )
    client.http_client = mock_http_client

    request = VerificationRequest(
        request_id="req_123",
        content="Test content",
        nl_query="Find admins",
    )

    await client.verify(request)

    # Verify cache set was NOT called
    mock_cache.set.assert_not_called()
```

**Expected Behavior:** UNKNOWN results not cached

---

#### Test Suite: Metrics Integration

**Test 33: test_metrics_recording_success**
```python
@pytest.mark.asyncio
async def test_metrics_recording_success(mock_metrics, mock_http_client):
    """Test metrics recorded for successful verification."""
    mock_response = {"check_sat_result": "SAT", "formalization_similarity": 0.9}
    mock_http_client.post.return_value = AsyncMock(
        status_code=200, json=lambda: mock_response
    )

    client = HupyyClient(
        api_url="https://hupyy.example.com",
        metrics=mock_metrics,
    )
    client.http_client = mock_http_client

    request = VerificationRequest(
        request_id="req_123",
        content="Test content",
        nl_query="Find admins",
    )

    await client.verify(request)

    mock_metrics.record_verification_request.assert_called()
    assert mock_metrics.record_verification_request.call_args[0][0] == "success"
```

**Expected Behavior:** Success metrics recorded

---

**Test 34: test_metrics_recording_failure**
```python
@pytest.mark.asyncio
async def test_metrics_recording_failure(mock_metrics, mock_http_client):
    """Test metrics recorded for failed verification."""
    mock_http_client.post.side_effect = httpx.NetworkError("Connection failed")

    client = HupyyClient(
        api_url="https://hupyy.example.com",
        metrics=mock_metrics,
    )
    client.http_client = mock_http_client

    request = VerificationRequest(
        request_id="req_123",
        content="Test content",
        nl_query="Find admins",
    )

    await client.verify(request)

    mock_metrics.record_verification_request.assert_called()
    assert mock_metrics.record_verification_request.call_args[0][0] == "failure"
```

**Expected Behavior:** Failure metrics recorded

---

**Test 35: test_close_http_client**
```python
@pytest.mark.asyncio
async def test_close_http_client(mock_http_client):
    """Test HTTP client closure."""
    client = HupyyClient(api_url="https://hupyy.example.com")
    client.http_client = mock_http_client

    await client.close()

    mock_http_client.aclose.assert_called_once()
```

**Expected Behavior:** HTTP client closed properly

---

### 1.3 File: `backend/python/app/tests/verification/test_orchestrator.py`

**Purpose:** Test Kafka message consumption, batch processing, and result publishing

**Test Count:** 15 tests

**Dependencies to Mock:**
- `AIOKafkaConsumer` - Kafka consumer
- `AIOKafkaProducer` - Kafka producer
- `HupyyClient` - Verification client
- `FeatureFlagService` - Feature flags

---

#### Test Suite: Orchestrator Initialization

**Test 36: test_orchestrator_initialization**
```python
def test_orchestrator_initialization():
    """Test VerificationOrchestrator initialization."""
    mock_client = Mock(spec=HupyyClient)
    mock_ff_service = Mock(spec=FeatureFlagService)

    orchestrator = VerificationOrchestrator(
        kafka_brokers="localhost:9092",
        consumer_group="test-group",
        hupyy_client=mock_client,
        feature_flag_service=mock_ff_service,
        batch_size=10,
        max_concurrency=5,
    )

    assert orchestrator.kafka_brokers == "localhost:9092"
    assert orchestrator.consumer_group == "test-group"
    assert orchestrator.batch_size == 10
    assert orchestrator.max_concurrency == 5
```

**Expected Behavior:** Orchestrator initialized correctly

---

#### Test Suite: Message Consumption

**Test 37: test_process_batch_valid_messages**
```python
@pytest.mark.asyncio
async def test_process_batch_valid_messages(mock_hupyy_client):
    """Test processing batch of valid messages."""
    # Setup mock client
    mock_hupyy_client.verify_parallel.return_value = [
        VerificationResult(
            request_id="req_1",
            chunk_index=0,
            verdict=VerificationVerdict.SAT,
            confidence=0.95,
            duration_seconds=60.0,
            cached=False,
        )
    ]

    orchestrator = VerificationOrchestrator(
        kafka_brokers="localhost:9092",
        consumer_group="test-group",
        hupyy_client=mock_hupyy_client,
        feature_flag_service=Mock(),
    )
    orchestrator.producer = Mock(spec=AIOKafkaProducer)

    # Create mock message
    message = Mock()
    message.value = {
        "request_id": "req_1",
        "content": "Test content",
        "nl_query": "Find admins",
        "timestamp": datetime.utcnow().isoformat(),
    }

    await orchestrator.process_batch([message])

    # Verify verification called
    mock_hupyy_client.verify_parallel.assert_called_once()

    # Verify result published
    orchestrator.producer.send.assert_called_once()
```

**Expected Behavior:** Messages processed and results published

---

**Test 38: test_process_batch_malformed_message**
```python
@pytest.mark.asyncio
async def test_process_batch_malformed_message():
    """Test handling of malformed messages."""
    orchestrator = VerificationOrchestrator(
        kafka_brokers="localhost:9092",
        consumer_group="test-group",
        hupyy_client=Mock(),
        feature_flag_service=Mock(),
    )
    orchestrator.producer = Mock(spec=AIOKafkaProducer)
    orchestrator.send_to_dlq = AsyncMock()

    # Create malformed message
    message = Mock()
    message.value = {"invalid": "data"}  # Missing required fields

    await orchestrator.process_batch([message])

    # Verify sent to DLQ
    orchestrator.send_to_dlq.assert_called_once()
```

**Expected Behavior:** Malformed messages sent to DLQ

---

#### Test Suite: Result Publishing

**Test 39: test_publish_result_sat_verdict**
```python
@pytest.mark.asyncio
async def test_publish_result_sat_verdict():
    """Test publishing SAT result to verification_complete topic."""
    orchestrator = VerificationOrchestrator(
        kafka_brokers="localhost:9092",
        consumer_group="test-group",
        hupyy_client=Mock(),
        feature_flag_service=Mock(),
    )
    orchestrator.producer = AsyncMock(spec=AIOKafkaProducer)

    result = VerificationResult(
        request_id="req_1",
        chunk_index=0,
        verdict=VerificationVerdict.SAT,
        confidence=0.95,
        duration_seconds=60.0,
        cached=False,
    )

    metadata = {"org_id": "org_1", "user_id": "user_1"}

    await orchestrator.publish_result(result, metadata)

    # Verify sent to correct topic
    orchestrator.producer.send.assert_called_once_with(
        "verification_complete", value=ANY
    )
```

**Expected Behavior:** SAT results sent to verification_complete

---

**Test 40: test_publish_result_unsat_verdict**
```python
@pytest.mark.asyncio
async def test_publish_result_unsat_verdict():
    """Test publishing UNSAT result."""
    orchestrator = VerificationOrchestrator(
        kafka_brokers="localhost:9092",
        consumer_group="test-group",
        hupyy_client=Mock(),
        feature_flag_service=Mock(),
    )
    orchestrator.producer = AsyncMock(spec=AIOKafkaProducer)

    result = VerificationResult(
        request_id="req_1",
        chunk_index=0,
        verdict=VerificationVerdict.UNSAT,
        confidence=0.88,
        duration_seconds=65.0,
        cached=False,
    )

    metadata = {}

    await orchestrator.publish_result(result, metadata)

    orchestrator.producer.send.assert_called_once_with(
        "verification_complete", value=ANY
    )
```

**Expected Behavior:** UNSAT results sent to verification_complete

---

**Test 41: test_publish_result_unknown_verdict**
```python
@pytest.mark.asyncio
async def test_publish_result_unknown_verdict():
    """Test publishing UNKNOWN result to verification_failed topic."""
    orchestrator = VerificationOrchestrator(
        kafka_brokers="localhost:9092",
        consumer_group="test-group",
        hupyy_client=Mock(),
        feature_flag_service=Mock(),
    )
    orchestrator.producer = AsyncMock(spec=AIOKafkaProducer)

    result = VerificationResult(
        request_id="req_1",
        chunk_index=0,
        verdict=VerificationVerdict.UNKNOWN,
        confidence=0.0,
        failure_mode=FailureMode.TIMEOUT,
        duration_seconds=150.0,
        cached=False,
    )

    metadata = {}

    await orchestrator.publish_result(result, metadata)

    # Verify sent to failed topic
    orchestrator.producer.send.assert_called_once_with(
        "verification_failed", value=ANY
    )
```

**Expected Behavior:** UNKNOWN/ERROR results sent to verification_failed

---

**Test 42: test_publish_result_includes_metadata**
```python
@pytest.mark.asyncio
async def test_publish_result_includes_metadata():
    """Test that published message includes original metadata."""
    orchestrator = VerificationOrchestrator(
        kafka_brokers="localhost:9092",
        consumer_group="test-group",
        hupyy_client=Mock(),
        feature_flag_service=Mock(),
    )
    orchestrator.producer = AsyncMock(spec=AIOKafkaProducer)

    result = VerificationResult(
        request_id="req_1",
        chunk_index=0,
        verdict=VerificationVerdict.SAT,
        confidence=0.95,
        duration_seconds=60.0,
        cached=False,
    )

    metadata = {
        "org_id": "org_123",
        "user_id": "user_456",
        "query_id": "query_789",
        "document_id": "doc_abc",
    }

    await orchestrator.publish_result(result, metadata)

    # Extract published message
    call_args = orchestrator.producer.send.call_args[1]
    message = call_args["value"]

    assert message["org_id"] == "org_123"
    assert message["user_id"] == "user_456"
    assert message["query_id"] == "query_789"
    assert message["document_id"] == "doc_abc"
```

**Expected Behavior:** Metadata included in published message

---

#### Test Suite: Feature Flag Integration

**Test 43: test_run_verification_disabled**
```python
@pytest.mark.asyncio
async def test_run_verification_disabled(mock_feature_flags):
    """Test orchestrator behavior when verification disabled."""
    # Setup feature flag to return disabled
    mock_ff = Mock()
    mock_ff.verification_enabled = False
    mock_feature_flags.get_verification_flags.return_value = mock_ff

    orchestrator = VerificationOrchestrator(
        kafka_brokers="localhost:9092",
        consumer_group="test-group",
        hupyy_client=Mock(),
        feature_flag_service=mock_feature_flags,
    )
    orchestrator.consumer = AsyncMock(spec=AIOKafkaConsumer)
    orchestrator.shutdown_requested = True  # Exit after one iteration

    # Run orchestrator (should sleep and not process)
    await orchestrator.run()

    # Verify no messages consumed
    orchestrator.consumer.getmany.assert_not_called()
```

**Expected Behavior:** No processing when verification disabled

---

#### Test Suite: Offset Management

**Test 44: test_manual_offset_commit**
```python
@pytest.mark.asyncio
async def test_manual_offset_commit():
    """Test manual offset commit after batch processing."""
    orchestrator = VerificationOrchestrator(
        kafka_brokers="localhost:9092",
        consumer_group="test-group",
        hupyy_client=Mock(),
        feature_flag_service=Mock(),
    )
    orchestrator.consumer = AsyncMock(spec=AIOKafkaConsumer)
    orchestrator.consumer.getmany.return_value = {}  # No messages
    orchestrator.shutdown_requested = True

    await orchestrator.run()

    # Verify commit called
    orchestrator.consumer.commit.assert_called()
```

**Expected Behavior:** Offsets committed after processing

---

**Test 45: test_start_consumer_auto_commit_false**
```python
@pytest.mark.asyncio
async def test_start_consumer_auto_commit_false():
    """Test consumer started with auto_commit disabled."""
    orchestrator = VerificationOrchestrator(
        kafka_brokers="localhost:9092",
        consumer_group="test-group",
        hupyy_client=Mock(),
        feature_flag_service=Mock(),
    )

    with patch("app.verification.orchestrator.AIOKafkaConsumer") as MockConsumer:
        await orchestrator.start()

        # Verify consumer created with enable_auto_commit=False
        MockConsumer.assert_called_once()
        call_kwargs = MockConsumer.call_args[1]
        assert call_kwargs["enable_auto_commit"] is False
```

**Expected Behavior:** Auto-commit disabled (manual control)

---

#### Test Suite: Error Handling

**Test 46: test_send_to_failed_topic**
```python
@pytest.mark.asyncio
async def test_send_to_failed_topic():
    """Test sending failed request to failed topic."""
    orchestrator = VerificationOrchestrator(
        kafka_brokers="localhost:9092",
        consumer_group="test-group",
        hupyy_client=Mock(),
        feature_flag_service=Mock(),
    )
    orchestrator.producer = AsyncMock(spec=AIOKafkaProducer)

    request = VerificationRequest(
        request_id="req_1",
        content="Test content",
        nl_query="Find admins",
    )

    metadata = {"org_id": "org_1"}
    error_message = "Network timeout"

    await orchestrator.send_to_failed_topic(request, metadata, error_message)

    orchestrator.producer.send.assert_called_once_with(
        "verification_failed", value=ANY
    )

    # Verify error message included
    call_args = orchestrator.producer.send.call_args[1]
    message = call_args["value"]
    assert message["error_message"] == "Network timeout"
```

**Expected Behavior:** Failed requests sent to failed topic

---

**Test 47: test_send_to_dlq**
```python
@pytest.mark.asyncio
async def test_send_to_dlq():
    """Test sending malformed message to DLQ."""
    orchestrator = VerificationOrchestrator(
        kafka_brokers="localhost:9092",
        consumer_group="test-group",
        hupyy_client=Mock(),
        feature_flag_service=Mock(),
    )
    orchestrator.producer = AsyncMock(spec=AIOKafkaProducer)

    malformed_message = {"invalid": "data"}
    error_reason = "Missing required field: request_id"

    await orchestrator.send_to_dlq(malformed_message, error_reason)

    orchestrator.producer.send.assert_called_once_with(
        "verify_chunks_dlq", value=ANY
    )

    # Verify DLQ message format
    call_args = orchestrator.producer.send.call_args[1]
    dlq_message = call_args["value"]
    assert dlq_message["original_message"] == malformed_message
    assert dlq_message["error_reason"] == error_reason
```

**Expected Behavior:** Malformed messages sent to DLQ

---

#### Test Suite: Graceful Shutdown

**Test 48: test_graceful_shutdown**
```python
@pytest.mark.asyncio
async def test_graceful_shutdown():
    """Test graceful shutdown on signal."""
    orchestrator = VerificationOrchestrator(
        kafka_brokers="localhost:9092",
        consumer_group="test-group",
        hupyy_client=Mock(),
        feature_flag_service=Mock(),
    )
    orchestrator.consumer = AsyncMock(spec=AIOKafkaConsumer)
    orchestrator.producer = AsyncMock(spec=AIOKafkaProducer)
    orchestrator.hupyy_client = AsyncMock(spec=HupyyClient)

    await orchestrator.stop()

    # Verify all components stopped
    orchestrator.consumer.stop.assert_called_once()
    orchestrator.producer.stop.assert_called_once()
    orchestrator.hupyy_client.close.assert_called_once()
    assert orchestrator.shutdown_requested is True
```

**Expected Behavior:** Clean shutdown of all resources

---

**Test 49: test_batch_processing_with_retry**
```python
@pytest.mark.asyncio
async def test_batch_processing_with_retry(mock_hupyy_client):
    """Test batch processing with retry on failure."""
    # First call fails, individual retries succeed
    mock_hupyy_client.verify_parallel.side_effect = Exception("Batch failed")
    mock_hupyy_client.verify.return_value = VerificationResult(
        request_id="req_1",
        chunk_index=0,
        verdict=VerificationVerdict.SAT,
        confidence=0.95,
        duration_seconds=60.0,
        cached=False,
    )

    orchestrator = VerificationOrchestrator(
        kafka_brokers="localhost:9092",
        consumer_group="test-group",
        hupyy_client=mock_hupyy_client,
        feature_flag_service=Mock(),
    )
    orchestrator.producer = AsyncMock(spec=AIOKafkaProducer)

    message = Mock()
    message.value = {
        "request_id": "req_1",
        "content": "Test content",
        "nl_query": "Find admins",
        "timestamp": datetime.utcnow().isoformat(),
    }

    await orchestrator.process_batch([message])

    # Verify retry called
    mock_hupyy_client.verify.assert_called_once()
```

**Expected Behavior:** Individual retry on batch failure

---

**Test 50: test_parallel_verification_concurrency**
```python
@pytest.mark.asyncio
async def test_parallel_verification_concurrency(mock_hupyy_client):
    """Test parallel verification respects max_concurrency."""
    orchestrator = VerificationOrchestrator(
        kafka_brokers="localhost:9092",
        consumer_group="test-group",
        hupyy_client=mock_hupyy_client,
        feature_flag_service=Mock(),
        max_concurrency=3,
    )

    # Create multiple requests
    messages = [
        Mock(
            value={
                "request_id": f"req_{i}",
                "content": f"Content {i}",
                "nl_query": "Test",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        for i in range(10)
    ]

    await orchestrator.process_batch(messages)

    # Verify max_concurrency passed to client
    call_args = mock_hupyy_client.verify_parallel.call_args
    assert call_args[1]["max_concurrency"] == 3
```

**Expected Behavior:** Concurrency limit respected

---

## 2. TypeScript Backend Tests

### 2.1 File: `backend/nodejs/apps/src/modules/enterprise_search/validators/__tests__/es_validators.spec.ts`

**Purpose:** Test validation schemas for verification_enabled field

**Test Count:** 8 tests

**Dependencies to Mock:** None (pure validation logic)

---

#### Test Suite: Verification Enabled Validation

**Test 51: test_verification_enabled_default_false**
```typescript
describe('es_validators', () => {
  test('should default verification_enabled to false', () => {
    const result = verificationSchema.parse({})

    expect(result.verification_enabled).toBe(false)
  })
})
```

**Expected Behavior:** Default value is false

---

**Test 52: test_verification_enabled_accepts_true**
```typescript
test('should accept verification_enabled=true', () => {
  const result = verificationSchema.parse({
    verification_enabled: true,
  })

  expect(result.verification_enabled).toBe(true)
})
```

**Expected Behavior:** True value accepted

---

**Test 53: test_verification_enabled_accepts_false**
```typescript
test('should accept verification_enabled=false', () => {
  const result = verificationSchema.parse({
    verification_enabled: false,
  })

  expect(result.verification_enabled).toBe(false)
})
```

**Expected Behavior:** False value accepted

---

**Test 54: test_verification_enabled_rejects_non_boolean**
```typescript
test('should reject non-boolean verification_enabled', () => {
  expect(() => {
    verificationSchema.parse({
      verification_enabled: 'true',  // String instead of boolean
    })
  }).toThrow()
})
```

**Expected Behavior:** ValidationError for non-boolean

---

**Test 55: test_verification_enabled_optional**
```typescript
test('should treat verification_enabled as optional', () => {
  const result = verificationSchema.parse({
    query: 'test query',
    // verification_enabled omitted
  })

  expect(result).toHaveProperty('verification_enabled')
  expect(result.verification_enabled).toBe(false)
})
```

**Expected Behavior:** Optional field with default

---

**Test 56: test_verification_schema_full_payload**
```typescript
test('should validate full payload with verification_enabled', () => {
  const payload = {
    query: 'Find all admin users',
    filters: { status: 'active' },
    verification_enabled: true,
  }

  const result = verificationSchema.parse(payload)

  expect(result.query).toBe('Find all admin users')
  expect(result.verification_enabled).toBe(true)
})
```

**Expected Behavior:** Full payload validated

---

**Test 57: test_verification_schema_serialization**
```typescript
test('should serialize verification_enabled correctly', () => {
  const data = {
    query: 'test',
    verification_enabled: true,
  }

  const validated = verificationSchema.parse(data)
  const serialized = JSON.stringify(validated)
  const deserialized = JSON.parse(serialized)

  expect(deserialized.verification_enabled).toBe(true)
})
```

**Expected Behavior:** Correct serialization/deserialization

---

**Test 58: test_verification_schema_type_coercion**
```typescript
test('should not coerce types for verification_enabled', () => {
  expect(() => {
    verificationSchema.parse({
      verification_enabled: 1,  // Number instead of boolean
    })
  }).toThrow()
})
```

**Expected Behavior:** No type coercion

---

### 2.2 File: `backend/nodejs/apps/src/modules/enterprise_search/controller/__tests__/es_controller.spec.ts`

**Purpose:** Test controller methods for verification_enabled extraction and forwarding

**Test Count:** 7 tests

**Dependencies to Mock:**
- Python FastAPI service (HTTP calls)
- Request/Response objects

---

#### Test Suite: ES Controller

**Test 59: test_controller_extracts_verification_enabled**
```typescript
describe('es_controller', () => {
  test('should extract verification_enabled from request', async () => {
    const mockPythonService = jest.fn().mockResolvedValue({
      data: { results: [] },
    })

    const req = {
      body: {
        query: 'Find admins',
        verification_enabled: true,
      },
    }
    const res = { json: jest.fn(), status: jest.fn().mockReturnThis() }

    const controller = new ESController(mockPythonService)
    await controller.search(req, res)

    // Verify verification_enabled passed to Python service
    expect(mockPythonService).toHaveBeenCalledWith(
      expect.objectContaining({
        verification_enabled: true,
      })
    )
  })
})
```

**Expected Behavior:** verification_enabled extracted and forwarded

---

**Test 60: test_controller_defaults_verification_enabled**
```typescript
test('should default verification_enabled to false', async () => {
  const mockPythonService = jest.fn().mockResolvedValue({
    data: { results: [] },
  })

  const req = {
    body: {
      query: 'Find admins',
      // verification_enabled omitted
    },
  }
  const res = { json: jest.fn(), status: jest.fn().mockReturnThis() }

  const controller = new ESController(mockPythonService)
  await controller.search(req, res)

  expect(mockPythonService).toHaveBeenCalledWith(
    expect.objectContaining({
      verification_enabled: false,
    })
  )
})
```

**Expected Behavior:** Defaults to false when omitted

---

**Test 61: test_controller_handles_verification_results**
```typescript
test('should handle verification results in response', async () => {
  const mockPythonService = jest.fn().mockResolvedValue({
    data: {
      results: [{ id: '1', content: 'Result 1' }],
      verification_results: [
        { chunk_index: 0, verdict: 'SAT', confidence: 0.95 },
      ],
    },
  })

  const req = {
    body: { query: 'Find admins', verification_enabled: true },
  }
  const res = { json: jest.fn(), status: jest.fn().mockReturnThis() }

  const controller = new ESController(mockPythonService)
  await controller.search(req, res)

  expect(res.json).toHaveBeenCalledWith(
    expect.objectContaining({
      verification_results: expect.arrayContaining([
        expect.objectContaining({ verdict: 'SAT' }),
      ]),
    })
  )
})
```

**Expected Behavior:** Verification results forwarded to client

---

**Test 62: test_controller_handles_verification_error**
```typescript
test('should handle verification errors gracefully', async () => {
  const mockPythonService = jest.fn().mockResolvedValue({
    data: {
      results: [{ id: '1', content: 'Result 1' }],
      verification_error: 'Hupyy API timeout',
    },
  })

  const req = {
    body: { query: 'Find admins', verification_enabled: true },
  }
  const res = { json: jest.fn(), status: jest.fn().mockReturnThis() }

  const controller = new ESController(mockPythonService)
  await controller.search(req, res)

  // Should still return results, with error info
  expect(res.json).toHaveBeenCalledWith(
    expect.objectContaining({
      results: expect.any(Array),
      verification_error: 'Hupyy API timeout',
    })
  )
})
```

**Expected Behavior:** Graceful error handling

---

**Test 63: test_controller_forwards_payload_to_python**
```typescript
test('should forward full payload to Python service', async () => {
  const mockPythonService = jest.fn().mockResolvedValue({
    data: { results: [] },
  })

  const req = {
    body: {
      query: 'Find admins',
      filters: { status: 'active' },
      verification_enabled: true,
    },
  }
  const res = { json: jest.fn(), status: jest.fn().mockReturnThis() }

  const controller = new ESController(mockPythonService)
  await controller.search(req, res)

  expect(mockPythonService).toHaveBeenCalledWith({
    query: 'Find admins',
    filters: { status: 'active' },
    verification_enabled: true,
  })
})
```

**Expected Behavior:** Full payload forwarded

---

**Test 64: test_controller_error_response**
```typescript
test('should return error response on Python service failure', async () => {
  const mockPythonService = jest
    .fn()
    .mockRejectedValue(new Error('Service unavailable'))

  const req = {
    body: { query: 'Find admins', verification_enabled: true },
  }
  const res = { json: jest.fn(), status: jest.fn().mockReturnThis() }

  const controller = new ESController(mockPythonService)
  await controller.search(req, res)

  expect(res.status).toHaveBeenCalledWith(500)
  expect(res.json).toHaveBeenCalledWith(
    expect.objectContaining({
      error: expect.any(String),
    })
  )
})
```

**Expected Behavior:** 500 error on service failure

---

**Test 65: test_controller_validation_error**
```typescript
test('should return 400 on validation error', async () => {
  const req = {
    body: {
      query: 'Find admins',
      verification_enabled: 'true',  // Invalid type
    },
  }
  const res = { json: jest.fn(), status: jest.fn().mockReturnThis() }

  const controller = new ESController(jest.fn())
  await controller.search(req, res)

  expect(res.status).toHaveBeenCalledWith(400)
  expect(res.json).toHaveBeenCalledWith(
    expect.objectContaining({
      error: expect.stringContaining('validation'),
    })
  )
})
```

**Expected Behavior:** 400 error on validation failure

---

## 3. Frontend React Tests

### 3.1 File: `frontend/src/sections/qna/chatbot/components/__tests__/HupyyControls.spec.tsx`

**Purpose:** Test HupyyControls checkbox component rendering and interactions

**Test Count:** 10 tests

**Dependencies to Mock:** None (React Testing Library)

---

#### Test Suite: Component Rendering

**Test 66: test_checkbox_renders**
```typescript
import { render, screen } from '@testing-library/react'
import { HupyyControls } from '../HupyyControls'

describe('HupyyControls', () => {
  test('should render checkbox', () => {
    render(<HupyyControls onToggle={jest.fn()} enabled={false} />)

    const checkbox = screen.getByRole('checkbox', {
      name: /enable verification/i,
    })

    expect(checkbox).toBeInTheDocument()
  })
})
```

**Expected Behavior:** Checkbox visible

---

**Test 67: test_checkbox_unchecked_by_default**
```typescript
test('should be unchecked by default', () => {
  render(<HupyyControls onToggle={jest.fn()} enabled={false} />)

  const checkbox = screen.getByRole('checkbox')

  expect(checkbox).not.toBeChecked()
})
```

**Expected Behavior:** Unchecked initially

---

**Test 68: test_checkbox_checked_when_enabled**
```typescript
test('should be checked when enabled=true', () => {
  render(<HupyyControls onToggle={jest.fn()} enabled={true} />)

  const checkbox = screen.getByRole('checkbox')

  expect(checkbox).toBeChecked()
})
```

**Expected Behavior:** Checked when prop is true

---

**Test 69: test_tooltip_visible_on_hover**
```typescript
test('should show tooltip on hover', async () => {
  const { user } = render(<HupyyControls onToggle={jest.fn()} enabled={false} />)

  const checkbox = screen.getByRole('checkbox')
  await user.hover(checkbox)

  const tooltip = await screen.findByText(
    /SMT verification uses formal logic/i
  )

  expect(tooltip).toBeInTheDocument()
})
```

**Expected Behavior:** Tooltip shown on hover

---

#### Test Suite: User Interactions

**Test 70: test_checkbox_toggle_calls_callback**
```typescript
test('should call onToggle when clicked', async () => {
  const onToggle = jest.fn()
  const { user } = render(<HupyyControls onToggle={onToggle} enabled={false} />)

  const checkbox = screen.getByRole('checkbox')
  await user.click(checkbox)

  expect(onToggle).toHaveBeenCalledTimes(1)
  expect(onToggle).toHaveBeenCalledWith(true)
})
```

**Expected Behavior:** Callback invoked on click

---

**Test 71: test_checkbox_toggle_from_true_to_false**
```typescript
test('should toggle from true to false', async () => {
  const onToggle = jest.fn()
  const { user } = render(<HupyyControls onToggle={onToggle} enabled={true} />)

  const checkbox = screen.getByRole('checkbox')
  await user.click(checkbox)

  expect(onToggle).toHaveBeenCalledWith(false)
})
```

**Expected Behavior:** Toggles from checked to unchecked

---

**Test 72: test_checkbox_disabled_state**
```typescript
test('should be disabled when disabled=true', () => {
  render(<HupyyControls onToggle={jest.fn()} enabled={false} disabled={true} />)

  const checkbox = screen.getByRole('checkbox')

  expect(checkbox).toBeDisabled()
})
```

**Expected Behavior:** Disabled when prop is true

---

#### Test Suite: Accessibility

**Test 73: test_checkbox_aria_label**
```typescript
test('should have proper aria-label', () => {
  render(<HupyyControls onToggle={jest.fn()} enabled={false} />)

  const checkbox = screen.getByRole('checkbox', {
    name: /enable verification/i,
  })

  expect(checkbox).toHaveAccessibleName()
})
```

**Expected Behavior:** Accessible label present

---

**Test 74: test_keyboard_navigation**
```typescript
test('should be keyboard accessible', async () => {
  const onToggle = jest.fn()
  const { user } = render(<HupyyControls onToggle={onToggle} enabled={false} />)

  const checkbox = screen.getByRole('checkbox')

  // Tab to checkbox
  await user.tab()
  expect(checkbox).toHaveFocus()

  // Press Space to toggle
  await user.keyboard(' ')
  expect(onToggle).toHaveBeenCalledWith(true)
})
```

**Expected Behavior:** Keyboard navigation works

---

**Test 75: test_tooltip_aria_describedby**
```typescript
test('should have aria-describedby for tooltip', () => {
  render(<HupyyControls onToggle={jest.fn()} enabled={false} />)

  const checkbox = screen.getByRole('checkbox')

  expect(checkbox).toHaveAttribute('aria-describedby')
})
```

**Expected Behavior:** Tooltip linked via aria-describedby

---

## 4. Summary

### Test Count by File

| File | Test Count | Purpose |
|------|-----------|---------|
| `test_models.py` | 15 | Pydantic model validation |
| `test_hupyy_client.py` | 20 | HTTP client, caching, errors |
| `test_orchestrator.py` | 15 | Kafka consumption, publishing |
| `es_validators.spec.ts` | 8 | Validation schemas |
| `es_controller.spec.ts` | 7 | Controller logic |
| `HupyyControls.spec.tsx` | 10 | React component |
| **Total** | **75** | **Complete unit test suite** |

### Coverage Expectations

| Component | Line Coverage | Branch Coverage | Function Coverage |
|-----------|--------------|-----------------|-------------------|
| Python Models | ≥95% | ≥90% | ≥95% |
| Python Client | ≥90% | ≥85% | ≥90% |
| Python Orchestrator | ≥85% | ≥80% | ≥85% |
| TypeScript Validators | ≥90% | ≥85% | ≥90% |
| TypeScript Controller | ≥85% | ≥80% | ≥85% |
| React Components | ≥80% | ≥75% | ≥80% |
| **Overall** | **≥90%** | **≥85%** | **≥95%** |

### Execution Time Goals

- **Python Tests**: <30 seconds
- **TypeScript Tests**: <20 seconds
- **React Tests**: <10 seconds
- **Total**: <1 minute

### Key Patterns Used

1. **Arrange-Act-Assert** - Clear test structure
2. **Descriptive Names** - test_what_condition_expected
3. **Mocking** - Mock external dependencies
4. **Fixtures** - Reusable test data
5. **Parametrization** - Test multiple scenarios
6. **Async Testing** - Proper async/await handling

---

## Conclusion

This unit test specification provides a comprehensive blueprint for **75 unit tests** covering all critical components of the Hupyy SMT verification integration. Each test is designed to be:

- **Fast**: <100ms execution time
- **Isolated**: No external dependencies
- **Deterministic**: Same result every time
- **Maintainable**: Clear naming and structure
- **Comprehensive**: High code coverage

These tests form the **foundation (70%)** of our testing pyramid and will provide rapid feedback during development.
