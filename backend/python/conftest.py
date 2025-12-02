"""
Root conftest.py for PipesHub AI Python tests

This file contains shared fixtures and configuration for all Python tests.
Fixtures defined here are available to all test files.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from httpx import AsyncClient
from pytest_mock import MockerFixture

# Add app to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================================
# Session Configuration
# ============================================================================


def pytest_configure(config):
    """
    Pytest configuration hook.
    Called once before tests run.
    """
    # Set environment variables for testing
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"

    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    print("\n" + "=" * 80)
    print("PipesHub AI Test Suite")
    print("=" * 80)


def pytest_sessionstart(session):
    """
    Called after Session object has been created and before tests run.
    """
    print(f"\nTest session started: {datetime.now()}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before returning the exit status.
    """
    print(f"\nTest session finished: {datetime.now()}")
    print(f"Exit status: {exitstatus}")


# ============================================================================
# Event Loop Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the entire test session.
    Required for async tests.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP client for testing external APIs.
    """
    async with AsyncClient(timeout=30.0) as client:
        yield client


# ============================================================================
# Environment & Configuration Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def test_env() -> Dict[str, str]:
    """
    Provide test environment variables.
    """
    return {
        "TESTING": "true",
        "LOG_LEVEL": "DEBUG",
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        "REDIS_URL": "redis://localhost:6379/0",
        "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
    }


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """
    Provide a temporary directory for test files.
    Cleaned up automatically after test.
    """
    return tmp_path


@pytest.fixture
def test_data_dir() -> Path:
    """
    Provide path to test data directory.
    """
    return Path(__file__).parent / "tests" / "fixtures" / "data"


# ============================================================================
# Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_kafka_producer(mocker: MockerFixture) -> Mock:
    """
    Mock Kafka producer for testing.
    """
    producer = mocker.Mock()
    producer.send = mocker.AsyncMock(return_value=None)
    producer.flush = mocker.AsyncMock(return_value=None)
    producer.stop = mocker.AsyncMock(return_value=None)
    return producer


@pytest.fixture
def mock_kafka_consumer(mocker: MockerFixture) -> Mock:
    """
    Mock Kafka consumer for testing.
    """
    consumer = mocker.Mock()
    consumer.start = mocker.AsyncMock(return_value=None)
    consumer.stop = mocker.AsyncMock(return_value=None)
    consumer.subscribe = mocker.Mock(return_value=None)
    consumer.getmany = mocker.AsyncMock(return_value={})
    return consumer


@pytest.fixture
def mock_redis_client(mocker: MockerFixture) -> Mock:
    """
    Mock Redis client for testing.
    """
    redis = mocker.Mock()
    redis.get = mocker.AsyncMock(return_value=None)
    redis.set = mocker.AsyncMock(return_value=True)
    redis.delete = mocker.AsyncMock(return_value=1)
    redis.exists = mocker.AsyncMock(return_value=0)
    redis.close = mocker.AsyncMock(return_value=None)
    return redis


@pytest.fixture
def mock_arango_client(mocker: MockerFixture) -> Mock:
    """
    Mock ArangoDB client for testing.
    """
    arango = mocker.Mock()
    arango.db = mocker.Mock()
    arango.db.collection = mocker.Mock()
    arango.db.collection.insert = mocker.Mock(return_value={"_key": "test123"})
    arango.db.collection.get = mocker.Mock(return_value=None)
    arango.db.collection.update = mocker.Mock(return_value={"_key": "test123"})
    arango.db.collection.delete = mocker.Mock(return_value=True)
    return arango


@pytest.fixture
def mock_qdrant_client(mocker: MockerFixture) -> Mock:
    """
    Mock Qdrant vector database client for testing.
    """
    qdrant = mocker.Mock()
    qdrant.upsert = mocker.AsyncMock(return_value=None)
    qdrant.search = mocker.AsyncMock(return_value=[])
    qdrant.delete = mocker.AsyncMock(return_value=None)
    return qdrant


@pytest.fixture
def mock_anthropic_client(mocker: MockerFixture) -> Mock:
    """
    Mock Anthropic API client for testing.
    """
    client = mocker.Mock()

    # Mock the messages.create method
    mock_message = mocker.Mock()
    mock_message.content = [mocker.Mock(text="This is a test response")]
    mock_message.id = "msg_test123"
    mock_message.model = "claude-sonnet-4-5-20250929"
    mock_message.role = "assistant"
    mock_message.stop_reason = "end_turn"
    mock_message.usage = mocker.Mock(input_tokens=10, output_tokens=20)

    client.messages.create = mocker.Mock(return_value=mock_message)

    return client


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture
async def test_db_session():
    """
    Provide a test database session.
    Rolls back changes after test.

    NOTE: Implement this based on your actual database setup.
    This is a placeholder showing the pattern.
    """
    # TODO: Initialize test database session
    # session = await create_test_db_session()
    session = Mock()  # Placeholder

    try:
        yield session
    finally:
        # Rollback changes
        # await session.rollback()
        # await session.close()
        pass


# ============================================================================
# Verification/Hupyy Feature Fixtures
# ============================================================================


@pytest.fixture
def sample_verification_request() -> Dict[str, Any]:
    """
    Provide a sample verification request for testing.
    """
    return {
        "user_prompt": "What is the capital of France?",
        "ai_response": "The capital of France is Paris.",
        "sources": [
            {
                "document_id": "doc123",
                "chunk_id": "chunk456",
                "content": "Paris is the capital and largest city of France.",
                "score": 0.95,
            }
        ],
    }


@pytest.fixture
def sample_verification_response() -> Dict[str, Any]:
    """
    Provide a sample verification response for testing.
    """
    return {
        "is_verified": True,
        "confidence": 0.92,
        "explanation": "The response is accurate. Paris is indeed the capital of France.",
        "sources_used": ["doc123"],
        "corrections": [],
    }


@pytest.fixture
def sample_connector_config() -> Dict[str, Any]:
    """
    Provide sample connector configuration for testing.
    """
    return {
        "name": "TestConnector",
        "type": "google_drive",
        "auth_type": "OAUTH",
        "credentials": {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
        },
        "settings": {
            "sync_frequency": "daily",
            "batch_size": 100,
        },
    }


# ============================================================================
# HTTP Client Fixtures
# ============================================================================


@pytest.fixture
def mock_httpx_response(mocker: MockerFixture):
    """
    Factory fixture for creating mock HTTP responses.

    Usage:
        response = mock_httpx_response(
            status_code=200,
            json_data={"key": "value"}
        )
    """

    def _create_response(
        status_code: int = 200,
        json_data: Dict[str, Any] = None,
        text: str = None,
        headers: Dict[str, str] = None,
    ):
        response = mocker.Mock()
        response.status_code = status_code
        response.headers = headers or {}

        if json_data is not None:
            response.json = mocker.Mock(return_value=json_data)
            response.text = json.dumps(json_data)
        elif text is not None:
            response.text = text
            response.json = mocker.Mock(side_effect=ValueError("No JSON"))
        else:
            response.text = ""
            response.json = mocker.Mock(side_effect=ValueError("No JSON"))

        response.raise_for_status = mocker.Mock()
        return response

    return _create_response


# ============================================================================
# Time Fixtures
# ============================================================================


@pytest.fixture
def freeze_time(mocker: MockerFixture):
    """
    Fixture to freeze time for testing.

    Usage:
        freeze_time(datetime(2024, 1, 1, 12, 0, 0))
    """

    def _freeze(frozen_time: datetime):
        mocker.patch("datetime.datetime", wraps=datetime)
        mocker.patch.object(datetime, "now", return_value=frozen_time)
        mocker.patch.object(datetime, "utcnow", return_value=frozen_time)

    return _freeze


# ============================================================================
# File Fixtures
# ============================================================================


@pytest.fixture
def sample_pdf_file(tmp_path: Path) -> Path:
    """
    Create a sample PDF file for testing.
    """
    pdf_path = tmp_path / "test.pdf"
    # Create a minimal PDF (placeholder - use real PDF library if needed)
    pdf_path.write_bytes(b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\nendobj\n%%EOF")
    return pdf_path


@pytest.fixture
def sample_json_file(tmp_path: Path) -> Path:
    """
    Create a sample JSON file for testing.
    """
    json_path = tmp_path / "test.json"
    json_path.write_text(json.dumps({"test": "data", "number": 123}))
    return json_path


# ============================================================================
# Async Helpers
# ============================================================================


@pytest.fixture
def async_return():
    """
    Helper to create async return values for mocks.

    Usage:
        mock.method = async_return({"key": "value"})
    """

    def _async_return(value):
        async def _inner(*args, **kwargs):
            return value
        return _inner

    return _async_return


# ============================================================================
# VCR Configuration (for recording HTTP interactions)
# ============================================================================


@pytest.fixture(scope="module")
def vcr_config():
    """
    Configuration for VCR.py (HTTP interaction recording).
    """
    return {
        "filter_headers": [
            "authorization",
            "api-key",
            "x-api-key",
        ],
        "filter_query_parameters": [
            "api_key",
            "apikey",
        ],
        "record_mode": "once",  # once, new_episodes, none, all
        "match_on": ["uri", "method"],
        "cassette_library_dir": "tests/fixtures/vcr_cassettes",
    }


# ============================================================================
# Pytest Markers & Hooks
# ============================================================================


def pytest_collection_modifyitems(config, items):
    """
    Modify test items after collection.
    Add markers automatically based on test location or name.
    """
    for item in items:
        # Auto-mark verification tests
        if "verification" in str(item.fspath):
            item.add_marker(pytest.mark.verification)

        # Auto-mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Auto-mark unit tests
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Mark slow tests
        if "slow" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)

        # Mark tests requiring external APIs
        if any(keyword in item.nodeid.lower() for keyword in ["external", "api", "http"]):
            item.add_marker(pytest.mark.external_api)


# ============================================================================
# Cleanup
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """
    Auto-use fixture that runs after every test.
    Clean up resources, reset mocks, etc.
    """
    yield
    # Cleanup code here
    # e.g., clear caches, reset singletons, etc.


# ============================================================================
# Test Data Factories (using simple functions, can upgrade to factory_boy)
# ============================================================================


@pytest.fixture
def create_test_user():
    """
    Factory fixture for creating test users.
    """

    def _create(
        user_id: str = "test_user_123",
        email: str = "test@example.com",
        name: str = "Test User",
    ) -> Dict[str, Any]:
        return {
            "id": user_id,
            "email": email,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "is_active": True,
        }

    return _create


@pytest.fixture
def create_test_document():
    """
    Factory fixture for creating test documents.
    """

    def _create(
        doc_id: str = "doc_123",
        content: str = "Test document content",
        title: str = "Test Document",
    ) -> Dict[str, Any]:
        return {
            "id": doc_id,
            "title": title,
            "content": content,
            "created_at": datetime.now().isoformat(),
            "metadata": {
                "source": "test",
                "type": "text",
            },
        }

    return _create


# ============================================================================
# Example: Testcontainers fixtures (if using)
# ============================================================================


# @pytest.fixture(scope="session")
# def kafka_container():
#     """
#     Start a Kafka container for integration tests.
#     Requires testcontainers-python library.
#     """
#     from testcontainers.kafka import KafkaContainer
#
#     with KafkaContainer() as kafka:
#         yield kafka


print("✓ conftest.py loaded successfully")
