"""
Circuit breaker pattern implementation for Hupyy client.

Prevents cascading failures when Hupyy API is down or slow.
States: CLOSED (normal) -> OPEN (blocking) -> HALF_OPEN (testing)
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, TypeVar, Generic

from app.infrastructure.metrics import CircuitBreakerState


T = TypeVar("T")


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Failures before opening circuit
    recovery_timeout_seconds: float = 60.0  # Time before trying recovery
    success_threshold: int = 2  # Successes needed to close from half-open
    timeout_seconds: float = 150.0  # Request timeout


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    pass


class CircuitBreaker(Generic[T]):
    """
    Circuit breaker implementation.

    Tracks failures and prevents requests when failure threshold exceeded.
    Automatically attempts recovery after timeout period.
    """

    def __init__(
        self,
        config: Optional[CircuitBreakerConfig] = None,
        logger: Optional[logging.Logger] = None,
        fallback_value: Optional[T] = None,
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration
            logger: Optional logger instance
            fallback_value: Optional fallback value when circuit is open
        """
        self.config = config or CircuitBreakerConfig()
        self.logger = logger or logging.getLogger(__name__)
        self.fallback_value = fallback_value

        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._state_lock = asyncio.Lock()

    @property
    def state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count

    @property
    def success_count(self) -> int:
        """Get current success count."""
        return self._success_count

    async def call(self, func: Callable[[], T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If function raises exception
        """
        async with self._state_lock:
            # Check if we should attempt recovery
            if self._state == CircuitBreakerState.OPEN:
                if self._should_attempt_recovery():
                    self._transition_to_half_open()
                else:
                    self.logger.warning("Circuit breaker is OPEN - request blocked")
                    raise CircuitBreakerError("Circuit breaker is OPEN")

        # Execute the function
        try:
            # Add timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs), timeout=self.config.timeout_seconds
            )

            # Record success
            await self._on_success()
            return result

        except asyncio.TimeoutError as e:
            self.logger.error(f"Request timeout after {self.config.timeout_seconds}s")
            await self._on_failure()
            raise

        except Exception as e:
            self.logger.error(f"Request failed: {str(e)}")
            await self._on_failure()
            raise

    async def _on_success(self) -> None:
        """Handle successful request."""
        async with self._state_lock:
            if self._state == CircuitBreakerState.HALF_OPEN:
                self._success_count += 1
                self.logger.info(
                    f"Circuit breaker HALF_OPEN: success {self._success_count}/"
                    f"{self.config.success_threshold}"
                )

                if self._success_count >= self.config.success_threshold:
                    self._transition_to_closed()

            elif self._state == CircuitBreakerState.CLOSED:
                # Reset failure count on success
                if self._failure_count > 0:
                    self.logger.debug("Resetting failure count after success")
                    self._failure_count = 0

    async def _on_failure(self) -> None:
        """Handle failed request."""
        async with self._state_lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitBreakerState.HALF_OPEN:
                # Any failure in half-open immediately opens circuit
                self.logger.warning("Circuit breaker: failure in HALF_OPEN, reopening")
                self._transition_to_open()

            elif self._state == CircuitBreakerState.CLOSED:
                self.logger.warning(
                    f"Circuit breaker: failure {self._failure_count}/"
                    f"{self.config.failure_threshold}"
                )

                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to_open()

    def _should_attempt_recovery(self) -> bool:
        """
        Check if enough time has passed to attempt recovery.

        Returns:
            True if should attempt recovery, False otherwise
        """
        if self._last_failure_time is None:
            return False

        time_since_failure = time.time() - self._last_failure_time
        return time_since_failure >= self.config.recovery_timeout_seconds

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self.logger.info("✅ Circuit breaker: CLOSED (normal operation)")

    def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        self._state = CircuitBreakerState.OPEN
        self._success_count = 0
        self.logger.error(
            f"❌ Circuit breaker: OPEN (blocking requests for "
            f"{self.config.recovery_timeout_seconds}s)"
        )

    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        self._state = CircuitBreakerState.HALF_OPEN
        self._failure_count = 0
        self._success_count = 0
        self.logger.info("⚠️  Circuit breaker: HALF_OPEN (testing recovery)")

    async def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        async with self._state_lock:
            self._transition_to_closed()
            self.logger.info("Circuit breaker manually reset")

    def get_state_info(self) -> dict:
        """
        Get current circuit breaker state information.

        Returns:
            Dictionary with state info
        """
        return {
            "state": self._state.name,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "failure_threshold": self.config.failure_threshold,
            "success_threshold": self.config.success_threshold,
            "recovery_timeout_seconds": self.config.recovery_timeout_seconds,
        }
