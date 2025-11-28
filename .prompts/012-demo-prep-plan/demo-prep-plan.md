# Demo Preparation Deployment Plan

**Created**: 2025-11-28
**Demo Target**: 10AM PST
**Time Available**: ~7-8 hours
**Estimated Execution**: 55-85 minutes
**Buffer for Testing**: 5+ hours

## Executive Summary

Based on comprehensive research findings, the critical blocker is **Kafka consumer lag of 44,952 messages** causing the indexing service to be stuck in an infinite retry loop. The fastest path to demo-ready state is:

1. **Keep existing infrastructure** (services healthy, database valid)
2. **Reset Kafka offset to latest** (skip old/invalid messages)
3. **Trigger indexing** for 1,690 valid records
4. **Monitor progress** to 100% completion

**Recommended Path**: Phases 0, 3, 6, 7, 8 (skip clean/redeploy)

---

## Critical Research Findings

### Blocker Identified
- **Consumer lag**: 44,952 messages
- **Consumer offset**: 46,458 (stuck)
- **Log-end offset**: 91,410
- **Database records**: 1,690 valid, all `indexingStatus: NOT_STARTED`
- **Indexed records**: 0

### Root Cause
Indexing service stuck processing old/invalid Kafka messages from previous test runs, attempting to index records that no longer exist in the database. This blocks ALL new indexing operations.

### Solution
Reset Kafka consumer offset to latest, allowing the consumer to skip old messages and process only new events.

---

## Phase 0: Pre-Deployment Preparation (5 minutes)

**Purpose**: Verify current state and prepare for deployment

### Tasks

1. **Review research findings**
   ```bash
   cat /Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/.prompts/011-debug-indexing-research/SUMMARY.md
   ```

2. **Check Docker services status**
   ```bash
   docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
   ```

3. **Verify database connectivity**
   ```bash
   docker exec postgres-1 psql -U postgres -d pipeshub -c "\dt"
   ```

4. **Check current record count**
   ```bash
   docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT COUNT(*) as total, indexing_status, COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage FROM records GROUP BY indexing_status;"
   ```

5. **Verify Kafka consumer group status**
   ```bash
   docker exec kafka-1 kafka-consumer-groups \
     --bootstrap-server localhost:9092 \
     --group records_consumer_group \
     --describe
   ```

### Success Criteria
- ✅ All Docker services running
- ✅ Database accessible
- ✅ ~1,690 records visible with `indexingStatus: NOT_STARTED`
- ✅ Consumer lag confirms ~44,952 messages
- ✅ Research findings validated

### Decision Point
- If services are down → Execute Phase 2 (Docker deployment)
- If database is empty → Execute Phase 1 (Database clean + Phase 6 sync)
- If current state matches research → **Proceed directly to Phase 3** ✅ RECOMMENDED

---

## Phase 1: Database Clean (OPTIONAL - 10 minutes)

**⚠️ RECOMMENDATION**: **SKIP THIS PHASE** - Existing data is valid

**Purpose**: Clean slate for fresh data (only if needed)

### When to Execute
- If data corruption detected
- If testing requires fresh start
- If explicitly requested

### Tasks

1. **Stop indexing service** (prevent interference)
   ```bash
   docker stop indexing-service-1
   ```

2. **Clean records table**
   ```bash
   docker exec postgres-1 psql -U postgres -d pipeshub -c "TRUNCATE TABLE records CASCADE;"
   ```

3. **Clean chunks table**
   ```bash
   docker exec postgres-1 psql -U postgres -d pipeshub -c "TRUNCATE TABLE chunks CASCADE;"
   ```

4. **Clean vector store** (Qdrant)
   ```bash
   curl -X DELETE "http://localhost:6333/collections/records" \
     -H "Content-Type: application/json"
   ```

5. **Recreate Qdrant collection**
   ```bash
   curl -X PUT "http://localhost:6333/collections/records" \
     -H "Content-Type: application/json" \
     -d '{
       "vectors": {
         "size": 1536,
         "distance": "Cosine"
       }
     }'
   ```

6. **Restart indexing service**
   ```bash
   docker start indexing-service-1
   ```

7. **Verify clean state**
   ```bash
   docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT COUNT(*) FROM records;"
   docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT COUNT(*) FROM chunks;"
   curl "http://localhost:6333/collections/records" | jq '.result.points_count'
   ```

### Success Criteria
- ✅ Records table empty (count = 0)
- ✅ Chunks table empty (count = 0)
- ✅ Qdrant collection empty (points_count = 0)
- ✅ Indexing service running

### Next Steps
- If cleaned → Execute Phase 3 (Kafka reset) + Phase 6 (sync)
- If skipped → Proceed to Phase 2 or Phase 3

---

