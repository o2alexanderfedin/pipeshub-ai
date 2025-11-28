# Quick Start Guide - Demo Preparation

**Use this for rapid execution. See `demo-prep-plan.md` for full details.**

## Critical Blocker Fix (5 minutes)

```bash
# Stop indexing service
docker stop indexing-service-1

# Reset Kafka offset to latest
docker exec kafka-1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group records_consumer_group \
  --reset-offsets \
  --topic record-events \
  --to-latest \
  --execute

# Restart indexing service
docker start indexing-service-1

# Verify offset reset
docker exec kafka-1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group records_consumer_group \
  --describe
```

## Monitor Indexing Progress (30-60 minutes)

```bash
# Check progress every 5 minutes
docker exec postgres-1 psql -U postgres -d pipeshub -c "
  SELECT
    indexing_status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
  FROM records
  GROUP BY indexing_status
  ORDER BY indexing_status;
"

# Watch indexing service logs
docker logs -f --tail 100 indexing-service-1

# Check vector count
curl -s "http://localhost:6333/collections/records" | jq '.result.points_count'
```

## Health Check (run anytime)

```bash
docker ps --format "table {{.Names}}\t{{.Status}}" && \
echo "\n=== Database Records ===" && \
docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT indexing_status, COUNT(*) FROM records GROUP BY indexing_status;" && \
echo "\n=== Kafka Consumer ===" && \
docker exec kafka-1 kafka-consumer-groups --bootstrap-server localhost:9092 --group records_consumer_group --describe
```

## Demo-Ready Checklist

- [ ] Kafka consumer lag = 0
- [ ] 1,690 records with `indexing_status = 'INDEXED'`
- [ ] 5,000-10,000 chunks in database
- [ ] 5,000-10,000 vectors in Qdrant
- [ ] Q&A returns relevant results
- [ ] Response time < 5 seconds

## Next Steps

1. Run critical blocker fix (above)
2. Monitor indexing progress to 100%
3. Test Q&A with sample queries
4. Declare demo-ready

**Full details**: See `demo-prep-plan.md`
