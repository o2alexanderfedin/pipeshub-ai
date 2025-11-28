"""
Kafka topic setup for Hupyy verification.

This module creates and manages Kafka topics for the verification workflow:
- verify_chunks: Queue of chunks to verify
- verification_complete: Successfully verified results
- verification_failed: Failed verifications
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError


@dataclass
class TopicConfig:
    """Configuration for a Kafka topic."""

    name: str
    num_partitions: int = 3
    replication_factor: int = 1
    retention_ms: int = 86400000  # 24 hours


class KafkaTopicManager:
    """Manages Kafka topics for verification workflow."""

    # Topic names
    VERIFY_CHUNKS = "verify_chunks"
    VERIFICATION_COMPLETE = "verification_complete"
    VERIFICATION_FAILED = "verification_failed"

    def __init__(
        self, bootstrap_servers: List[str], logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Initialize Kafka topic manager.

        Args:
            bootstrap_servers: List of Kafka broker addresses
            logger: Optional logger instance
        """
        self.bootstrap_servers = bootstrap_servers
        self.logger = logger or logging.getLogger(__name__)
        self._admin_client: Optional[AIOKafkaAdminClient] = None

    async def connect(self) -> bool:
        """
        Connect to Kafka admin client.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self._admin_client = AIOKafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
            await self._admin_client.start()
            self.logger.info("✅ Connected to Kafka admin client")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Kafka: {str(e)}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Kafka admin client."""
        if self._admin_client:
            await self._admin_client.close()
            self._admin_client = None
            self.logger.info("✅ Disconnected from Kafka admin client")

    async def create_verification_topics(self) -> bool:
        """
        Create all verification-related Kafka topics.

        Returns:
            True if all topics created successfully, False otherwise
        """
        topics = [
            TopicConfig(name=self.VERIFY_CHUNKS),
            TopicConfig(name=self.VERIFICATION_COMPLETE),
            TopicConfig(name=self.VERIFICATION_FAILED),
        ]

        return await self.create_topics(topics)

    async def create_topics(self, topics: List[TopicConfig]) -> bool:
        """
        Create multiple Kafka topics.

        Args:
            topics: List of topic configurations

        Returns:
            True if all topics created successfully, False otherwise
        """
        if not self._admin_client:
            self.logger.error("Admin client not connected")
            return False

        try:
            new_topics = [
                NewTopic(
                    name=topic.name,
                    num_partitions=topic.num_partitions,
                    replication_factor=topic.replication_factor,
                    topic_configs={"retention.ms": str(topic.retention_ms)},
                )
                for topic in topics
            ]

            await self._admin_client.create_topics(new_topics)
            self.logger.info(f"✅ Created {len(topics)} verification topics")
            return True

        except TopicAlreadyExistsError:
            self.logger.info("Topics already exist, skipping creation")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create topics: {str(e)}")
            return False

    async def delete_verification_topics(self) -> bool:
        """
        Delete all verification-related topics (for testing/cleanup).

        Returns:
            True if topics deleted successfully, False otherwise
        """
        if not self._admin_client:
            self.logger.error("Admin client not connected")
            return False

        try:
            topics = [self.VERIFY_CHUNKS, self.VERIFICATION_COMPLETE, self.VERIFICATION_FAILED]
            await self._admin_client.delete_topics(topics)
            self.logger.info("✅ Deleted verification topics")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete topics: {str(e)}")
            return False

    async def list_topics(self) -> List[str]:
        """
        List all Kafka topics.

        Returns:
            List of topic names
        """
        if not self._admin_client:
            self.logger.error("Admin client not connected")
            return []

        try:
            metadata = await self._admin_client.list_topics()
            return list(metadata)
        except Exception as e:
            self.logger.error(f"Failed to list topics: {str(e)}")
            return []


async def setup_verification_kafka_topics(
    bootstrap_servers: List[str], logger: Optional[logging.Logger] = None
) -> bool:
    """
    Convenience function to set up all verification Kafka topics.

    Args:
        bootstrap_servers: List of Kafka broker addresses
        logger: Optional logger instance

    Returns:
        True if setup successful, False otherwise
    """
    manager = KafkaTopicManager(bootstrap_servers, logger)

    try:
        connected = await manager.connect()
        if not connected:
            return False

        created = await manager.create_verification_topics()
        return created
    finally:
        await manager.disconnect()
