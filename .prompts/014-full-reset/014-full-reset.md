# Full System Reset and Fresh Deployment

## Objective
Complete system reset: clean all databases, clean all queues, reinstall all services from scratch, start Local Filesystem connector sync, and monitor to ensure continuous indexing works properly for the demo.

## Context
- **Demo Time**: 10AM PST (approximately 7-8 hours from now)
- **Previous Issue**: Kafka queue contaminated with 91,000+ invalid messages from previous test runs
- **Solution**: Complete fresh start to ensure clean, working state
- **Target**: Get as many files indexed as possible by demo time (expecting a few hundred files)
- **Strategy**: Start fresh, let it run continuously, files will become available as they're indexed

## Requirements

### 1. Complete Database Cleanup
- **ArangoDB**: Drop all collections and recreate schema
- **PostgreSQL**: Drop all tables and recreate schema
- **Qdrant**: Clear all vectors and collections
- Verify all databases are empty and schemas are correct

### 2. Complete Queue Cleanup
- **Kafka**: Delete and recreate all topics
- Reset all consumer group offsets
- Verify no messages in any topics

### 3. Complete Service Reinstallation
- Stop all Docker containers
- Remove all containers, volumes, and networks
- Rebuild all Docker images from scratch
- Start all services in correct order
- Verify all services are healthy and connected

### 4. Local Filesystem Connector Setup
- Configure Local Filesystem connector in UI
- Point to correct data directory with files
- Start sync operation
- Verify records are being created in database

### 5. Continuous Monitoring
- Monitor indexing pipeline continuously
- Track records: NOT_STARTED → COMPLETED
- Monitor Kafka consumer lag (should stay at 0)
- Monitor error logs for any failures
- Report progress every 10-15 minutes

## Success Criteria
- All databases clean and schemas correct
- All queues empty and topics recreated
- All services healthy and running
- Connector sync started successfully
- Records flowing through pipeline: Created → Indexed → Searchable
- Kafka consumer processing without errors
- Zero consumer lag maintained
- Files steadily accumulating as COMPLETED status
- Q&A system returning results from indexed files

## Time Estimate
- Database cleanup: 5 minutes
- Queue cleanup: 3 minutes
- Service reinstallation: 10-15 minutes (includes build time)
- Connector setup: 5 minutes
- Verification: 5 minutes
- **Total Setup**: 30-40 minutes
- **Continuous Indexing**: Remaining 6-7 hours until demo

## Expected Outcome
By demo time (10AM PST):
- Clean system with no contaminated data
- 200-400 files indexed (estimate based on indexing rate)
- Q&A system functional with indexed content
- Stable pipeline with zero errors
- Demo-ready state

## Execution Notes
- **No time limits on indexing**: Let it run continuously
- **Progressive availability**: Files become searchable as they're indexed
- **Focus on stability**: Ensure pipeline runs error-free
- **Monitor but don't interrupt**: Check progress periodically but let it work

## Commands Reference

### Database Cleanup Commands
```bash
# ArangoDB - drop database and recreate
curl -u "root:PASSWORD" -X DELETE http://localhost:8529/_db/es
curl -u "root:PASSWORD" -X POST http://localhost:8529/_db/_system/_api/database -d '{"name":"es"}'

# PostgreSQL - drop and recreate database
docker exec postgres-1 psql -U postgres -c "DROP DATABASE IF EXISTS pipeshub;"
docker exec postgres-1 psql -U postgres -c "CREATE DATABASE pipeshub;"

# Qdrant - clear all collections
curl -X DELETE http://localhost:6333/collections/pipeshub_records
```

### Kafka Cleanup Commands
```bash
# Stop consumers first
docker compose -f docker-compose.dev.yml stop pipeshub-ai

# Delete topics
docker exec kafka-1 kafka-topics --bootstrap-server localhost:9092 --delete --topic record-events
docker exec kafka-1 kafka-topics --bootstrap-server localhost:9092 --delete --topic connector-events

# Recreate topics
docker exec kafka-1 kafka-topics --bootstrap-server localhost:9092 --create --topic record-events --partitions 1 --replication-factor 1
docker exec kafka-1 kafka-topics --bootstrap-server localhost:9092 --create --topic connector-events --partitions 1 --replication-factor 1
```

### Service Reinstallation Commands
```bash
cd /Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/deployment/docker-compose

# Stop everything
docker compose -f docker-compose.dev.yml down

# Remove volumes (optional but recommended for complete cleanup)
docker compose -f docker-compose.dev.yml down -v

# Rebuild images
docker compose -f docker-compose.dev.yml build

# Start services
docker compose -f docker-compose.dev.yml up -d

# Check health
docker compose -f docker-compose.dev.yml ps
docker compose -f docker-compose.dev.yml logs --tail=50
```

### Monitoring Commands
```bash
# Check indexing status distribution
curl -s -u "root:PASSWORD" "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d '{"query":"FOR doc IN records COLLECT status = doc.indexingStatus WITH COUNT INTO count RETURN {status: status, count: count}"}' \
  | jq '.result'

# Check Kafka consumer lag
docker exec kafka-1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group records_consumer_group \
  --describe

# Check service logs
docker compose -f docker-compose.dev.yml logs pipeshub-ai --tail=50 --follow

# Check Qdrant vector count
curl http://localhost:6333/collections/pipeshub_records
```

## Task Breakdown

