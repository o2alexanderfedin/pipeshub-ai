"""
Prometheus metrics for Hupyy verification monitoring.

Tracks:
- Verification requests (counter)
- Verification duration (histogram)
- Success rate (gauge)
- Circuit breaker state (gauge)
- Cache hit rate (gauge)
- Queue depth (gauge)
"""

import logging
from enum import Enum
from typing import Optional

from prometheus_client import Counter, Gauge, Histogram, Info


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = 0  # Normal operation
    OPEN = 1  # Failures exceeded, blocking requests
    HALF_OPEN = 2  # Testing if service recovered


class VerificationMetrics:
    """
    Prometheus metrics for verification system.

    Provides comprehensive monitoring of:
    - Request volume and outcomes
    - Performance (latency)
    - Reliability (success rate, circuit breaker)
    - Efficiency (cache hit rate)
    - Load (queue depth)
    """

    def __init__(self, namespace: str = "hupyy", logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize verification metrics.

        Args:
            namespace: Prometheus namespace prefix
            logger: Optional logger instance
        """
        self.namespace = namespace
        self.logger = logger or logging.getLogger(__name__)

        # Request counters
        self.verification_requests_total = Counter(
            name=f"{namespace}_verification_requests_total",
            documentation="Total number of verification requests",
            labelnames=["status"],  # success, failure, timeout, cache_hit
        )

        # Duration histogram
        self.verification_duration_seconds = Histogram(
            name=f"{namespace}_verification_duration_seconds",
            documentation="Verification request duration in seconds",
            labelnames=["status"],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 240.0, 300.0],
        )

        # Success rate gauge
        self.verification_success_rate = Gauge(
            name=f"{namespace}_verification_success_rate",
            documentation="Verification success rate (0.0 to 1.0)",
        )

        # Circuit breaker state
        self.circuit_breaker_state = Gauge(
            name=f"{namespace}_circuit_breaker_state",
            documentation="Circuit breaker state (0=closed, 1=open, 2=half_open)",
        )

        # Cache metrics
        self.cache_hit_rate = Gauge(
            name=f"{namespace}_cache_hit_rate", documentation="Cache hit rate (0.0 to 1.0)"
        )

        self.cache_operations_total = Counter(
            name=f"{namespace}_cache_operations_total",
            documentation="Total cache operations",
            labelnames=["operation", "result"],  # get/set, hit/miss/error
        )

        # Queue metrics
        self.verification_queue_depth = Gauge(
            name=f"{namespace}_verification_queue_depth",
            documentation="Number of pending verification requests",
        )

        # Chunk processing
        self.chunks_processed_total = Counter(
            name=f"{namespace}_chunks_processed_total",
            documentation="Total chunks processed",
            labelnames=["verdict"],  # SAT, UNSAT, UNKNOWN, ERROR
        )

        # System info
        self.system_info = Info(name=f"{namespace}_system_info", documentation="System information")

        # Initialize counters
        self._total_requests = 0
        self._successful_requests = 0
        self._cache_hits = 0
        self._cache_requests = 0

        self.logger.info(f"✅ Initialized {namespace} verification metrics")

    def record_verification_request(self, status: str, duration_seconds: float) -> None:
        """
        Record a verification request.

        Args:
            status: Request status (success, failure, timeout, cache_hit)
            duration_seconds: Request duration
        """
        self.verification_requests_total.labels(status=status).inc()
        self.verification_duration_seconds.labels(status=status).observe(duration_seconds)

        # Update running totals for success rate
        self._total_requests += 1
        if status == "success":
            self._successful_requests += 1

        # Update success rate gauge
        if self._total_requests > 0:
            success_rate = self._successful_requests / self._total_requests
            self.verification_success_rate.set(success_rate)

    def record_chunk_processed(self, verdict: str) -> None:
        """
        Record a processed chunk.

        Args:
            verdict: Verification verdict (SAT, UNSAT, UNKNOWN, ERROR)
        """
        self.chunks_processed_total.labels(verdict=verdict).inc()

    def set_circuit_breaker_state(self, state: CircuitBreakerState) -> None:
        """
        Set circuit breaker state.

        Args:
            state: Current circuit breaker state
        """
        self.circuit_breaker_state.set(state.value)
        self.logger.debug(f"Circuit breaker state: {state.name}")

    def record_cache_operation(self, operation: str, result: str) -> None:
        """
        Record a cache operation.

        Args:
            operation: Operation type (get, set, invalidate)
            result: Operation result (hit, miss, error, success)
        """
        self.cache_operations_total.labels(operation=operation, result=result).inc()

        # Update cache hit rate
        if operation == "get":
            self._cache_requests += 1
            if result == "hit":
                self._cache_hits += 1

            if self._cache_requests > 0:
                hit_rate = self._cache_hits / self._cache_requests
                self.cache_hit_rate.set(hit_rate)

    def set_queue_depth(self, depth: int) -> None:
        """
        Set current queue depth.

        Args:
            depth: Number of pending requests
        """
        self.verification_queue_depth.set(depth)

    def set_system_info(self, info: dict) -> None:
        """
        Set system information.

        Args:
            info: System information dictionary
        """
        self.system_info.info(info)

    def get_metrics_summary(self) -> dict:
        """
        Get summary of current metrics.

        Returns:
            Dictionary with metric values
        """
        return {
            "total_requests": self._total_requests,
            "successful_requests": self._successful_requests,
            "success_rate": (
                self._successful_requests / self._total_requests
                if self._total_requests > 0
                else 0.0
            ),
            "cache_requests": self._cache_requests,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": (
                self._cache_hits / self._cache_requests if self._cache_requests > 0 else 0.0
            ),
        }


# Global metrics instance (singleton pattern)
_metrics_instance: Optional[VerificationMetrics] = None


def get_metrics(
    namespace: str = "hupyy", logger: Optional[logging.Logger] = None
) -> VerificationMetrics:
    """
    Get or create global metrics instance.

    Args:
        namespace: Prometheus namespace
        logger: Optional logger instance

    Returns:
        Global VerificationMetrics instance
    """
    global _metrics_instance

    if _metrics_instance is None:
        _metrics_instance = VerificationMetrics(namespace, logger)

    return _metrics_instance