## Phase 2: Docker Deployment (OPTIONAL - 5 minutes)

**⚠️ RECOMMENDATION**: **SKIP THIS PHASE** - Services already healthy

**Purpose**: Redeploy services (only if needed)

### When to Execute
- If services are down
- If configuration changes made
- If explicit rebuild requested

### Tasks

1. **Stop all services**
   ```bash
   cd /Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig
   docker-compose down
   ```

2. **Rebuild services** (if code changes)
   ```bash
   docker-compose build --no-cache
   ```

   OR **Pull latest images** (if no code changes)
   ```bash
   docker-compose pull
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Wait for services to be healthy**
   ```bash
   sleep 30
   docker ps --format "table {{.Names}}\t{{.Status}}"
   ```

5. **Verify service connectivity**
   ```bash
   # Check backend API
   curl -s http://localhost:3001/health | jq

   # Check Qdrant
   curl -s http://localhost:6333/collections | jq

   # Check Kafka
   docker exec kafka-1 kafka-topics --bootstrap-server localhost:9092 --list
   ```

### Success Criteria
- ✅ All containers running (status "Up")
- ✅ Backend API responding (health check passes)
- ✅ Qdrant responding
- ✅ Kafka broker accessible
- ✅ Indexing service running

### Next Steps
Proceed to Phase 3 (Kafka offset reset)

---

## Phase 3: Kafka Offset Reset ⚠️ CRITICAL BLOCKER FIX (5 minutes)

**🔥 CRITICAL**: This phase resolves the primary blocker

**Purpose**: Reset Kafka consumer offset to skip old/invalid messages

### Why This Matters
The indexing service is stuck processing 44,952 old messages from previous test runs. These messages reference records that no longer exist in the database, causing infinite retry loops and blocking ALL indexing operations.

### Tasks

1. **Stop indexing service** (required before offset reset)
   ```bash
   docker stop indexing-service-1
   ```

2. **Verify current consumer lag**
   ```bash
   docker exec kafka-1 kafka-consumer-groups \
     --bootstrap-server localhost:9092 \
     --group records_consumer_group \
     --describe
   ```

   Expected output:
   ```
   TOPIC           PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
   record-events   0          46458           91410           44952
   ```

3. **Reset offset to latest** ⚠️ CRITICAL COMMAND
   ```bash
   docker exec kafka-1 kafka-consumer-groups \
     --bootstrap-server localhost:9092 \
     --group records_consumer_group \
     --reset-offsets \
     --topic record-events \
     --to-latest \
     --execute
   ```

   Expected output:
   ```
   TOPIC           PARTITION  NEW-OFFSET
   record-events   0          91410
   ```

4. **Verify offset reset**
   ```bash
   docker exec kafka-1 kafka-consumer-groups \
     --bootstrap-server localhost:9092 \
     --group records_consumer_group \
     --describe
   ```

   Expected result: `LAG` should be 0

5. **Restart indexing service**
   ```bash
   docker start indexing-service-1
   ```

6. **Monitor service logs** (verify no retry errors)
   ```bash
   docker logs -f --tail 50 indexing-service-1
   ```

   Look for:
   - ✅ "Connected to Kafka" messages
   - ✅ No "Record not found" errors
   - ✅ No infinite retry loops

### Alternative: Reset to Earliest (if full reprocessing needed)

**⚠️ NOT RECOMMENDED** - Takes much longer (processes all 91,410 messages)

```bash
docker exec kafka-1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group records_consumer_group \
  --reset-offsets \
  --topic record-events \
  --to-earliest \
  --execute
