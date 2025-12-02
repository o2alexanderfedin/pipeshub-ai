# Concrete Test Scenarios for Hupyy SMT Verification

**Date:** November 30, 2025
**Purpose:** Real-world test scenarios with example data and expected outcomes

---

## Scenario 1: Successful Verification (SAT)

### Input
```json
{
  "request_id": "req_sat_001",
  "content": "All prime numbers greater than 2 are odd",
  "nl_query": "Verify: All primes > 2 are odd",
  "chunk_index": 0,
  "total_chunks": 1,
  "verification_enabled": true
}
```

### Expected Hupyy API Call
```json
{
  "informal_text": "All prime numbers greater than 2 are odd",
  "skip_formalization": false,
  "enrich": false
}
```

### Expected Hupyy Response
```json
{
  "check_sat_result": "SAT",
  "formalization_similarity": 0.92,
  "model": {},
  "proof": {
    "summary": "The statement is mathematically valid. All prime numbers except 2 are odd because they cannot be divisible by 2.",
    "steps": ["Assumption: p is prime and p > 2", "If p is even, then p = 2k for some k", "Then 2 divides p, contradicting primality", "Therefore p must be odd"]
  },
  "smt_lib_code": "(assert (forall ((p Int)) (=> (and (is-prime p) (> p 2)) (is-odd p))))",
  "formal_text": "∀p ∈ ℤ: (isPrime(p) ∧ p > 2) → isOdd(p)",
  "informal_text": "All prime numbers greater than 2 are odd",
  "solver_success": true,
  "passed_all_checks": true,
  "metrics": {
    "total_time_ms": 1250,
    "formalization_time_ms": 450,
    "solver_time_ms": 800
  }
}
```

### Expected Verification Result
```json
{
  "request_id": "req_sat_001",
  "chunk_index": 0,
  "verdict": "SAT",
  "confidence": 0.92,
  "formalization_similarity": 0.92,
  "explanation": "The statement is mathematically valid. All prime numbers except 2 are odd because they cannot be divisible by 2.",
  "failure_mode": null,
  "metadata": {
    "model": {},
    "proof": {...},
    "smt_lib_code": "(...)",
    "formal_text": "∀p ∈ ℤ: (isPrime(p) ∧ p > 2) → isOdd(p)",
    "solver_success": true
  },
  "duration_seconds": 62.3,
  "cached": false,
  "timestamp": "2025-11-30T10:15:42Z"
}
```

### Expected UI Display
- ✅ Verification badge: "Verified (SAT)"
- ✅ Confidence: 92%
- ✅ Proof summary visible
- ✅ Formal logic displayed

---

## Scenario 2: Failed Verification (UNSAT)

### Input
```json
{
  "request_id": "req_unsat_001",
  "content": "2 + 2 = 5",
  "nl_query": "Is 2 + 2 equal to 5?",
  "verification_enabled": true
}
```

### Expected Hupyy Response
```json
{
  "check_sat_result": "UNSAT",
  "formalization_similarity": 0.98,
  "proof": {
    "summary": "The statement is mathematically false. 2 + 2 equals 4, not 5.",
    "contradiction": "The assertion (= (+ 2 2) 5) contradicts the axioms of arithmetic"
  },
  "smt_lib_code": "(assert (= (+ 2 2) 5))",
  "formal_text": "2 + 2 = 5",
  "solver_success": true,
  "passed_all_checks": false,
  "metrics": {
    "total_time_ms": 890
  }
}
```

### Expected Verification Result
```json
{
  "request_id": "req_unsat_001",
  "chunk_index": 0,
  "verdict": "UNSAT",
  "confidence": 0.98,
  "formalization_similarity": 0.98,
  "explanation": "The statement is mathematically false. 2 + 2 equals 4, not 5.",
  "failure_mode": null,
  "duration_seconds": 45.2,
  "cached": false
}
```

### Expected UI Display
- ❌ Verification badge: "Verification Failed (UNSAT)"
- ❌ Confidence: 98%
- ❌ Explanation: "Statement is mathematically false"
- ❌ Red indicator

---

## Scenario 3: Inconclusive Verification (UNKNOWN)

### Input
```json
{
  "request_id": "req_unknown_001",
  "content": "The halting problem is decidable",
  "nl_query": "Can we decide if any program halts?",
  "verification_enabled": true
}
```

### Expected Hupyy Response
```json
{
  "check_sat_result": "UNKNOWN",
  "formalization_similarity": 0.45,
  "explanation": "The statement involves undecidable properties. The solver cannot determine satisfiability within resource limits.",
  "smt_lib_code": "(...complex undecidable formula...)",
  "solver_success": false,
  "metrics": {
    "total_time_ms": 150000,
    "timeout": true
  }
}
```

### Expected Verification Result
```json
{
  "request_id": "req_unknown_001",
  "chunk_index": 0,
  "verdict": "UNKNOWN",
  "confidence": 0.45,
  "formalization_similarity": 0.45,
  "explanation": "The statement involves undecidable properties. The solver cannot determine satisfiability within resource limits.",
  "failure_mode": null,
  "duration_seconds": 150.5,
  "cached": false
}
```

### Expected UI Display
- ⚠️ Verification badge: "Inconclusive (UNKNOWN)"
- ⚠️ Confidence: 45%
- ⚠️ Explanation: "Cannot determine within time limits"
- ⚠️ Yellow/orange indicator

---

## Scenario 4: Timeout

### Input
```json
{
  "request_id": "req_timeout_001",
  "content": "Very complex mathematical statement requiring extensive computation...",
  "nl_query": "Verify complex statement",
  "verification_enabled": true
}
```

### Expected Behavior
- Hupyy API takes >150 seconds
- Client timeout triggers

