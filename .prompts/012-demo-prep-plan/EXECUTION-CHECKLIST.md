# Demo Preparation Execution Checklist

**Track your progress through the deployment plan.**

## Pre-Execution Verification

- [ ] Research findings reviewed (`.prompts/011-debug-indexing-research/`)
- [ ] Time available: ~7-8 hours until demo
- [ ] Execution estimate: 55-85 minutes
- [ ] Buffer: 5+ hours for testing

---

## Phase 0: Pre-Deployment Prep (5 min)

**Start time**: ___:___

- [ ] Review research SUMMARY.md
- [ ] Check Docker services: `docker ps`
- [ ] Verify database connectivity
- [ ] Count current records (expect ~1,690)
- [ ] Check Kafka consumer lag (expect ~44,952)
- [ ] **Decision**: Current state matches research?
  - [ ] YES → Skip to Phase 3 (RECOMMENDED)
  - [ ] NO → Execute Phase 1 & 2

**End time**: ___:___
**Issues**: _______________________

---

## Phase 1: Database Clean (OPTIONAL - 10 min)

**⚠️ RECOMMENDATION: SKIP THIS PHASE**

**Start time**: ___:___

- [ ] Stop indexing service
- [ ] Truncate records table
- [ ] Truncate chunks table
- [ ] Delete Qdrant collection
- [ ] Recreate Qdrant collection
- [ ] Restart indexing service
- [ ] Verify clean state (all counts = 0)

**End time**: ___:___
**Issues**: _______________________

---

## Phase 2: Docker Deployment (OPTIONAL - 5 min)

**⚠️ RECOMMENDATION: SKIP THIS PHASE**

**Start time**: ___:___

- [ ] Stop all services: `docker-compose down`
- [ ] Build/pull images
- [ ] Start services: `docker-compose up -d`
- [ ] Wait 30 seconds for health
- [ ] Verify all containers running
- [ ] Test backend API health
- [ ] Test Qdrant connectivity
- [ ] Test Kafka connectivity

**End time**: ___:___
**Issues**: _______________________

---

## Phase 3: Kafka Offset Reset 🔥 CRITICAL (5 min)

**Start time**: ___:___

- [ ] Stop indexing service: `docker stop indexing-service-1`
- [ ] Check current consumer lag (expect 44,952)
- [ ] **Execute reset command**:
  ```bash
  docker exec kafka-1 kafka-consumer-groups \
    --bootstrap-server localhost:9092 \
    --group records_consumer_group \
    --reset-offsets \
    --topic record-events \
    --to-latest \
    --execute
  ```
- [ ] Verify offset reset (NEW-OFFSET should be 91,410)
- [ ] Verify lag = 0
- [ ] Restart indexing service: `docker start indexing-service-1`
- [ ] Monitor logs for 1 minute (no retry errors)
- [ ] **SUCCESS CRITERIA**: Lag = 0, no retry loops

**End time**: ___:___
**Issues**: _______________________

---

## Phase 4: UI Account Setup (5 min)

**Start time**: ___:___

- [ ] Open browser: http://localhost:3000
- [ ] Click "Sign Up"
- [ ] Enter credentials:
  - Email: demo@pipeshub.local
  - Password: Demo123!
- [ ] Verify registration successful
- [ ] Verify login works
- [ ] Verify dashboard accessible
- [ ] Document credentials

**End time**: ___:___
**Issues**: _______________________

---

## Phase 5: Connector Configuration (5 min)

**Start time**: ___:___

- [ ] Navigate to Connectors page
- [ ] Click "Add Connector"
- [ ] Select "Local Filesystem"
- [ ] Configure:
  - Name: Demo Documents
  - Path: /workspace/sample-documents
  - File Types: .txt, .md, .pdf
  - Schedule: Manual
- [ ] Save configuration
- [ ] Verify connector appears in list
- [ ] Verify in database: `docker exec postgres-1 psql...`

**End time**: ___:___
**Issues**: _______________________

---

## Phase 6A: Verify Existing Records ✅ RECOMMENDED (2 min)

**Start time**: ___:___

- [ ] Count records: `docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT COUNT(*) FROM records;"`
- [ ] **Expected**: ~1,690 records
- [ ] Check status distribution
- [ ] **Expected**: All `NOT_STARTED`
- [ ] Sample 5 records to verify metadata
- [ ] **Decision**: Records valid?
  - [ ] YES → Proceed to Phase 7
  - [ ] NO → Execute Phase 6B (fresh sync)

**End time**: ___:___
**Issues**: _______________________

---

## Phase 6B: Fresh Sync (OPTIONAL - 10 min)

**⚠️ Only if Phase 1 executed or records invalid**

**Start time**: ___:___

- [ ] Navigate to connector in UI
- [ ] Click "Sync Now"
- [ ] Monitor sync logs: `docker logs -f backend-1`
- [ ] Wait for "Sync completed" message
- [ ] Verify record count increased
- [ ] Check Kafka messages published
- [ ] Verify all records `NOT_STARTED`

**End time**: ___:___
**Issues**: _______________________

---

## Phase 7: Monitor Indexing Progress ⏱️ LONGEST (30-60 min)

**Start time**: ___:___

