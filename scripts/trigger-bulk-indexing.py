#!/usr/bin/env python3
"""
Trigger bulk indexing for NOT_STARTED records by publishing Kafka events.

This script queries ArangoDB for records with indexingStatus: NOT_STARTED
and publishes Kafka newRecord events to trigger the indexing pipeline.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

import aiohttp
from aiokafka import AIOKafkaProducer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
ARANGO_URL = "http://localhost:8529"
ARANGO_DB = "es"
ARANGO_USER = "root"
ARANGO_PASSWORD = "czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm"

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "record-events"

BATCH_SIZE = 100  # Process in batches to avoid overwhelming the system


async def get_not_started_records() -> List[Dict[str, Any]]:
    """Query ArangoDB for all NOT_STARTED records."""

    query = """
    FOR doc IN records
    FILTER doc.indexingStatus == "NOT_STARTED"
    RETURN {
        id: doc._key,
        recordId: doc.recordId,
        recordName: doc.recordName,
        connectorId: doc.connectorId,
        connectorName: doc.connectorName
    }
    """

    auth = aiohttp.BasicAuth(ARANGO_USER, ARANGO_PASSWORD)

    async with aiohttp.ClientSession(auth=auth) as session:
        url = f"{ARANGO_URL}/_db/{ARANGO_DB}/_api/cursor"
        payload = {"query": query}

        async with session.post(url, json=payload) as response:
            if response.status != 201:
                error_text = await response.text()
                raise Exception(f"ArangoDB query failed: {error_text}")

            data = await response.json()
            records = data.get("result", [])

            logger.info(f"Found {len(records)} NOT_STARTED records")
            return records


async def publish_kafka_event(producer: AIOKafkaProducer, record: Dict[str, Any]) -> bool:
    """Publish a newRecord event to Kafka."""

    event = {
        "eventType": "newRecord",
        "recordId": record["recordId"],
        "connectorId": record["connectorId"],
        "timestamp": datetime.utcnow().isoformat()
    }

    try:
        key = record["recordId"].encode('utf-8')
        value = json.dumps(event).encode('utf-8')

        await producer.send_and_wait(KAFKA_TOPIC, value=value, key=key)
        return True

    except Exception as e:
        logger.error(f"Failed to publish event for {record['recordName']}: {e}")
        return False


async def process_batch(producer: AIOKafkaProducer, records: List[Dict[str, Any]]) -> tuple[int, int]:
    """Process a batch of records, publishing Kafka events."""

    success_count = 0
    failure_count = 0

    for record in records:
        if await publish_kafka_event(producer, record):
            success_count += 1
            logger.info(f"Published event for: {record['recordName']} ({success_count}/{len(records)})")
        else:
            failure_count += 1

    return success_count, failure_count


async def main():
    """Main execution function."""

    logger.info("=== Bulk Indexing Trigger Script ===")
    logger.info(f"Target: {KAFKA_TOPIC} on {KAFKA_BOOTSTRAP_SERVERS}")

    # Step 1: Get all NOT_STARTED records
    logger.info("Step 1: Querying for NOT_STARTED records...")
    try:
        records = await get_not_started_records()
    except Exception as e:
        logger.error(f"Failed to query records: {e}")
        return 1

    if not records:
        logger.info("No NOT_STARTED records found. Exiting.")
        return 0

    logger.info(f"Found {len(records)} records to process")

    # Step 2: Initialize Kafka producer
    logger.info("Step 2: Initializing Kafka producer...")
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: v  # Already encoded to bytes
    )

    try:
        await producer.start()
        logger.info("Kafka producer started successfully")
    except Exception as e:
        logger.error(f"Failed to start Kafka producer: {e}")
        return 1

    try:
        # Step 3: Process records in batches
        logger.info(f"Step 3: Publishing events (batch size: {BATCH_SIZE})...")

        total_success = 0
        total_failure = 0

        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i:i + BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            total_batches = (len(records) + BATCH_SIZE - 1) // BATCH_SIZE

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} records)...")

            success, failure = await process_batch(producer, batch)
            total_success += success
            total_failure += failure

            logger.info(f"Batch {batch_num} complete: {success} success, {failure} failures")

            # Small delay between batches to avoid overwhelming the system
            if i + BATCH_SIZE < len(records):
                await asyncio.sleep(1)

        # Step 4: Summary
        logger.info("=== Execution Complete ===")
        logger.info(f"Total records processed: {len(records)}")
        logger.info(f"Events published: {total_success}")
        logger.info(f"Failures: {total_failure}")
        logger.info(f"Success rate: {(total_success/len(records)*100):.1f}%")

        if total_success > 0:
            logger.info("")
            logger.info("Next steps:")
            logger.info("1. Monitor indexing progress:")
            logger.info("   docker exec postgres-1 psql -U postgres -d pipeshub -c \"SELECT indexing_status, COUNT(*) FROM records GROUP BY indexing_status;\"")
            logger.info("")
            logger.info("2. Check Kafka consumer lag:")
            logger.info("   docker exec docker-compose-kafka-1-1 kafka-consumer-groups --bootstrap-server localhost:9092 --group records_consumer_group --describe")
            logger.info("")
            logger.info(f"Expected: {total_success} records will transition from NOT_STARTED to COMPLETED over next 30-60 minutes")

        return 0 if total_failure == 0 else 1

    finally:
        await producer.stop()
        logger.info("Kafka producer stopped")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
