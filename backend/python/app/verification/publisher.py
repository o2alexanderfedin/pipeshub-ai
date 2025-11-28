"""
Verification publisher service for publishing verification requests to Kafka.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError


class VerificationPublisher:
    """
    Publisher for verification requests.

    Publishes chunks to the verify_chunks topic for asynchronous verification.
    """

    def __init__(
        self,
        kafka_brokers: str,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Initialize verification publisher.

        Args:
            kafka_brokers: Kafka broker list (e.g., "localhost:9092")
            logger: Optional logger instance
        """
        self.kafka_brokers = kafka_brokers
        self.logger = logger or logging.getLogger(__name__)
        self.producer: Optional[AIOKafkaProducer] = None
        self._started = False

    async def start(self) -> None:
        """Initialize and start the Kafka producer."""
        if self._started:
            return

        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.kafka_brokers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self.producer.start()
            self._started = True
            self.logger.info(f"✅ Verification publisher started (brokers: {self.kafka_brokers})")
        except Exception as e:
            self.logger.error(f"❌ Failed to start verification publisher: {str(e)}")
            raise

    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self.producer:
            await self.producer.stop()
            self.producer = None
            self._started = False
            self.logger.info("✅ Verification publisher stopped")

    async def publish_verification_request(
        self,
        chunks: List[Dict[str, Any]],
        query: str,
        user_id: str,
        org_id: str,
        session_id: Optional[str] = None,
    ) -> bool:
        """
        Publish a verification request to the verify_chunks topic.

        Args:
            chunks: List of chunks with content and metadata
            query: The original user query
            user_id: User identifier
            org_id: Organization identifier
            session_id: Optional session identifier for tracking

        Returns:
            True if published successfully, False otherwise
        """
        if not self._started:
            await self.start()

        if not self.producer:
            self.logger.error("Producer not initialized")
            return False

        try:
            # Prepare verification request payload
            request = {
                "chunks": chunks,
                "query": query,
                "user_id": user_id,
                "org_id": org_id,
                "session_id": session_id,
            }

            # Publish to verify_chunks topic
            await self.producer.send_and_wait(
                "verify_chunks",
                value=request,
            )

            self.logger.info(
                f"✅ Published verification request: {len(chunks)} chunks, "
                f"session={session_id}, org={org_id}"
            )
            return True

        except KafkaError as e:
            self.logger.error(f"❌ Kafka error publishing verification request: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Failed to publish verification request: {str(e)}")
            return False

    async def publish_batch_verification_requests(
        self,
        requests: List[Dict[str, Any]],
    ) -> int:
        """
        Publish multiple verification requests in a batch.

        Args:
            requests: List of verification request payloads

        Returns:
            Number of successfully published requests
        """
        if not self._started:
            await self.start()

        if not self.producer:
            self.logger.error("Producer not initialized")
            return 0

        success_count = 0
        for request in requests:
            try:
                await self.producer.send_and_wait(
                    "verify_chunks",
                    value=request,
                )
                success_count += 1
            except Exception as e:
                self.logger.error(f"❌ Failed to publish batch request: {str(e)}")

        self.logger.info(f"✅ Published {success_count}/{len(requests)} verification requests")
        return success_count