### Expected Verification Result
```json
{
  "request_id": "req_timeout_001",
  "chunk_index": 0,
  "verdict": "UNKNOWN",
  "confidence": 0.0,
  "formalization_similarity": null,
  "explanation": null,
  "failure_mode": "timeout",
  "duration_seconds": 150.0,
  "cached": false
}
```

### Expected UI Display
- ⏱️ Timeout indicator
- ⏱️ Message: "Verification timed out. Try simplifying the query."
- ⏱️ Gray badge

---

## Scenario 5: Hupyy API Error

### Input
```json
{
  "request_id": "req_error_001",
  "content": "Test query",
  "nl_query": "Test",
  "verification_enabled": true
}
```

### Hupyy API Response
```
HTTP 500 Internal Server Error
{
  "error": "Internal solver error",
  "message": "SMT solver crashed"
}
```

### Expected Verification Result
```json
{
  "request_id": "req_error_001",
  "chunk_index": 0,
  "verdict": "ERROR",
  "confidence": 0.0,
  "formalization_similarity": null,
  "explanation": "Internal solver error",
  "failure_mode": "network_error",
  "duration_seconds": 5.2,
  "cached": false
}
```

### Expected UI Display
- ❌ Error message: "Verification service temporarily unavailable"
- ❌ Chat continues to function normally
- ❌ Search results displayed without verification

---

## Scenario 6: Cached Result

### Setup
Previous request for "2 + 2 = 4" returned SAT and was cached.

### Input
```json
{
  "request_id": "req_cache_001",
  "content": "2 + 2 = 4",
  "nl_query": "Is 2+2=4?",
  "verification_enabled": true
}
```

### Expected Behavior
1. Check cache for "2 + 2 = 4"
2. Cache hit - return cached result
3. NO HTTP call to Hupyy
4. Very fast response (<1 second)

### Expected Verification Result
```json
{
  "request_id": "req_cache_001",
  "chunk_index": 0,
  "verdict": "SAT",
  "confidence": 0.95,
  "formalization_similarity": 0.92,
  "explanation": "(cached) 2 + 2 equals 4",
  "duration_seconds": 0.02,
  "cached": true,
  "timestamp": "2025-11-30T10:20:15Z"
}
```

### Expected UI Display
- ✅ Same as SAT scenario
- ✅ Optional: "Cached result" indicator

---

## Scenario 7: Multiple Chunks

### Input (Large Content Chunked)
```json
{
  "request_id": "req_chunks_001",
  "chunks": [
    {
      "chunk_index": 0,
      "total_chunks": 3,
      "content": "First chunk content..."
    },
    {
      "chunk_index": 1,
      "total_chunks": 3,
      "content": "Second chunk content..."
    },
    {
      "chunk_index": 2,
      "total_chunks": 3,
      "content": "Third chunk content..."
    }
  ],
  "nl_query": "Verify large document",
  "verification_enabled": true
}
```

### Expected Behavior
1. Publish 3 messages to Kafka (verify_chunks topic)
2. Orchestrator processes all 3 chunks in parallel
3. Results aggregated

### Expected Verification Results
```json
[
  {
    "request_id": "req_chunks_001",
    "chunk_index": 0,
    "verdict": "SAT",
    "confidence": 0.90
  },
  {
    "request_id": "req_chunks_001",
    "chunk_index": 1,
    "verdict": "SAT",
    "confidence": 0.88
  },
  {
    "request_id": "req_chunks_001",
    "chunk_index": 2,
    "verdict": "UNSAT",
    "confidence": 0.92
  }
]
```

### Expected UI Display
- ✅ Overall verdict: "Partially verified (2/3 SAT)"
- ✅ Chunk-by-chunk breakdown available
- ⚠️ Highlight chunk 2 as failed

---

## Scenario 8: Verification Disabled

### Input
```json
{
  "request_id": "req_disabled_001",
  "content": "Any query",
  "nl_query": "Find documents",
  "verification_enabled": false
}
```

### Expected Behavior
1. NodeJS API receives request
2. verification_enabled=false
3. NO message published to Kafka
4. Search proceeds normally without verification

### Expected Response
```json
{
  "results": [...search results...],
  "verification_results": null
}
```

### Expected UI Display
- ✅ Search results displayed normally
- ✅ No verification badges
- ✅ Checkbox unchecked

---

## Performance Test Scenarios

### Scenario 9: High Load (100 Concurrent Requests)
- **Input:** 100 verification requests simultaneously
- **Expected:** All processed within 5 minutes
- **Expected:** No timeouts or failures
- **Expected:** Kafka consumers handle load

### Scenario 10: Large Batch (1000 Chunks)
- **Input:** Single document split into 1000 chunks
- **Expected:** Parallel processing (5 concurrent)
- **Expected:** Results aggregated correctly
- **Expected:** Completion within 30 minutes

---

## Edge Case Scenarios

### Scenario 11: Empty Query
- **Input:** `{"content": "", "verification_enabled": true}`
- **Expected:** ValidationError before API call

### Scenario 12: Very Long Query (>10KB)
- **Input:** Query with 15KB content
- **Expected:** Automatic chunking into 2 chunks

### Scenario 13: Special Characters
- **Input:** `{"content": "∀x ∈ ℝ: x² ≥ 0"}`
- **Expected:** Proper encoding, successful verification

### Scenario 14: Network Interruption
- **Input:** Valid request, network fails mid-call
- **Expected:** ERROR verdict with NETWORK_ERROR failure mode

---

## Summary

These scenarios provide concrete examples for:
- ✅ Manual testing
- ✅ Automated test data
- ✅ Documentation examples
- ✅ Training materials
- ✅ Debugging reference

Each scenario includes complete input/output examples with expected behavior at every layer (API, Kafka, UI).
