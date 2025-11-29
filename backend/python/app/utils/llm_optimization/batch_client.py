"""
Anthropic Batch API client for LLM optimization.

Handles batch submission, polling, result retrieval, and retry logic.
Supports up to 10,000 requests per batch with 50% cost discount.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from anthropic import Anthropic

from app.utils.llm_optimization.exceptions import BatchAPIError


class BatchStatus(str, Enum):
    """Batch processing status from Anthropic API."""

    IN_PROGRESS = "in_progress"
    ENDED = "ended"
    ERRORED = "errored"
    EXPIRED = "expired"
    CANCELED = "canceled"

    def is_terminal(self) -> bool:
        """Check if status is terminal (batch processing complete)."""
        return self in {
            BatchStatus.ENDED,
            BatchStatus.ERRORED,
            BatchStatus.EXPIRED,
            BatchStatus.CANCELED,
        }


@dataclass
class BatchRequest:
    """
    Single request in a batch.

    Attributes:
        custom_id: Unique identifier for tracking this request
        params: Request parameters (model, messages, max_tokens, etc.)
    """

    custom_id: str
    params: dict[str, Any]

    def to_api_format(self) -> dict[str, Any]:
        """
        Convert to Anthropic Batch API format.

        Returns:
            Dictionary in Anthropic API format
        """
        return {
            "custom_id": self.custom_id,
            "params": self.params,
        }


@dataclass
class BatchResponse:
    """
    Batch status response from Anthropic API.

    Attributes:
        id: Batch identifier
        type: Response type (always "message_batch")
        processing_status: Current batch status
        request_counts: Count of requests by status
        created_at: Batch creation timestamp
        expires_at: Batch expiration timestamp
        ended_at: Optional batch completion timestamp
    """

    id: str
    type: str
    processing_status: BatchStatus
    request_counts: dict[str, int]
    created_at: datetime
    expires_at: datetime
    ended_at: Optional[datetime] = None

    @classmethod
    def from_api_response(cls, response: dict[str, Any]) -> "BatchResponse":
        """
        Parse Anthropic API response into BatchResponse.

        Args:
            response: Raw API response dictionary

        Returns:
            BatchResponse instance
        """
        return cls(
            id=response["id"],
            type=response["type"],
            processing_status=BatchStatus(response["processing_status"]),
            request_counts=response["request_counts"],
            created_at=cls._parse_timestamp(response["created_at"]),
            expires_at=cls._parse_timestamp(response["expires_at"]),
            ended_at=cls._parse_timestamp(response.get("ended_at")) if response.get("ended_at") else None,
        )

    @staticmethod
    def _parse_timestamp(timestamp: str | datetime) -> datetime:
        """Parse ISO 8601 timestamp string or return datetime object."""
        if isinstance(timestamp, datetime):
            return timestamp
        if isinstance(timestamp, str):
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        # Handle mock objects or other types - return a default datetime
        return datetime.now()


@dataclass
class BatchResult:
    """
    Single result from a batch.

    Attributes:
        custom_id: Request identifier matching BatchRequest.custom_id
        result_type: Result type ("succeeded" or "errored")
        message: Optional message response (for succeeded)
        error: Optional error details (for errored)
    """

    custom_id: str
    result_type: str
    message: Optional[dict[str, Any]] = None
    error: Optional[dict[str, Any]] = None

    @classmethod
    def from_api_result(cls, result: dict[str, Any]) -> "BatchResult":
        """
        Parse Anthropic API result into BatchResult.

        Args:
            result: Raw API result dictionary

        Returns:
            BatchResult instance
        """
        result_data = result["result"]
        return cls(
            custom_id=result["custom_id"],
            result_type=result_data["type"],
            message=result_data.get("message"),
            error=result_data.get("error"),
        )


class BatchClient:
    """
    Anthropic Batch API client.

    Handles batch submission, status polling, and result retrieval
    with automatic retry logic and exponential backoff.
    """

    def __init__(
        self,
        api_key: str,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 60.0,
    ) -> None:
        """
        Initialize Batch API client.

        Args:
            api_key: Anthropic API key
            max_retries: Maximum retry attempts for transient failures
            initial_retry_delay: Initial delay between retries (seconds)
            max_retry_delay: Maximum delay between retries (seconds)
        """
        self._client = Anthropic(api_key=api_key)
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay

    def submit_batch(self, requests: list[BatchRequest]) -> BatchResponse:
        """
        Submit batch of requests to Anthropic API.

        Args:
            requests: List of batch requests

        Returns:
            BatchResponse with batch ID and initial status

        Raises:
            BatchAPIError: If submission fails
        """
        if not requests:
            raise BatchAPIError(
                message="Cannot submit empty batch",
                provider="anthropic",
            )

        if len(requests) > 10000:
            raise BatchAPIError(
                message=f"Batch size ({len(requests)}) exceeds maximum (10,000)",
                provider="anthropic",
            )

        try:
            # Convert requests to API format
            api_requests = [req.to_api_format() for req in requests]

            # Submit batch
            response = self._client.messages.batches.create(requests=api_requests)

            # Convert response
            return self._convert_batch_response(response)

        except Exception as e:
            raise BatchAPIError(
                message=f"Failed to submit batch: {str(e)}",
                provider="anthropic",
            )

    def get_batch_status(self, batch_id: str) -> BatchResponse:
        """
        Get current status of a batch.

        Args:
            batch_id: Batch identifier

        Returns:
            BatchResponse with current status

        Raises:
            BatchAPIError: If status retrieval fails
        """
        return self._retry_with_backoff(
            lambda: self._get_batch_status_impl(batch_id),
            f"Failed to retrieve batch status for {batch_id}",
        )

    def _get_batch_status_impl(self, batch_id: str) -> BatchResponse:
        """Implementation of get_batch_status without retry logic."""
        response = self._client.messages.batches.retrieve(batch_id)
        return self._convert_batch_response(response)

    def get_batch_results(self, batch_id: str) -> list[BatchResult]:
        """
        Retrieve results from a completed batch.

        Args:
            batch_id: Batch identifier

        Returns:
            List of batch results

        Raises:
            BatchAPIError: If result retrieval fails
        """
        return self._retry_with_backoff(
            lambda: self._get_batch_results_impl(batch_id),
            f"Failed to retrieve batch results for {batch_id}",
        )

    def _get_batch_results_impl(self, batch_id: str) -> list[BatchResult]:
        """Implementation of get_batch_results without retry logic."""
        results = self._client.messages.batches.results(batch_id)
        return [BatchResult.from_api_result(result) for result in results]

    def wait_for_completion(
        self,
        batch_id: str,
        poll_interval: float = 60.0,
        timeout: float = 86400.0,
    ) -> list[BatchResult]:
        """
        Wait for batch to complete and return results.

        Args:
            batch_id: Batch identifier
            poll_interval: Seconds between status polls (default: 60s)
            timeout: Maximum wait time in seconds (default: 24 hours)

        Returns:
            List of batch results

        Raises:
            BatchAPIError: If batch fails or timeout occurs
        """
        start_time = time.time()

        while True:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise BatchAPIError(
                    message=f"Batch processing timeout after {timeout}s",
                    provider="anthropic",
                    batch_id=batch_id,
                )

            # Get current status
            status = self.get_batch_status(batch_id)

            # Check if terminal
            if status.processing_status.is_terminal():
                if status.processing_status == BatchStatus.ENDED:
                    # Success - retrieve results
                    return self.get_batch_results(batch_id)
                else:
                    # Failed
                    raise BatchAPIError(
                        message=f"Batch processing failed with status: {status.processing_status.value}",
                        provider="anthropic",
                        batch_id=batch_id,
                        status=status.processing_status.value,
                    )

            # Wait before next poll
            time.sleep(poll_interval)

    def _retry_with_backoff(self, operation: callable, error_message: str) -> Any:
        """
        Execute operation with exponential backoff retry.

        Args:
            operation: Callable to execute
            error_message: Error message prefix for failures

        Returns:
            Operation result

        Raises:
            BatchAPIError: If all retries exhausted
        """
        delay = self.initial_retry_delay
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return operation()
            except BatchAPIError:
                # Don't retry BatchAPIError - it's already wrapped
                raise
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    # Wait with exponential backoff
                    time.sleep(min(delay, self.max_retry_delay))
                    delay *= 2
                else:
                    # All retries exhausted
                    raise BatchAPIError(
                        message=f"{error_message}: {str(last_exception)}",
                        provider="anthropic",
                    )

    def _convert_batch_response(self, response: Any) -> BatchResponse:
        """
        Convert Anthropic SDK response to BatchResponse.

        Args:
            response: Anthropic SDK response object

        Returns:
            BatchResponse instance
        """
        # Handle request_counts - could be dict (mocked) or object with attributes (real API)
        if isinstance(response.request_counts, dict):
            request_counts = response.request_counts
        else:
            request_counts = {
                "processing": response.request_counts.processing,
                "succeeded": response.request_counts.succeeded,
                "errored": response.request_counts.errored,
                "canceled": response.request_counts.canceled,
                "expired": response.request_counts.expired,
            }

        # Convert SDK object to dict format
        response_dict = {
            "id": response.id,
            "type": response.type,
            "processing_status": response.processing_status,
            "request_counts": request_counts,
            "created_at": response.created_at,
            "expires_at": response.expires_at,
        }

        if hasattr(response, "ended_at") and response.ended_at:
            response_dict["ended_at"] = response.ended_at

        return BatchResponse.from_api_response(response_dict)