```

### Success Criteria
- ✅ Consumer offset reset to latest (91,410)
- ✅ Consumer lag = 0
- ✅ Indexing service restarted successfully
- ✅ No retry loop errors in logs
- ✅ Service ready to process new events

### Impact
This single operation unblocks ALL indexing operations. Once complete, the system can begin processing new indexing requests immediately.

### Next Steps
Proceed to Phase 4 (UI setup) or Phase 6 (trigger indexing)

---

## Phase 4: UI Account Setup (5 minutes)

**Purpose**: Create user account for demo

### Tasks

1. **Access UI**
   ```
   Open browser: http://localhost:3000
   ```

2. **Register new account**
   - Email: `demo@pipeshub.local` (or your preference)
   - Password: `Demo123!` (or your preference)
   - Click "Sign Up"

3. **Verify login**
   - Should redirect to dashboard
   - Check for empty connectors list

4. **Document credentials** (for demo reference)
   ```bash
   echo "Demo Account" > /Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/.prompts/012-demo-prep-plan/demo-credentials.txt
   echo "Email: demo@pipeshub.local" >> /Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/.prompts/012-demo-prep-plan/demo-credentials.txt
   echo "Password: Demo123!" >> /Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/.prompts/012-demo-prep-plan/demo-credentials.txt
   ```

### Success Criteria
- ✅ Account created successfully
- ✅ Login successful
- ✅ Dashboard accessible
- ✅ Credentials documented

### Next Steps
Proceed to Phase 5 (connector setup)

---

## Phase 5: Connector Configuration (5 minutes)

**Purpose**: Configure local filesystem connector

### Tasks

1. **Navigate to Connectors**
   - Click "Connectors" in sidebar
   - Click "Add Connector" or "+"

2. **Select Connector Type**
   - Choose "Local Filesystem"

3. **Configure Connector**
   ```
   Name: Demo Documents
   Path: /workspace/sample-documents
   File Types: .txt, .md, .pdf (select all available)
   Sync Schedule: Manual (for demo control)
   ```

4. **Save Configuration**
   - Click "Save" or "Create"
   - Verify connector appears in list

5. **Verify connector in database**
   ```bash
   docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT id, name, connector_type, config FROM connectors ORDER BY created_at DESC LIMIT 1;"
   ```

### Success Criteria
- ✅ Connector created successfully
- ✅ Connector visible in UI
- ✅ Connector stored in database
- ✅ Configuration correct

### Next Steps
Proceed to Phase 6 (initial sync)

---

## Phase 6: Initial Sync / Verify Existing Records (10 minutes)

**Purpose**: Trigger sync or verify existing 1,690 records

### Decision Point

**Option A: Use Existing Records** ✅ RECOMMENDED (fastest)
- 1,690 valid records already in database
- All have `indexingStatus: NOT_STARTED`
- Can proceed directly to indexing
- Saves 5-10 minutes

**Option B: Fresh Sync**
- Required if Phase 1 was executed (database cleaned)
- Required if existing records are invalid
- Takes 5-10 minutes to sync

### Tasks for Option A (Use Existing)

1. **Verify existing records**
   ```bash
   docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT COUNT(*) as total, indexing_status FROM records GROUP BY indexing_status;"
   ```

   Expected: ~1,690 records with `NOT_STARTED`

2. **Check record metadata**
   ```bash
   docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT id, file_path, file_type, file_size, indexing_status FROM records LIMIT 5;"
   ```

3. **Skip to Phase 7** (trigger indexing)

### Tasks for Option B (Fresh Sync)

1. **Trigger sync in UI**
   - Navigate to connector
   - Click "Sync Now" or "Run Sync"
   - Observe progress indicator

2. **Monitor sync logs**
   ```bash
   docker logs -f --tail 100 backend-1
   ```

   Look for:
   - "Starting sync for connector..."
   - "Found X files"
   - "Created X records"
   - "Sync completed"

3. **Verify records created**
   ```bash
   docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT COUNT(*) as total FROM records;"
   ```

4. **Check Kafka messages**
   ```bash
   docker exec kafka-1 kafka-consumer-groups \
     --bootstrap-server localhost:9092 \
     --group records_consumer_group \
     --describe
   ```

   Should show new messages in topic (lag > 0)

5. **Verify indexing status**
   ```bash
   docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT indexing_status, COUNT(*) FROM records GROUP BY indexing_status;"
   ```

   Expected: All records `NOT_STARTED` or `IN_PROGRESS`

### Success Criteria

**Option A**:
- ✅ 1,690 existing records verified
- ✅ All records have `NOT_STARTED` status
- ✅ Ready for indexing

**Option B**:
- ✅ Sync completed successfully
- ✅ Records created in database
- ✅ Kafka messages published
- ✅ Records have `NOT_STARTED` status

### Next Steps
Proceed to Phase 7 (monitor indexing)

---

## Phase 7: Monitor Indexing Progress (30-60 minutes) ⏱️

**Purpose**: Watch indexing progress to 100% completion

**⚠️ LONGEST PHASE**: This is where time is spent

### Expected Timeline
- **Total records**: 1,690
- **Rate**: ~28-56 records/minute (conservative estimate)
- **Duration**: 30-60 minutes
- **Progress checkpoints**: Every 5-10 minutes

### Tasks

1. **Trigger indexing** (if not auto-started)

   **Method 1: Via UI** (if available)
   - Navigate to connector or records view
   - Click "Index All" or similar button

   **Method 2: Via API** (if UI not available)
   ```bash
   # Get connector ID
   CONNECTOR_ID=$(docker exec postgres-1 psql -U postgres -d pipeshub -t -c "SELECT id FROM connectors ORDER BY created_at DESC LIMIT 1;" | tr -d ' ')

   # Trigger indexing
   curl -X POST "http://localhost:3001/api/connectors/${CONNECTOR_ID}/index" \
     -H "Content-Type: application/json"
   ```

   **Method 3: Publish Kafka events manually** (if needed)
   ```bash
   # Get records that need indexing
   docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT id FROM records WHERE indexing_status = 'NOT_STARTED' LIMIT 10;"

   # Publish events to Kafka (example for one record)
   docker exec kafka-1 kafka-console-producer \
     --bootstrap-server localhost:9092 \
     --topic record-events << EOF
   {"eventType":"RECORD_CREATED","recordId":"<record-id-from-above>"}
   EOF
   ```

2. **Monitor indexing service logs** (real-time)
   ```bash
   docker logs -f --tail 100 indexing-service-1
   ```

   Look for:
   - ✅ "Processing record: {id}" messages
   - ✅ "Chunking completed: X chunks"
   - ✅ "Embeddings generated: X vectors"
   - ✅ "Indexed successfully: {id}"
   - ❌ No error messages
   - ❌ No retry loops

3. **Check progress every 5 minutes**
   ```bash
   docker exec postgres-1 psql -U postgres -d pipeshub -c "
     SELECT
       indexing_status,
       COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
     FROM records
     GROUP BY indexing_status
     ORDER BY indexing_status;
   "
   ```

   Expected progression:
   ```
   T=0min:  NOT_STARTED: 1690 (100%), INDEXED: 0 (0%)
   T=10min: NOT_STARTED: 1400 (83%), IN_PROGRESS: 10 (1%), INDEXED: 280 (16%)
   T=20min: NOT_STARTED: 1100 (65%), IN_PROGRESS: 5 (0.3%), INDEXED: 585 (35%)
   T=30min: NOT_STARTED: 800 (47%), IN_PROGRESS: 5 (0.3%), INDEXED: 885 (52%)
   T=45min: NOT_STARTED: 400 (24%), IN_PROGRESS: 5 (0.3%), INDEXED: 1285 (76%)
   T=60min: NOT_STARTED: 0 (0%), INDEXED: 1690 (100%)
   ```

4. **Monitor Kafka consumer lag**
   ```bash
   docker exec kafka-1 kafka-consumer-groups \
     --bootstrap-server localhost:9092 \
     --group records_consumer_group \
     --describe
   ```

   - `LAG` should remain low (< 100)
   - `CURRENT-OFFSET` should steadily increase
   - If lag grows significantly → investigate performance

5. **Check vector store progress**
   ```bash
   curl -s "http://localhost:6333/collections/records" | jq '.result.points_count'
   ```

   Should increase proportionally with indexed records

6. **Monitor database chunks**
   ```bash
   docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT COUNT(*) FROM chunks;"
   ```

   Expected: 5,000-10,000 chunks for 1,690 records (avg 3-6 chunks per record)

### Troubleshooting

**If indexing stalls (no progress for 10+ minutes)**:

1. Check service health:
   ```bash
   docker ps --filter name=indexing-service
   docker logs --tail 100 indexing-service-1
   ```

2. Check for errors in logs:
   ```bash
   docker logs indexing-service-1 | grep -i "error\|exception\|failed"
   ```

3. Verify Kafka connectivity:
   ```bash
   docker exec kafka-1 kafka-consumer-groups \
     --bootstrap-server localhost:9092 \
     --group records_consumer_group \
     --describe
   ```

4. Restart indexing service:
   ```bash
   docker restart indexing-service-1
   ```

**If indexing is too slow (< 20 records/minute)**:

1. Check resource usage:
   ```bash
   docker stats --no-stream
   ```

2. Check OpenAI API rate limits (if using OpenAI embeddings)
   - May need to adjust batch size
   - May need to add delays between requests

3. Consider parallel processing (if service supports it)

### Success Criteria
- ✅ All 1,690 records have `indexing_status = 'INDEXED'`
- ✅ 0 records with `NOT_STARTED` status
- ✅ 5,000-10,000 chunks created
- ✅ 5,000-10,000 vectors in Qdrant
- ✅ No errors in indexing service logs
- ✅ Kafka consumer lag = 0

### Next Steps
Proceed to Phase 8 (Q&A testing)

---

## Phase 8: Assistant Q&A Testing (10 minutes)

**Purpose**: Verify end-to-end functionality

### Tasks

1. **Access Q&A interface**
   ```
   Navigate in UI: Dashboard → Assistant or Chat
   OR
   Open: http://localhost:3000/chat
   ```

2. **Test basic query**
   ```
   Query: "What documents do we have?"

   Expected: List of indexed documents or summary
   ```

3. **Test specific content query**
   ```
   Query: "Tell me about [specific topic from your documents]"

   Expected: Relevant answer with citations
   ```

4. **Test semantic search**
   ```
   Query: "Find information about [concept not directly mentioned]"

   Expected: Related content based on semantic similarity
   ```

5. **Verify citations**
   - Check that responses include source references
   - Verify source references are accurate
   - Confirm links to original documents work

6. **Test edge cases**
   ```
   Query: "What is the capital of France?"

   Expected: "I can only answer questions based on indexed documents"
   OR similar response indicating scope limitation
   ```

7. **Monitor query logs**
   ```bash
   docker logs -f --tail 50 backend-1
   ```

   Look for:
   - Query received
   - Vector search performed
   - Context retrieved
   - LLM response generated

8. **Check query performance**
   - Note response time for each query
   - Should be < 5 seconds for typical queries
   - If slow → investigate vector search or LLM latency

### Test Queries Template

Create a test script for consistent testing:

```bash
# Save test queries
cat > /Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/.prompts/012-demo-prep-plan/test-queries.txt << 'EOF'
1. What documents do we have?
2. Summarize the key topics across all documents.
3. [Specific technical question about your domain]
4. [Question requiring inference from multiple documents]
5. What is the meaning of life? (should fail gracefully)
EOF
```

### Success Criteria
- ✅ Q&A interface accessible
- ✅ Queries return relevant results
- ✅ Citations included and accurate
- ✅ Response time < 5 seconds
- ✅ Edge cases handled gracefully
- ✅ No errors in backend logs

### Next Steps
Proceed to Phase 9 (demo rehearsal) OR declare demo-ready

---

## Phase 9: Demo Rehearsal (OPTIONAL - 10 minutes)

**Purpose**: Practice demo flow and identify issues

### Tasks

1. **Create demo script**
   ```markdown
   # Demo Script

   ## Introduction (1 min)
   - "Today I'll show you PipesHub AI, a knowledge base platform"
   - "We've indexed 1,690 documents from our local filesystem"

   ## Live Demo (5 min)

   ### 1. Show Connectors
   - Navigate to Connectors page
   - Highlight configured connector
   - Show sync status

   ### 2. Show Knowledge Base
   - Navigate to Records/Documents page
   - Show total indexed: 1,690
   - Filter by file type
   - Open a document detail view

   ### 3. Q&A Session
   - Navigate to Assistant/Chat
   - Ask: "What documents do we have?"
   - Ask: [Specific content question]
   - Highlight citations
   - Show source links

   ### 4. Advanced Features
   - Show vector search
   - Show semantic similarity
   - Show multi-document synthesis

   ## Wrap-up (1 min)
   - Summary of capabilities
   - Q&A
   ```

2. **Rehearse demo flow**
   - Follow script exactly
   - Time each section
   - Note any lag or issues

3. **Take screenshots**
   ```bash
   # Create screenshots directory
   mkdir -p /Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/.prompts/012-demo-prep-plan/screenshots

   # Document locations for manual screenshots:
   # - Connectors list view
   # - Records/documents list (showing 1,690)
   # - Document detail view
   # - Q&A interface with response
   # - Citations example
   ```

4. **Test backup scenarios**
   - What if Q&A is slow?
   - What if a query fails?
   - What if UI is unresponsive?

5. **Prepare fallback queries**
   - Have 5-10 tested queries ready
   - Know which queries give best responses
   - Avoid queries that might fail

### Demo Day Checklist

Save to `.prompts/012-demo-prep-plan/demo-day-checklist.md`:

```markdown
# Demo Day Checklist

