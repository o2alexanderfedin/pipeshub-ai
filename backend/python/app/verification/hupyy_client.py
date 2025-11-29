"""
Hupyy API client with circuit breaker and caching.

Provides async, fault-tolerant access to Hupyy SMT verification service.
Features:
- Async HTTP client (httpx)
- Circuit breaker protection
- Input chunking (>10KB)
- Simple caching
- Parallel verification
- Comprehensive metrics
"""

import asyncio
import logging
from typing import List, Optional, Tuple

import httpx

from app.infrastructure.cache import VerificationCache
from app.infrastructure.metrics import VerificationMetrics, get_metrics
from app.verification.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from app.verification.models import (
    ChunkingConfig,
    FailureMode,
    HupyyRequest,
    HupyyResponse,
    VerificationRequest,
    VerificationResult,
    VerificationVerdict,
)


class HupyyClient:
    """
    Client for Hupyy SMT verification API.

    Handles:
    - HTTP requests to Hupyy
    - Circuit breaker protection
    - Caching
    - Chunking large inputs
    - Parallel processing
    """

    def __init__(
        self,
        api_url: str,
        cache: Optional[VerificationCache] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        metrics: Optional[VerificationMetrics] = None,
        chunking_config: Optional[ChunkingConfig] = None,
        logger: Optional[logging.Logger] = None,
        timeout_seconds: int = 150,
    ) -> None:
        """
        Initialize Hupyy client.

        Args:
            api_url: Hupyy API base URL
            cache: Optional verification cache
            circuit_breaker: Optional circuit breaker
            metrics: Optional metrics collector
            chunking_config: Optional chunking configuration
            logger: Optional logger instance
            timeout_seconds: Request timeout (default: 150s for 1-2 min calls)
        """
        self.api_url = api_url.rstrip("/")
        self.cache = cache
        self.circuit_breaker = circuit_breaker or CircuitBreaker(
            config=CircuitBreakerConfig(timeout_seconds=timeout_seconds)
        )
        self.metrics = metrics or get_metrics()
        self.chunking_config = chunking_config or ChunkingConfig()
        self.logger = logger or logging.getLogger(__name__)
        self.timeout_seconds = timeout_seconds

        # HTTP client
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds, connect=5.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    async def close(self) -> None:
        """Close HTTP client."""
        await self.http_client.aclose()

    async def verify(self, request: VerificationRequest) -> VerificationResult:
        """
        Verify a single chunk.

        Args:
            request: Verification request

        Returns:
            Verification result
        """
        import time

        start_time = time.time()

        # Check cache first
        if self.cache:
            cached_result = await self.cache.get(request.content)
            if cached_result:
                self.logger.info(f"✅ Cache hit for request {request.request_id}")
                self.metrics.record_cache_operation("get", "hit")
                self.metrics.record_verification_request("cache_hit", 0.0)

                return VerificationResult(
                    request_id=request.request_id,
                    chunk_index=request.chunk_index,
                    verdict=VerificationVerdict(cached_result["verdict"]),
                    confidence=cached_result["confidence"],
                    formalization_similarity=cached_result.get(
                        "formalization_similarity"
                    ),
                    explanation=cached_result.get("explanation"),
                    metadata=cached_result.get("metadata", {}),
                    duration_seconds=time.time() - start_time,
                    cached=True,
                )

            self.metrics.record_cache_operation("get", "miss")

        # Make API call with circuit breaker
        try:
            hupyy_response = await self.circuit_breaker.call(
                self._make_api_call, request
            )

            duration = time.time() - start_time

            # Create result
            result = VerificationResult(
                request_id=request.request_id,
                chunk_index=request.chunk_index,
                verdict=hupyy_response.verdict,
                confidence=hupyy_response.confidence,
                formalization_similarity=hupyy_response.formalization_similarity,
                explanation=hupyy_response.explanation,
                metadata=hupyy_response.metadata,
                duration_seconds=duration,
                cached=False,
            )

            # Cache successful results
            if self.cache and hupyy_response.verdict in [
                VerificationVerdict.SAT,
                VerificationVerdict.UNSAT,
            ]:
                await self.cache.set(
                    request.content,
                    {
                        "verdict": hupyy_response.verdict.value,
                        "confidence": hupyy_response.confidence,
                        "formalization_similarity": hupyy_response.formalization_similarity,
                        "explanation": hupyy_response.explanation,
                        "metadata": hupyy_response.metadata,
                    },
                )
                self.metrics.record_cache_operation("set", "success")

            # Record metrics
            self.metrics.record_verification_request("success", duration)
            self.metrics.record_chunk_processed(hupyy_response.verdict.value)

            return result

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            self.logger.error(f"Verification timeout for request {request.request_id}")
            self.metrics.record_verification_request("timeout", duration)

            return VerificationResult(
                request_id=request.request_id,
                chunk_index=request.chunk_index,
                verdict=VerificationVerdict.UNKNOWN,
                confidence=0.0,
                failure_mode=FailureMode.TIMEOUT,
                duration_seconds=duration,
                cached=False,
            )

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"Verification failed for request {request.request_id}: {str(e)}"
            )
            self.metrics.record_verification_request("failure", duration)
            self.metrics.record_chunk_processed("ERROR")

            return VerificationResult(
                request_id=request.request_id,
                chunk_index=request.chunk_index,
                verdict=VerificationVerdict.ERROR,
                confidence=0.0,
                failure_mode=FailureMode.NETWORK_ERROR,
                explanation=str(e),
                duration_seconds=duration,
                cached=False,
            )

    async def _make_api_call(self, request: VerificationRequest) -> HupyyResponse:
        """
        Make actual API call to Hupyy.

        Args:
            request: Verification request

        Returns:
            Hupyy response

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        # Prepare Hupyy request
        hupyy_request = HupyyRequest(
            informal_text=request.content,
            skip_formalization=False,
            enrich=False,  # Always False
        )

        self.logger.info(
            f"🔍 Calling Hupyy API for request {request.request_id} "
            f"(chunk {request.chunk_index + 1}/{request.total_chunks})"
        )

        # Make HTTP request
        response = await self.http_client.post(
            f"{self.api_url}/pipeline/process",
            json=hupyy_request.model_dump(),
            headers={"Content-Type": "application/json"},
        )

        response.raise_for_status()

        # Parse response using the parser
        response_data = response.json()
        return HupyyResponse.from_hupyy_process_response(response_data)

    async def verify_parallel(
        self, requests: List[VerificationRequest], max_concurrency: int = 5
    ) -> List[VerificationResult]:
        """
        Verify multiple chunks in parallel.

        Args:
            requests: List of verification requests
            max_concurrency: Maximum concurrent verifications (default: 5)

        Returns:
            List of verification results
        """
        self.logger.info(f"🚀 Starting parallel verification of {len(requests)} chunks")

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrency)

        async def verify_with_semaphore(req: VerificationRequest) -> VerificationResult:
            async with semaphore:
                return await self.verify(req)

        # Execute in parallel
        results = await asyncio.gather(
            *[verify_with_semaphore(req) for req in requests], return_exceptions=False
        )

        self.logger.info(
            f"✅ Completed parallel verification of {len(requests)} chunks"
        )
        return results

    def chunk_content(
        self,
        content: str,
        request_id: str,
        nl_query: str,
        source_document_id: Optional[str] = None,
    ) -> List[VerificationRequest]:
        """
        Split large content into chunks.

        Args:
            content: Content to chunk
            request_id: Request ID
            nl_query: Natural language query
            source_document_id: Optional source document ID

        Returns:
            List of verification requests (one per chunk)
        """
        content_bytes = content.encode("utf-8")
        max_size = self.chunking_config.max_chunk_size_bytes
        overlap = self.chunking_config.overlap_chars

        # If content fits in one chunk, return as-is
        if len(content_bytes) <= max_size:
            return [
                VerificationRequest(
                    request_id=request_id,
                    content=content,
                    chunk_index=0,
                    total_chunks=1,
                    nl_query=nl_query,
                    source_document_id=source_document_id,
                )
            ]

        # Split into chunks
        chunks = []
        start = 0

        while start < len(content):
            end = min(start + max_size, len(content))
            chunk = content[start:end]

            chunks.append(
                VerificationRequest(
                    request_id=request_id,
                    content=chunk,
                    chunk_index=len(chunks),
                    total_chunks=0,  # Will update after
                    nl_query=nl_query,
                    source_document_id=source_document_id,
                )
            )

            # Move start with overlap
            start = end - overlap if end < len(content) else end

        # Update total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)

        self.logger.info(
            f"📦 Split content into {len(chunks)} chunks "
            f"(max size: {max_size} bytes, overlap: {overlap} chars)"
        )

        return chunks
