"""
Unit tests for Anthropic Batch API client.

Tests batch submission, polling, result retrieval, and retry logic.
Target: 90%+ coverage, all Anthropic API calls mocked.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Any
from datetime import datetime, timedelta

from app.utils.llm_optimization.batch_client import (
    BatchClient,
    BatchRequest,
    BatchResponse,
    BatchStatus,
    BatchResult,
)
from app.utils.llm_optimization.exceptions import BatchAPIError


class TestBatchRequest:
    """Test BatchRequest dataclass."""

    def test_create_valid_request(self) -> None:
        """Test creating a valid batch request."""
        request = BatchRequest(
            custom_id="test-001",
            params={
                "model": "claude-sonnet-4-5-20250929",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )

        assert request.custom_id == "test-001"
        assert request.params["model"] == "claude-sonnet-4-5-20250929"
        assert request.params["max_tokens"] == 1024
        assert len(request.params["messages"]) == 1

    def test_to_api_format(self) -> None:
        """Test conversion to Anthropic API format."""
        request = BatchRequest(
            custom_id="test-002",
            params={
                "model": "claude-sonnet-4-5-20250929",
                "max_tokens": 512,
                "messages": [{"role": "user", "content": "Test"}],
            },
        )

        api_format = request.to_api_format()

        assert api_format["custom_id"] == "test-002"
        assert api_format["params"]["model"] == "claude-sonnet-4-5-20250929"
        assert api_format["params"]["max_tokens"] == 512


class TestBatchStatus:
    """Test BatchStatus enum."""

    def test_batch_status_values(self) -> None:
        """Test batch status enum values."""
        assert BatchStatus.IN_PROGRESS.value == "in_progress"
        assert BatchStatus.ENDED.value == "ended"
        assert BatchStatus.ERRORED.value == "errored"
        assert BatchStatus.EXPIRED.value == "expired"
        assert BatchStatus.CANCELED.value == "canceled"

    def test_is_terminal(self) -> None:
        """Test terminal status detection."""
        assert BatchStatus.IN_PROGRESS.is_terminal() is False
        assert BatchStatus.ENDED.is_terminal() is True
        assert BatchStatus.ERRORED.is_terminal() is True
        assert BatchStatus.EXPIRED.is_terminal() is True
        assert BatchStatus.CANCELED.is_terminal() is True


class TestBatchResponse:
    """Test BatchResponse dataclass."""

    def test_create_valid_response(self) -> None:
        """Test creating a valid batch response."""
        response = BatchResponse(
            id="batch_123",
            type="message_batch",
            processing_status=BatchStatus.IN_PROGRESS,
            request_counts={
                "processing": 10,
                "succeeded": 0,
                "errored": 0,
                "canceled": 0,
                "expired": 0,
            },
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24),
        )

        assert response.id == "batch_123"
        assert response.processing_status == BatchStatus.IN_PROGRESS
        assert response.request_counts["processing"] == 10

    def test_from_api_response(self) -> None:
        """Test parsing from Anthropic API response."""
        api_response = {
            "id": "batch_456",
            "type": "message_batch",
            "processing_status": "ended",
            "request_counts": {
                "processing": 0,
                "succeeded": 5,
                "errored": 0,
                "canceled": 0,
                "expired": 0,
            },
            "created_at": "2025-11-28T10:00:00Z",
            "expires_at": "2025-11-29T10:00:00Z",
        }

        response = BatchResponse.from_api_response(api_response)

        assert response.id == "batch_456"
        assert response.processing_status == BatchStatus.ENDED
        assert response.request_counts["succeeded"] == 5


class TestBatchResult:
    """Test BatchResult dataclass."""

    def test_create_successful_result(self) -> None:
        """Test creating a successful batch result."""
        result = BatchResult(
            custom_id="test-001",
            result_type="succeeded",
            message={
                "id": "msg_123",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": "Hello!"}],
            },
        )

        assert result.custom_id == "test-001"
        assert result.result_type == "succeeded"
        assert result.message is not None
        assert result.error is None

    def test_create_error_result(self) -> None:
        """Test creating an error batch result."""
        result = BatchResult(
            custom_id="test-002",
            result_type="errored",
            error={
                "type": "invalid_request_error",
                "message": "Invalid parameter",
            },
        )

        assert result.custom_id == "test-002"
        assert result.result_type == "errored"
        assert result.message is None
        assert result.error is not None

    def test_from_api_result(self) -> None:
        """Test parsing from Anthropic API result."""
        api_result = {
            "custom_id": "test-003",
            "result": {
                "type": "succeeded",
                "message": {
                    "id": "msg_789",
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "text", "text": "Response"}],
                },
            },
        }

        result = BatchResult.from_api_result(api_result)

        assert result.custom_id == "test-003"
        assert result.result_type == "succeeded"
        assert result.message["id"] == "msg_789"


class TestBatchClient:
    """Test BatchClient class."""

    @pytest.fixture
    def mock_anthropic_client(self) -> Mock:
        """Create mock Anthropic client."""
        client = Mock()
        client.messages = Mock()
        client.messages.batches = Mock()
        return client

    @pytest.fixture
    def batch_client(self, mock_anthropic_client: Mock) -> BatchClient:
        """Create BatchClient with mocked Anthropic client."""
        with patch("app.utils.llm_optimization.batch_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_anthropic_client
            client = BatchClient(api_key="test-api-key")
            client._client = mock_anthropic_client
            return client

    def test_create_client(self) -> None:
        """Test creating BatchClient."""
        with patch("app.utils.llm_optimization.batch_client.Anthropic") as mock_anthropic:
            client = BatchClient(api_key="test-key")
            mock_anthropic.assert_called_once_with(api_key="test-key")

    def test_submit_batch_success(self, batch_client: BatchClient, mock_anthropic_client: Mock) -> None:
        """Test successful batch submission."""
        requests = [
            BatchRequest(
                custom_id="req-1",
                params={
                    "model": "claude-sonnet-4-5-20250929",
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": "Test 1"}],
                },
            ),
            BatchRequest(
                custom_id="req-2",
                params={
                    "model": "claude-sonnet-4-5-20250929",
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": "Test 2"}],
                },
            ),
        ]

        mock_anthropic_client.messages.batches.create.return_value = Mock(
            id="batch_abc123",
            type="message_batch",
            processing_status="in_progress",
            request_counts={"processing": 2, "succeeded": 0, "errored": 0, "canceled": 0, "expired": 0},
            created_at="2025-11-28T10:00:00Z",
            expires_at="2025-11-29T10:00:00Z",
        )

        response = batch_client.submit_batch(requests)

        assert response.id == "batch_abc123"
        assert response.processing_status == BatchStatus.IN_PROGRESS
        mock_anthropic_client.messages.batches.create.assert_called_once()

    def test_submit_batch_empty_requests(self, batch_client: BatchClient) -> None:
        """Test submitting empty batch raises error."""
        with pytest.raises(BatchAPIError, match="Cannot submit empty batch"):
            batch_client.submit_batch([])

    def test_submit_batch_exceeds_max_size(self, batch_client: BatchClient) -> None:
        """Test submitting batch exceeding max size raises error."""
        requests = [
            BatchRequest(
                custom_id=f"req-{i}",
                params={
                    "model": "claude-sonnet-4-5-20250929",
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": f"Test {i}"}],
                },
            )
            for i in range(10001)  # Exceeds 10,000 limit
        ]

        with pytest.raises(BatchAPIError, match="Batch size.*exceeds maximum"):
            batch_client.submit_batch(requests)

    def test_get_batch_status_success(self, batch_client: BatchClient, mock_anthropic_client: Mock) -> None:
        """Test getting batch status."""
        mock_anthropic_client.messages.batches.retrieve.return_value = Mock(
            id="batch_xyz",
            type="message_batch",
            processing_status="ended",
            request_counts={"processing": 0, "succeeded": 5, "errored": 0, "canceled": 0, "expired": 0},
            created_at="2025-11-28T10:00:00Z",
            expires_at="2025-11-29T10:00:00Z",
        )

        response = batch_client.get_batch_status("batch_xyz")

        assert response.id == "batch_xyz"
        assert response.processing_status == BatchStatus.ENDED
        assert response.request_counts["succeeded"] == 5
        mock_anthropic_client.messages.batches.retrieve.assert_called_once_with("batch_xyz")

    def test_get_batch_status_not_found(self, batch_client: BatchClient, mock_anthropic_client: Mock) -> None:
        """Test getting status for non-existent batch."""
        mock_anthropic_client.messages.batches.retrieve.side_effect = Exception("Batch not found")

        with pytest.raises(BatchAPIError, match="Failed to retrieve batch status"):
            batch_client.get_batch_status("invalid_batch")

    def test_get_batch_results_success(self, batch_client: BatchClient, mock_anthropic_client: Mock) -> None:
        """Test retrieving batch results."""
        mock_results = [
            {
                "custom_id": "req-1",
                "result": {
                    "type": "succeeded",
                    "message": {
                        "id": "msg_1",
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "text", "text": "Result 1"}],
                    },
                },
            },
            {
                "custom_id": "req-2",
                "result": {
                    "type": "succeeded",
                    "message": {
                        "id": "msg_2",
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "text", "text": "Result 2"}],
                    },
                },
            },
        ]

        mock_anthropic_client.messages.batches.results.return_value = mock_results

        results = batch_client.get_batch_results("batch_completed")

        assert len(results) == 2
        assert results[0].custom_id == "req-1"
        assert results[1].custom_id == "req-2"
        mock_anthropic_client.messages.batches.results.assert_called_once_with("batch_completed")

    def test_retry_on_transient_failure(self, batch_client: BatchClient, mock_anthropic_client: Mock) -> None:
        """Test retry logic on transient failures."""
        # First two calls fail, third succeeds
        mock_anthropic_client.messages.batches.retrieve.side_effect = [
            Exception("Temporary network error"),
            Exception("Service unavailable"),
            Mock(
                id="batch_retry",
                processing_status="ended",
                request_counts={"succeeded": 1, "errored": 0},
            ),
        ]

        batch_client.max_retries = 3
        response = batch_client.get_batch_status("batch_retry")

        assert response.id == "batch_retry"
        assert mock_anthropic_client.messages.batches.retrieve.call_count == 3

    def test_retry_exhausted(self, batch_client: BatchClient, mock_anthropic_client: Mock) -> None:
        """Test retry exhaustion raises error."""
        mock_anthropic_client.messages.batches.retrieve.side_effect = Exception("Persistent error")

        batch_client.max_retries = 2

        with pytest.raises(BatchAPIError, match="Failed to retrieve batch status"):
            batch_client.get_batch_status("batch_fail")

        assert mock_anthropic_client.messages.batches.retrieve.call_count == 3  # Initial + 2 retries

    def test_wait_for_completion_success(self, batch_client: BatchClient, mock_anthropic_client: Mock) -> None:
        """Test waiting for batch completion."""
        # Simulate batch progressing: in_progress -> in_progress -> ended
        mock_anthropic_client.messages.batches.retrieve.side_effect = [
            Mock(id="batch_wait", processing_status="in_progress", request_counts={"processing": 10}),
            Mock(id="batch_wait", processing_status="in_progress", request_counts={"processing": 5}),
            Mock(id="batch_wait", processing_status="ended", request_counts={"succeeded": 10, "errored": 0}),
        ]

        mock_anthropic_client.messages.batches.results.return_value = [
            {
                "custom_id": "req-1",
                "result": {
                    "type": "succeeded",
                    "message": {"id": "msg_1", "content": [{"type": "text", "text": "Done"}]},
                },
            }
        ]

        results = batch_client.wait_for_completion("batch_wait", poll_interval=0.1, timeout=10)

        assert len(results) == 1
        assert results[0].custom_id == "req-1"

    def test_wait_for_completion_timeout(self, batch_client: BatchClient, mock_anthropic_client: Mock) -> None:
        """Test timeout when waiting for batch completion."""
        # Always return in_progress
        mock_anthropic_client.messages.batches.retrieve.return_value = Mock(
            id="batch_timeout",
            processing_status="in_progress",
            request_counts={"processing": 10},
        )

        with pytest.raises(BatchAPIError, match="Batch processing timeout"):
            batch_client.wait_for_completion("batch_timeout", poll_interval=0.1, timeout=0.5)

    def test_wait_for_completion_errored(self, batch_client: BatchClient, mock_anthropic_client: Mock) -> None:
        """Test batch ending in errored status."""
        mock_anthropic_client.messages.batches.retrieve.return_value = Mock(
            id="batch_error",
            processing_status="errored",
            request_counts={"errored": 10},
        )

        with pytest.raises(BatchAPIError, match="Batch processing failed"):
            batch_client.wait_for_completion("batch_error", poll_interval=0.1, timeout=10)