## Pre-Demo (30 min before)

- [ ] All Docker containers running
- [ ] Database accessible
- [ ] Verify record count: 1,690 indexed
- [ ] Verify Qdrant vector count: ~5,000-10,000
- [ ] Test Q&A with 2-3 queries
- [ ] Browser open to login page
- [ ] Demo script visible
- [ ] Backup queries ready
- [ ] Screen sharing tested
- [ ] Audio tested

## During Demo

- [ ] Login with demo account
- [ ] Navigate confidently
- [ ] Speak clearly about features
- [ ] Highlight key metrics (1,690 docs indexed)
- [ ] Show real-time Q&A
- [ ] Emphasize citations and accuracy
- [ ] Handle questions gracefully

## Post-Demo

- [ ] Note feedback
- [ ] Document issues encountered
- [ ] List feature requests
- [ ] Update roadmap
```

### Success Criteria
- ✅ Demo script complete and tested
- ✅ Demo flows smoothly (< 10 minutes)
- ✅ All features demonstrated successfully
- ✅ Screenshots captured
- ✅ Backup plans prepared
- ✅ Checklist ready for demo day

---

## Timeline and Estimates

### Recommended Path (Fastest to Demo-Ready)

**Skip**: Phases 1, 2, 9
**Execute**: Phases 0, 3, 4, 5, 6A, 7, 8

| Phase | Duration | Cumulative | Critical |
|-------|----------|------------|----------|
| Phase 0: Pre-deployment prep | 5 min | 5 min | ⚠️ |
| **Phase 3: Kafka offset reset** | **5 min** | **10 min** | **🔥 CRITICAL** |
| Phase 4: UI account setup | 5 min | 15 min | |
| Phase 5: Connector config | 5 min | 20 min | |
| Phase 6A: Verify existing records | 2 min | 22 min | |
| **Phase 7: Monitor indexing** | **30-60 min** | **52-82 min** | **⏱️ LONGEST** |
| Phase 8: Q&A testing | 10 min | 62-92 min | ⚠️ |
| **TOTAL** | **62-92 min** | | |

### Full Path (If Clean Start Needed)

**Execute**: All phases 0-9

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 0: Pre-deployment prep | 5 min | 5 min |
| Phase 1: Database clean | 10 min | 15 min |
| Phase 2: Docker deployment | 5 min | 20 min |
| Phase 3: Kafka offset reset | 5 min | 25 min |
| Phase 4: UI account setup | 5 min | 30 min |
| Phase 5: Connector config | 5 min | 35 min |
| Phase 6B: Fresh sync | 10 min | 45 min |
| Phase 7: Monitor indexing | 30-60 min | 75-105 min |
| Phase 8: Q&A testing | 10 min | 85-115 min |
| Phase 9: Demo rehearsal | 10 min | 95-125 min |
| **TOTAL** | **95-125 min** | |

---

## Decision Matrix

### Key Decisions and Recommendations

| Decision | Options | Recommendation | Reason |
|----------|---------|----------------|--------|
| **Database clean?** | Clean / Keep | **Keep** ✅ | Data is valid, saves 10 min |
| **Docker redeploy?** | Redeploy / Keep | **Keep** ✅ | Services healthy, saves 5 min |
| **Kafka offset reset** | to-latest / to-earliest | **to-latest** ✅ | Skips old messages, unblocks indexing |
| **Use existing records?** | Use / Fresh sync | **Use** ✅ | 1,690 valid records, saves 10 min |
| **Demo rehearsal?** | Yes / No | **Optional** | 5+ hours buffer available |

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Indexing slower than estimated | Medium | High | Start early, monitor progress, have buffer |
| Kafka offset reset fails | Low | High | Test in Phase 0, have rollback plan |
| Q&A returns poor results | Medium | Medium | Pre-test queries, have backup questions |
| Service crashes during demo | Low | High | Restart services pre-demo, have logs ready |
| Network/API issues | Low | Medium | Test connectivity, have offline fallback |

---

## Verification Commands Reference

### Quick Health Check (Run Anytime)

```bash
# All-in-one health check
docker ps --format "table {{.Names}}\t{{.Status}}" && \
echo "\n=== Database Records ===" && \
docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT indexing_status, COUNT(*) as count, ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as pct FROM records GROUP BY indexing_status;" && \
echo "\n=== Vector Store ===" && \
curl -s "http://localhost:6333/collections/records" | jq '.result.points_count' && \
echo "\n=== Kafka Consumer ===" && \
docker exec kafka-1 kafka-consumer-groups --bootstrap-server localhost:9092 --group records_consumer_group --describe
```

### Individual Checks

```bash
# Docker services
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Database records count
docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT COUNT(*) FROM records;"