### Phase 1: Cleanup (8 minutes)
1. Stop all services
2. Clean ArangoDB
3. Clean PostgreSQL
4. Clean Qdrant
5. Clean Kafka topics
6. Verify all empty

### Phase 2: Reinstallation (15 minutes)
1. Remove all containers and volumes
2. Rebuild Docker images
3. Start services in order
4. Wait for health checks
5. Verify service connectivity

### Phase 3: Database Migration (5 minutes)
1. Run ArangoDB migrations
2. Run PostgreSQL migrations
3. Verify schemas are correct
4. Create initial data if needed

### Phase 4: Connector Setup (5 minutes)
1. Access UI and create account
2. Configure Local Filesystem connector
3. Set data directory path
4. Save configuration
5. Start sync

### Phase 5: Verification (5 minutes)
1. Check records being created
2. Check Kafka messages flowing
3. Check indexing service processing
4. Check vectors being created
5. Test Q&A with first indexed files

### Phase 6: Continuous Monitoring (Until demo)
1. Check progress every 15 minutes
2. Monitor for errors
3. Track indexing count growth
4. Ensure consumer lag stays at 0
5. Verify Q&A quality improves as more files indexed

## Output Requirements

### SUMMARY.md Must Include:
1. **One-liner**: Executive summary of full reset and deployment
2. **Execution Timeline**:
   - Start time
   - Each phase completion time
   - Current status
3. **Current Stats**:
   - Total records created
   - Total records indexed (COMPLETED)
   - Current indexing rate (records/minute)
   - Kafka consumer lag
   - Vector count in Qdrant
4. **Issues Encountered**: Any errors or problems and how resolved
5. **Demo Readiness**:
   - Estimated records by demo time
   - Q&A functionality status
   - System stability assessment
   - Risk factors if any
6. **Next Steps**: Any remaining tasks or monitoring needed

### Progress Updates Format:
```
[HH:MM] Phase X: Task Name
Status: IN_PROGRESS / COMPLETED / FAILED
Duration: X minutes
Details: What was done
Stats: Current numbers
```

## Principles to Follow

### TRIZ - Ideal Final Result
- **Ideal**: System maintains itself with zero manual intervention
- **Approach**: Set up once, let it run continuously
- **Measure**: Zero errors, steady progress, no manual fixes needed

### KISS - Keep It Simple
- Use existing infrastructure
- Follow documented procedures
- Don't add complexity
- Focus on core functionality

### Fail Fast
- If any phase fails, stop and diagnose
- Don't proceed with broken foundation
- Report blockers immediately
- Fix root cause before continuing

### Evidence-Based
- Verify each phase with concrete checks
- Use actual numbers, not assumptions
- Screenshot or log evidence for critical steps
- Track metrics over time

## Risk Mitigation

### If Database Cleanup Fails
- Check for locked connections
- Stop all services first
- Use force drop if needed
- Verify permissions

### If Service Won't Start
- Check Docker resources (memory, CPU)
- Review logs for specific error
- Verify port availability
- Check environment variables

### If Migration Fails
- Check database connectivity
- Verify migration scripts exist
- Run migrations manually if needed
- Recreate schema from scratch if corrupted

### If Connector Fails to Sync
- Verify file permissions
- Check data directory exists and is accessible
- Review connector logs
- Test with smaller directory first

### If Indexing Stalls
- Check Kafka consumer health
- Verify indexing service logs
- Check Qdrant connectivity
- Restart indexing service if needed

## Important Notes

1. **Time Pressure**: We have ~7 hours until demo, but setup takes ~40 minutes, leaving 6+ hours for indexing
2. **Progressive Demo**: Files become available gradually - this is acceptable and actually demonstrates real-time processing
3. **Quality over Quantity**: Better to have 200 perfectly indexed files than 1,000 broken ones
4. **Monitoring is Key**: Continuous monitoring ensures we catch issues early
5. **Don't Panic**: If something breaks, we have time to fix it and restart

## Execution Strategy

### Parallel Tasks (Where Possible)
- Database cleanups can run in parallel
- Service health checks can run concurrently
- Monitoring multiple metrics simultaneously

### Sequential Tasks (Must Be In Order)
- Stop services before cleanup
- Clean databases before reinstalling
- Start services before configuring connector
- Verify health before starting sync

### Critical Path
1. Cleanup → 2. Reinstall → 3. Migrate → 4. Configure → 5. Sync → 6. Monitor

Total critical path: ~40 minutes
Remaining time for indexing: ~6-7 hours

## Expected Indexing Rate

Based on previous observations:
- Record creation: Fast (seconds for 1,690 files)
- Kafka publishing: Fast (milliseconds per message)
- Indexing processing: ~2-5 seconds per file
- Expected rate: 12-30 files/minute
- In 6 hours: 4,320-10,800 files

**Conservative estimate: 200-400 files indexed by demo time**

## Demo Preparation

While indexing runs in background:
1. Prepare demo script showing Q&A functionality
2. Test queries on indexed content
3. Prepare example questions that showcase system
4. Have backup demo plan if indexing slower than expected
5. Monitor system stability leading up to demo

## Begin Execution

**Your task**: Execute this full reset and deployment plan, providing:
1. Real-time progress updates
2. Clear status at each phase
3. Evidence of successful completion
4. Continuous monitoring reports
5. Final SUMMARY.md with complete status

**Start now and report progress every phase completion.**