### Trigger Indexing

- [ ] Method used: [ ] UI [ ] API [ ] Kafka manual
- [ ] Confirmed indexing started
- [ ] First record processed visible in logs

### Progress Tracking (check every 5 minutes)

**T+0 min** (___:___)
- [ ] Status: NOT_STARTED: ____, INDEXED: ____
- [ ] Percentage: ____%

**T+10 min** (___:___)
- [ ] Status: NOT_STARTED: ____, INDEXED: ____
- [ ] Percentage: ____%
- [ ] Expected: ~16%

**T+20 min** (___:___)
- [ ] Status: NOT_STARTED: ____, INDEXED: ____
- [ ] Percentage: ____%
- [ ] Expected: ~35%

**T+30 min** (___:___)
- [ ] Status: NOT_STARTED: ____, INDEXED: ____
- [ ] Percentage: ____%
- [ ] Expected: ~52%

**T+45 min** (___:___)
- [ ] Status: NOT_STARTED: ____, INDEXED: ____
- [ ] Percentage: ____%
- [ ] Expected: ~76%

**T+60 min** (___:___)
- [ ] Status: NOT_STARTED: ____, INDEXED: ____
- [ ] Percentage: ____%
- [ ] Expected: 100%

### Final Verification

- [ ] All 1,690 records `INDEXED`
- [ ] 0 records `NOT_STARTED`
- [ ] Chunks count: _____ (expect 5,000-10,000)
- [ ] Vectors count: _____ (expect 5,000-10,000)
- [ ] Kafka lag: _____ (expect 0)
- [ ] No errors in indexing service logs

**End time**: ___:___
**Issues**: _______________________

---

## Phase 8: Q&A Testing (10 min)

**Start time**: ___:___

### Test Queries

- [ ] **Query 1**: "What documents do we have?"
  - Response time: _____ sec
  - Quality: [ ] Good [ ] Poor
  - Citations: [ ] Yes [ ] No

- [ ] **Query 2**: "Tell me about [specific topic]"
  - Response time: _____ sec
  - Quality: [ ] Good [ ] Poor
  - Citations: [ ] Yes [ ] No

- [ ] **Query 3**: Semantic search query
  - Response time: _____ sec
  - Quality: [ ] Good [ ] Poor
  - Citations: [ ] Yes [ ] No

- [ ] **Query 4**: Edge case (unrelated question)
  - Response: [ ] Graceful failure [ ] Error
  - Message: _______________________

### Verification

- [ ] All responses < 5 seconds
- [ ] Citations accurate
- [ ] Source links work
- [ ] No errors in backend logs
- [ ] Q&A interface stable

**End time**: ___:___
**Issues**: _______________________

---

## Phase 9: Demo Rehearsal (OPTIONAL - 10 min)

**Start time**: ___:___

- [ ] Demo script created
- [ ] Full flow rehearsed (1-7 minutes)
- [ ] Screenshots captured
- [ ] Backup queries prepared
- [ ] Demo day checklist created
- [ ] Timing verified

**End time**: ___:___
**Issues**: _______________________

---

## Final Demo-Ready Verification

**Completion time**: ___:___
**Total execution time**: _____ minutes

### Critical Criteria

- [ ] **1,690 records indexed (100%)**
- [ ] **5,000-10,000 chunks created**
- [ ] **5,000-10,000 vectors in Qdrant**
- [ ] **Kafka consumer lag = 0**
- [ ] **Q&A returns relevant results**
- [ ] **Q&A includes citations**
- [ ] **Response time < 5 seconds**
- [ ] **All Docker services healthy**
- [ ] **No errors in service logs**

### GO/NO-GO Decision

**Status**: [ ] GO FOR DEMO [ ] NO-GO

**Justification**: ___________________________________________

**Remaining issues**: ________________________________________

**Mitigation plan**: _________________________________________

---

## Post-Execution Notes

### What Worked Well

1. _______________________
2. _______________________
3. _______________________

### Issues Encountered

1. _______________________
   - Resolution: _______________________
   - Time impact: _____ min

2. _______________________
   - Resolution: _______________________
   - Time impact: _____ min

### Deviations from Plan

1. _______________________
   - Reason: _______________________
   - Outcome: _______________________

### Lessons Learned

1. _______________________
2. _______________________
3. _______________________

### Recommendations for Next Time

1. _______________________
2. _______________________
3. _______________________

---

## Quick Reference Commands

### Health Check
```bash
docker ps --format "table {{.Names}}\t{{.Status}}" && \
echo "\n=== Database Records ===" && \
docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT indexing_status, COUNT(*) FROM records GROUP BY indexing_status;" && \
echo "\n=== Kafka Consumer ===" && \
docker exec kafka-1 kafka-consumer-groups --bootstrap-server localhost:9092 --group records_consumer_group --describe
```

### Progress Check
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

### Service Restart
```bash
docker restart indexing-service-1
docker restart backend-1
```

---

**Document saved**: `.prompts/012-demo-prep-plan/EXECUTION-CHECKLIST.md`
**Related files**:
- Full plan: `demo-prep-plan.md`
- Summary: `SUMMARY.md`
- Quick start: `QUICK-START.md`