# Indexing status distribution
docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT indexing_status, COUNT(*) FROM records GROUP BY indexing_status;"

# Chunks count
docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT COUNT(*) FROM chunks;"

# Qdrant vector count
curl -s "http://localhost:6333/collections/records" | jq '.result.points_count'

# Kafka consumer lag
docker exec kafka-1 kafka-consumer-groups --bootstrap-server localhost:9092 --group records_consumer_group --describe

# Indexing service logs (last 50 lines)
docker logs --tail 50 indexing-service-1

# Backend API health
curl -s http://localhost:3001/health | jq
```

---

## Rollback Procedures

### If Kafka Reset Goes Wrong

1. **Check current offset**
   ```bash
   docker exec kafka-1 kafka-consumer-groups \
     --bootstrap-server localhost:9092 \
     --group records_consumer_group \
     --describe
   ```

2. **Reset to specific offset** (if known good offset)
   ```bash
   docker exec kafka-1 kafka-consumer-groups \
     --bootstrap-server localhost:9092 \
     --group records_consumer_group \
     --reset-offsets \
     --topic record-events \
     --to-offset <good-offset> \
     --execute
   ```

3. **Reset to earliest** (reprocess all messages)
   ```bash
   docker exec kafka-1 kafka-consumer-groups \
     --bootstrap-server localhost:9092 \
     --group records_consumer_group \
     --reset-offsets \
     --topic record-events \
     --to-earliest \
     --execute
   ```

### If Database Clean Needed (Undo)

**Cannot undo clean operation** - data is permanently deleted

Options:
1. Restore from backup (if available)
2. Re-run sync to recreate records
3. Re-run indexing to recreate chunks and vectors

### If Services Become Unstable

1. **Restart specific service**
   ```bash
   docker restart <service-name>
   ```

2. **Restart all services**
   ```bash
   cd /Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig
   docker-compose restart
   ```

3. **Full redeploy**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

---

## Success Metrics

### Phase Completion Metrics

Track completion of each phase in this checklist:

```markdown
## Phase Completion Tracker

