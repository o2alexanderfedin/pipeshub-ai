# Demo Preparation Plan Summary

**One-liner**: 9-phase deployment plan to achieve demo-ready state in 55-85 minutes by resetting Kafka consumer offset (critical blocker), monitoring indexing of 1,690 records to 100%, and validating Q&A functionality.

**Version**: v2 (Updated with research findings)

**Purpose**: Deployment plan based on comprehensive research

## Key Findings from Research

**Critical Blocker**: Kafka consumer lag of 44,952 messages
- Indexing service stuck in infinite retry loop processing old/invalid messages
- 1,690 valid records in database, all `indexingStatus: NOT_STARTED`
- Zero records indexed
- Consumer offset: 46,458, Log-end offset: 91,410

**Root Cause**: Consumer processing messages for non-existent records from previous test runs

**Solution**: Reset Kafka consumer offset to latest (skip old messages)

## Deployment Plan Overview

### Recommended Path (Fastest - 55-85 minutes)

**Execute**: Phases 0, 3, 4, 5, 6A, 7, 8
**Skip**: Phases 1, 2, 9 (infrastructure healthy, data valid, buffer available)

| Phase | Duration | Description | Critical |
|-------|----------|-------------|----------|
| 0 | 5 min | Pre-deployment prep | ⚠️ |
| **3** | **5 min** | **Kafka offset reset** | **🔥 BLOCKER FIX** |
| 4 | 5 min | UI account setup | |
| 5 | 5 min | Connector configuration | |
| 6A | 2 min | Verify existing records | |
| **7** | **30-60 min** | **Monitor indexing to 100%** | **⏱️ LONGEST** |
| 8 | 10 min | Q&A testing | ⚠️ |
| **Total** | **62-92 min** | | |

### Alternative: Full Path (if clean start needed - 95-125 minutes)

**Execute**: All phases 0-9
**Use when**: Data corruption, fresh start required, or explicitly requested

### Critical Command (Phase 3)

Reset Kafka consumer offset to unblock indexing:

```bash
docker exec kafka-1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group records_consumer_group \
  --reset-offsets \
  --topic record-events \
  --to-latest \
  --execute
```

## Decision Matrix

| Decision | Recommendation | Reason |
|----------|----------------|--------|
| Database clean? | **Skip** ✅ | Data is valid, saves 10 min |
| Docker redeploy? | **Skip** ✅ | Services healthy, saves 5 min |
| Kafka offset | **to-latest** ✅ | Skip old messages, unblock immediately |
| Use existing records? | **Yes** ✅ | 1,690 valid records ready |

## Demo-Ready Criteria

- ✅ 1,690 records indexed (100%)
- ✅ 5,000-10,000 chunks created
- ✅ 5,000-10,000 vectors in Qdrant
- ✅ Kafka consumer lag = 0
- ✅ Q&A returns relevant results with citations
- ✅ Response time < 5 seconds
- ✅ All services healthy

## Timeline

- **Demo**: 10AM PST (~7-8 hours from plan creation)
- **Research**: Complete (1.5 hours)
- **Plan**: Created (this document)
- **Execution**: 55-85 minutes needed
- **Buffer**: 5+ hours for testing and contingency

## Key Success Factors

1. **Phase 3 must succeed**: Kafka offset reset resolves critical blocker
2. **Phase 7 must complete**: All 1,690 records indexed to 100%
3. **Phase 8 must pass**: Q&A functionality validated with real queries

## Risk Mitigation

- **If indexing stalls**: Restart indexing service, check logs, verify Kafka connectivity
- **If Q&A fails**: Pre-test queries documented, backup questions ready
- **If service crashes**: Health check commands provided, restart procedures documented

## Quick Health Check

```bash
# All-in-one verification
docker ps --format "table {{.Names}}\t{{.Status}}" && \
echo "\n=== Database Records ===" && \
docker exec postgres-1 psql -U postgres -d pipeshub -c "SELECT indexing_status, COUNT(*) FROM records GROUP BY indexing_status;" && \
echo "\n=== Kafka Consumer ===" && \
docker exec kafka-1 kafka-consumer-groups --bootstrap-server localhost:9092 --group records_consumer_group --describe
```

## Phase Details

**Phase 0**: Pre-deployment prep (5 min)
- Review research findings
- Check Docker services status
- Verify database connectivity
- Validate current state

**Phase 1**: Database clean (OPTIONAL - 10 min)
- ⚠️ RECOMMENDATION: SKIP - Data is valid
- Only execute if data corruption or fresh start needed

**Phase 2**: Docker deployment (OPTIONAL - 5 min)
- ⚠️ RECOMMENDATION: SKIP - Services healthy
- Only execute if services down or rebuild needed

**Phase 3**: Kafka offset reset (5 min) 🔥 CRITICAL
- Stop indexing service
- Reset consumer offset to latest
- Restart indexing service
- Verify no retry loops

**Phase 4**: UI account setup (5 min)
- Create demo account
- Verify login
- Document credentials

**Phase 5**: Connector configuration (5 min)
- Configure local filesystem connector
- Save configuration
- Verify in database

**Phase 6A**: Verify existing records (2 min) ✅ RECOMMENDED
- Verify 1,690 existing records
- Check all have NOT_STARTED status
- Proceed to indexing

**Phase 6B**: Fresh sync (10 min)
- Only if Phase 1 executed
- Trigger connector sync
- Monitor record creation

**Phase 7**: Monitor indexing (30-60 min) ⏱️ LONGEST
- Trigger indexing for all records
- Monitor progress every 5 minutes
- Verify chunks and vectors created
- Target: 100% completion

**Phase 8**: Q&A testing (10 min)
- Test basic queries
- Test specific content queries
- Test semantic search
- Verify citations and response time

**Phase 9**: Demo rehearsal (OPTIONAL - 10 min)
- Create demo script
- Rehearse flow
- Prepare backup scenarios

## Files

- **Full plan**: `demo-prep-plan.md` (comprehensive 9-phase guide with exact commands)
- **This summary**: `SUMMARY.md` (executive overview)

## Next Steps

1. Execute Phase 0 to validate current state
2. Execute Phase 3 to resolve critical blocker
3. Monitor Phase 7 indexing progress (longest operation)
4. Validate Phase 8 Q&A functionality
5. Declare demo-ready or address remaining issues

---

**Status**: Plan complete, ready for execution
**Confidence**: High (based on thorough research and tested procedures)
**Recommendation**: Execute recommended path (phases 0, 3, 4, 5, 6A, 7, 8) immediately
