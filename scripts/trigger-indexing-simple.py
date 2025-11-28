#!/usr/bin/env python3
"""Simple script to trigger indexing for NOT_STARTED records."""

import asyncio
import json
import sys
from datetime import datetime

import aiohttp
from aiokafka import AIOKafkaProducer

# Configuration for inside Docker container
ARANGO_URL = "http://arango-1:8529"
ARANGO_DB = "es"
ARANGO_USER = "root"
ARANGO_PASSWORD = "czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm"

KAFKA_SERVERS = "kafka-1:9092"
KAFKA_TOPIC = "record-events"


async def main():
    print("=== Triggering Bulk Indexing ===\n")

    # Step 1: Query NOT_STARTED records
    print("Step 1: Querying NOT_STARTED records...")
    auth = aiohttp.BasicAuth(ARANGO_USER, ARANGO_PASSWORD)

    async with aiohttp.ClientSession(auth=auth) as session:
        url = f"{ARANGO_URL}/_db/{ARANGO_DB}/_api/cursor"
        query = {
            "query": """
                FOR doc IN records
                FILTER doc.indexingStatus == "NOT_STARTED"
                RETURN {
                    recordId: doc.recordId,
                    recordName: doc.recordName,
                    connectorId: doc.connectorId
                }
            """
        }

        async with session.post(url, json=query) as response:
            if response.status != 201:
                print(f"❌ Query failed: {await response.text()}")
                return 1

            data = await response.json()
            records = data.get("result", [])

    print(f"Found {len(records)} records\n")

    if not records:
        print("No records to process. Exiting.")
        return 0

    # Step 2: Publish Kafka events
    print("Step 2: Publishing Kafka events...")
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8')
    )

    try:
        await producer.start()
        print("Kafka producer started\n")

        success = 0
        for i, record in enumerate(records, 1):
            event = {
                "eventType": "newRecord",
                "recordId": record["recordId"],
                "connectorId": record["connectorId"],
                "timestamp": datetime.utcnow().isoformat()
            }

            try:
                await producer.send_and_wait(
                    KAFKA_TOPIC,
                    value=event,
                    key=record["recordId"]
                )
                success += 1

                if i % 100 == 0:
                    print(f"Progress: {i}/{len(records)} events published...")

            except Exception as e:
                print(f"Failed to publish event for {record['recordName']}: {e}")

        print(f"\n✅ Published {success}/{len(records)} events successfully")
        print(f"\nIndexing will complete over next 30-60 minutes.")
        print(f"Monitor progress with:")
        print(f"  docker exec postgres-1 psql -U postgres -d pipeshub -c \"SELECT indexing_status, COUNT(*) FROM records GROUP BY indexing_status;\"")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    finally:
        await producer.stop()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