- [ ] Phase 0: Pre-deployment prep ✅
- [ ] Phase 1: Database clean (SKIPPED - not needed)
- [ ] Phase 2: Docker deployment (SKIPPED - services healthy)
- [ ] Phase 3: Kafka offset reset ✅ **CRITICAL**
- [ ] Phase 4: UI account setup ✅
- [ ] Phase 5: Connector configuration ✅
- [ ] Phase 6: Initial sync / verify records ✅
- [ ] Phase 7: Monitor indexing to 100% ✅ **LONGEST**
- [ ] Phase 8: Q&A testing ✅
- [ ] Phase 9: Demo rehearsal (OPTIONAL)

## Demo-Ready Criteria

- [ ] 1,690 records with `indexingStatus: INDEXED`
- [ ] 5,000-10,000 chunks in database
- [ ] 5,000-10,000 vectors in Qdrant
- [ ] Kafka consumer lag = 0
- [ ] Q&A returns relevant results with citations
- [ ] No errors in service logs
- [ ] Response time < 5 seconds
- [ ] Demo account accessible
- [ ] All Docker services healthy

## Final Go/No-Go

**GO for demo if**:
- All "Demo-Ready Criteria" checked ✅
- Phase 3 completed successfully (critical blocker resolved)
- Phase 7 completed successfully (100% indexed)
- Phase 8 completed successfully (Q&A working)

**NO-GO if**:
- Kafka consumer still lagging
- Less than 80% records indexed
- Q&A returning errors or no results
- Services unstable or crashing
```

---

## Post-Execution Report Template

After completing deployment, document results:

```markdown
# Deployment Execution Report

**Date**: 2025-11-28
**Executed by**: [Your name]
**Duration**: [Actual time taken]

## Phases Executed

| Phase | Executed? | Duration | Issues |
|-------|-----------|----------|--------|
| Phase 0 | Yes/No | X min | None / [describe] |
| Phase 1 | Yes/No | X min | None / [describe] |
| Phase 2 | Yes/No | X min | None / [describe] |
| Phase 3 | Yes/No | X min | None / [describe] |
| Phase 4 | Yes/No | X min | None / [describe] |
| Phase 5 | Yes/No | X min | None / [describe] |
| Phase 6 | Yes/No | X min | None / [describe] |
| Phase 7 | Yes/No | X min | None / [describe] |
| Phase 8 | Yes/No | X min | None / [describe] |
| Phase 9 | Yes/No | X min | None / [describe] |

## Final Metrics

- **Total records**: [number]
- **Indexed records**: [number] ([percentage]%)
- **Total chunks**: [number]
- **Total vectors**: [number]
- **Kafka consumer lag**: [number]
- **Q&A test results**: [X/Y passed]
- **Average response time**: [seconds]

## Issues Encountered

1. [Issue description]
   - **Resolution**: [How it was resolved]
   - **Time impact**: [minutes]

## Deviations from Plan

- [What was done differently than planned]
- [Why the deviation was necessary]
- [Outcome of the deviation]

## Lessons Learned

- [What worked well]
- [What could be improved]
- [Recommendations for next time]

## Demo Readiness

**Status**: READY / NOT READY

**Justification**: [Why ready or not ready]

**Remaining issues**: [List any outstanding issues]

**Mitigation for demo**: [How to work around issues during demo]
```

---

## Emergency Contacts and Resources

### Documentation Links

- Docker Compose: `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/docker-compose.yml`
- Research findings: `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/.prompts/011-debug-indexing-research/`
- Backend code: `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/backend/`
- Frontend code: `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/frontend/`

### Service Ports

- Frontend UI: http://localhost:3000
- Backend API: http://localhost:3001
- Qdrant: http://localhost:6333
- PostgreSQL: localhost:5432
- Kafka: localhost:9092
- Kafka UI: http://localhost:8080

### Log Locations

```bash
# All service logs
docker-compose logs

# Specific service
docker logs <service-name>

# Follow logs
docker logs -f --tail 100 <service-name>

# Search logs
docker logs <service-name> | grep "error"
```

---

## Appendix: Command Quick Reference

### Database Queries

```bash
# Count records by status
docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT indexing_status, COUNT(*) FROM records GROUP BY indexing_status;"

# Count total records
docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT COUNT(*) FROM records;"

# Count chunks
docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT COUNT(*) FROM chunks;"

# Show recent records
docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT id, file_path, indexing_status, created_at FROM records ORDER BY created_at DESC LIMIT 10;"

# Show connectors
docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT id, name, connector_type, status FROM connectors;"
```

### Kafka Commands

```bash
# List consumer groups
docker exec kafka-1 kafka-consumer-groups --bootstrap-server localhost:9092 --list

# Describe consumer group
docker exec kafka-1 kafka-consumer-groups --bootstrap-server localhost:9092 --group records_consumer_group --describe

# List topics
docker exec kafka-1 kafka-topics --bootstrap-server localhost:9092 --list

# Describe topic
docker exec kafka-1 kafka-topics --bootstrap-server localhost:9092 --describe --topic record-events

# Reset offset to latest
docker exec kafka-1 kafka-consumer-groups --bootstrap-server localhost:9092 --group records_consumer_group --reset-offsets --topic record-events --to-latest --execute

# Reset offset to earliest
docker exec kafka-1 kafka-consumer-groups --bootstrap-server localhost:9092 --group records_consumer_group --reset-offsets --topic record-events --to-earliest --execute
```

### Qdrant Commands

```bash
# Get collection info
curl -s "http://localhost:6333/collections/records" | jq

# Count vectors
curl -s "http://localhost:6333/collections/records" | jq '.result.points_count'

# List all collections
curl -s "http://localhost:6333/collections" | jq

# Delete collection
curl -X DELETE "http://localhost:6333/collections/records"

# Create collection
curl -X PUT "http://localhost:6333/collections/records" \
  -H "Content-Type: application/json" \
  -d '{"vectors": {"size": 1536, "distance": "Cosine"}}'
```

### Docker Commands

```bash
# List containers
docker ps

# List all containers (including stopped)
docker ps -a

# Container stats
docker stats --no-stream

# Restart service
docker restart <service-name>

# Stop service
docker stop <service-name>

# Start service
docker start <service-name>

# View logs
docker logs <service-name>

# Follow logs
docker logs -f <service-name>

# Execute command in container
docker exec <container-name> <command>

# Restart all services
docker-compose restart

# Stop all services
docker-compose down

# Start all services
docker-compose up -d
```

---

## Final Checklist

Before declaring demo-ready, verify ALL items:

### Infrastructure
- [ ] All Docker containers running (no restarts)
- [ ] PostgreSQL accessible and responding
- [ ] Kafka broker healthy
- [ ] Qdrant responding
- [ ] Backend API health check passes
- [ ] Frontend accessible at localhost:3000

### Data Integrity
- [ ] 1,690 records in database
- [ ] All records have `indexingStatus: INDEXED`
- [ ] 5,000-10,000 chunks created
- [ ] 5,000-10,000 vectors in Qdrant
- [ ] No orphaned records (all linked to valid connectors)

### Kafka Health
- [ ] Consumer group `records_consumer_group` exists
- [ ] Consumer offset at latest position
- [ ] Consumer lag = 0 or very low (< 10)
- [ ] Topic `record-events` has messages
- [ ] No consumer errors in logs

### Indexing Service
- [ ] Service running and healthy
- [ ] No error messages in logs
- [ ] No retry loops
- [ ] Connected to Kafka
- [ ] Connected to database
- [ ] Connected to Qdrant

### Q&A Functionality
- [ ] Assistant/chat interface accessible
- [ ] Test queries return results
- [ ] Results are relevant to indexed content
- [ ] Citations included in responses
- [ ] Source links work
- [ ] Response time < 5 seconds
- [ ] Edge cases handled gracefully

### Demo Preparation
- [ ] Demo account created and tested
- [ ] Demo script prepared
- [ ] Test queries documented
- [ ] Screenshots captured (optional)
- [ ] Backup plans prepared
- [ ] Demo day checklist ready

### Documentation
- [ ] Execution report completed
- [ ] Issues documented
- [ ] Lessons learned captured
- [ ] Next steps identified

---

## Conclusion

This deployment plan provides a comprehensive, step-by-step approach to achieving demo-ready state by 10AM PST. The **critical blocker (Kafka consumer lag)** is addressed in Phase 3, and the **longest operation (indexing)** is monitored in Phase 7.

**Recommended execution path**: Phases 0, 3, 4, 5, 6A, 7, 8 (skip 1, 2, 9)

**Total estimated time**: 55-85 minutes

**Buffer available**: 5+ hours for testing and contingency

**Critical success factors**:
1. Phase 3 must succeed (Kafka offset reset)
2. Phase 7 must complete (100% indexing)
3. Phase 8 must pass (Q&A working)

**Go/No-Go decision**: Based on completion of critical phases and achievement of demo-ready criteria listed above.

Good luck with the deployment and demo!
