# Content Extraction Validation Plan

**One-liner:** Complete 4-phase execution plan (3.5-5hr) to fix connector path mismatch, validate content extraction across 12 test files, execute 9 critical tests, and achieve "done-done-done" validation state

## Version
v1

## Plan Status
READY_FOR_EXECUTION - All tasks defined, commands documented, success criteria established

## Objective

Fix the configuration path mismatch discovered in research (connector syncing `/data/local-files/` instead of `/data/pipeshub/test-files/`), validate content extraction functionality works correctly, execute comprehensive testing, and achieve fully operational state.

## Phase Overview

| Phase | Name | Objective | Time | Success Metric |
|-------|------|-----------|------|----------------|
| 0 | Pre-Flight | Environment verification, baseline capture | 15-20 min | All containers up, 1673 records baseline |
| 1 | Configuration Fix | Update sync path to test-files | 30-45 min | Logs show "Found 12 files to sync" |
| 2 | Initial Validation | Verify content extraction working | 20-30 min | 12/12 files have content in DB |
| 3 | Comprehensive Testing | Execute 9 critical tests | 90-120 min | 8/9 tests passing |
| 4 | Final Verification | End-to-end validation | 30-45 min | Validation report complete |

**Total Time**: 3.5-5.0 hours (including troubleshooting buffer)

## Critical Findings from Research

**Based on**: `.prompts/001-content-extraction-validation-research/`

- **BLOCKER IDENTIFIED**: Connector configured to sync `/data/local-files/` (empty) instead of `/data/pipeshub/test-files/` (12 test files)
- **Code Status**: Content extraction deployed correctly (line 396, `_read_file_content()`)
- **Configuration**: Content extraction enabled (`enabled=True, max_size_mb=10`)
- **Current State**: 1,673 records, 0% have content (expected - syncing wrong path)
- **Test Files Ready**: 12 files, 7 types, ~130KB at `/data/pipeshub/test-files/`
- **Database**: ArangoDB "es" database, "records" collection, org ID `6928ff5506880ac843ef5a3c`

## Key Tasks by Phase

### Phase 0: Pre-Flight (15-20 min)
1. Verify all 8 containers running
2. Confirm 12 test files exist at correct path
3. Capture baseline (1,673 records, 0% content)
4. Verify current wrong sync path (/data/local-files)
5. Confirm content extraction code deployed (line 396)

**Gate**: All 5 tasks complete before Phase 1

---

### Phase 1: Configuration Fix (30-45 min)
1. **Identify config method** (10-15 min)
   - Investigate: env vars, config file, etcd, database
   - Choose fastest/safest method

2. **Update configuration** (10-15 min)
   - Change: `watch_path` from `/data/local-files` to `/data/pipeshub/test-files`
   - Method depends on Task 1.1 findings

3. **Restart connector** (2-3 min)
   - `docker compose restart pipeshub-ai`

4. **Verify config change** (5 min)
   - Logs show new path: `/data/pipeshub/test-files`

5. **Trigger initial sync** (5-10 min)
   - Wait for auto-sync (5 min intervals) or force restart
   - Verify: "Found 12 files to sync"
   - Verify: "Content loaded:" messages for each file

**Gate**: Must see "Found 12 files to sync" and "Content loaded:" logs before Phase 2

---

### Phase 2: Initial Validation (20-30 min)
1. **Query new records** (5 min)
   - Verify 12 records created with test-files path

2. **Verify content populated** (5 min)
   - All 12 have `block_containers != null`
   - All have `blocks[0].data` with content

3. **Verify all fields** (5 min)
   - extension, path, sizeInBytes, mimeType all populated

4. **Test multiple file types** (5 min)
   - .ts, .json, .py, .css, .md, .txt all processed

5. **Verify Unicode handling** (5 min)
   - unicode.txt content preserved correctly

**Gate**: 11/12 files minimum with content (empty.txt can be empty)

---

### Phase 3: Comprehensive Testing (90-120 min)

**9 Critical Tests** from 17-test suite:

1. **Large file handling** (5 min)
   - large-file.md (127KB) processed correctly

2. **Edge cases** (5 min)
   - empty.txt, .hidden.ts, "file with spaces.md" handled

3. **Directory structure** (5 min)
   - Paths preserve hierarchy: "source-code/app.ts"

4. **Database impact** (5 min)
   - Avg/max/min content sizes measured

5. **Organization isolation** (5 min)
   - All test-files have correct orgId

6. **Processing speed** (5 min)
   - <60 seconds for 12 files

7. **Content quality** (10 min)
   - DB content matches source files exactly

8. **Restart persistence** (5 min)
   - Config survives connector restart

9. **Migration validation** (5 min)
   - New records (12) vs old records (1673) distinguished

**Gate**: 8/9 tests passing minimum

---

### Phase 4: Final Verification (30-45 min)
1. **Complete content statistics** (5 min)
   - Final count: 1,685 records (1,673 old + 12 new)
   - Content: 12 with content (0.71%), 1,673 without (99.29%)

2. **File type distribution** (5 min)
   - 7 extensions represented

3. **Indexing status** (5 min)
   - All have indexingStatus and extractionStatus

4. **Sample full record** (10 min)
   - Manual review of complete config.json record
   - Verify all fields correct

5. **Baseline comparison** (5 min)
   - Before: 0% content, wrong path
   - After: 12 files with content, correct path

6. **Log analysis** (5 min)
   - 12 "Content loaded:" messages
   - 0 errors

7. **Create validation report** (10 min)
   - Document all results, evidence, metrics

**Gate**: All 7 tasks complete, validation report created

---

## Success Criteria (Overall)

### Configuration Fix
- [ ] Connector syncing `/data/pipeshub/test-files/`
- [ ] Logs confirm new path
- [ ] Sync finding 12 files (not 0)

### Content Extraction
- [ ] All 12 test files have DB records
- [ ] All records have `block_containers` populated
- [ ] Content matches source files
- [ ] Unicode preserved correctly

### Comprehensive Testing
- [ ] 8/9 critical tests passing
- [ ] Processing speed <60s for 12 files
- [ ] Edge cases handled
- [ ] Config persists across restarts

### Final Verification
- [ ] Statistics match expectations (12 new, 1673 old)
- [ ] No errors in logs
- [ ] All fields populated correctly
- [ ] Validation report complete

---

## Key Decision Points

### Decision 1: Configuration Method (Phase 1, Task 1.1)
**Options**: Environment variables | Config file | etcd | Database/UI

**Framework**:
- Env vars → If found and simple
- Config file → If found and not overridden
- etcd → If accessible and encryption manageable
- Database/UI → If API available

**Impact**: Determines how Task 1.2 executed

---

### Decision 2: Acceptable Content Percentage (Phase 2, Task 2.2)
**Options**: 100% (12/12) | 95%+ (11/12) | 90%+ (10/12) | <90%

**Framework**:
- 12/12 → Proceed immediately
- 11/12 → Investigate failed file, proceed if edge case
- 10/12 → Investigate pattern before proceeding
- <10/12 → STOP, major issue

**Impact**: Whether to proceed to Phase 3 or troubleshoot

---

### Decision 3: Old Records Migration (Phase 4)
**Options**: Leave as-is | Delete old records | Re-sync old path | Defer

**Framework**:
- Leave as-is → Validation focused, no production impact
- Delete → Clean state, old files don't exist
- Re-sync → Old files exist and should have content
- Defer → Out of scope for validation

**Current Plan**: Leave as-is (validation focused)

**Impact**: Database state and total record count

---

## Risk Assessment

### High Risk
1. **Configuration change breaks connector**
   - Mitigation: Backup before change
   - Rollback: 5 minutes to restore

2. **Sync path wrong causes errors**
   - Mitigation: Verify path exists first
   - Detection: "Path does not exist" in logs

### Medium Risk
3. **Content extraction OOM**
   - Mitigation: 10MB size limit enforced
   - Detection: Container crash/restart

4. **Encoding issues**
   - Mitigation: chardet with UTF-8 fallback
   - Detection: "No content for" warnings

### Low Risk
5. **Database write performance**
   - Impact: Sync takes longer
   - Mitigation: Only 12 files, small volume

6. **Query performance**
   - Impact: Queries take longer
   - Mitigation: Queries tested in research

---

## Rollback Plans

### Configuration Rollback
```bash
# Restore backup
cp docker-compose.dev.yml.backup docker-compose.dev.yml

# Restart
docker compose restart pipeshub-ai

# Verify old path
docker logs pipeshub-ai | grep "Starting Local Filesystem full sync"
```

**Time**: 5 minutes

---

### Content Extraction Disable (Emergency)
```bash
# Update config to disable content extraction
# "content_extraction": {"enabled": false}

# Restart
docker compose restart pipeshub-ai
```

**Note**: Reverts to metadata-only mode

---

## Dependencies

### External
- Docker containers running (8 services)
- ArangoDB accessible (localhost:8529)
- Test files exist (`/data/pipeshub/test-files/`)
- Credentials in .env file

### Code
- Content extraction deployed (line 396)
- chardet==5.2.0 installed
- Block model imports working

### Configuration
- Config mechanism accessible
- Permissions to update config
- Ability to restart connector

---

## Evidence to Collect

### Phase 0
- Container status
- Test files list (12 files)
- Baseline stats (1673 records, 0% content)
- Current sync path (wrong)

### Phase 1
- Config before/after
- Restart logs
- New sync path confirmation
- "Found 12 files" log

### Phase 2
- 12 records query results
- Content preview samples
- Field validation
- Unicode sample

### Phase 3
- 9 test query results
- Processing speed logs
- Content quality diffs
- Restart verification

### Phase 4
- Final statistics
- File type distribution
- Full sample record JSON
- Validation report

---

## Testing Strategy

**From Previous Work**: 17 comprehensive tests defined in `.prompts/010-connector-missing-content-test/`

**This Plan**: Execute 9 most critical tests

**Coverage**:
- Functionality: File types, edge cases, content quality
- Performance: Processing speed, database impact
- Reliability: Restart persistence, config survival
- Data Integrity: Org isolation, directory structure
- Migration: Old vs new records

**Excluded Tests** (defer to later):
- Chat UI search (Test 9) - requires UI interaction
- Semantic search (Test 10) - requires Qdrant integration
- Knowledge base stats (Test 11) - requires frontend
- Incremental sync (Test 7) - requires file changes
- Error scenarios (Test 5) - not critical for validation

---

## Post-Validation Actions

### Immediate (After Phase 4)
1. Create summary report (10 min)
2. Communicate results (5 min)

### Short-term (24 hours)
3. Monitor connector stability
4. Decide on old records (keep/migrate/delete)

### Medium-term (1 week)
5. Production deployment plan (if applicable)
6. Performance optimization (if needed)

---

## Quick Reference

### Key Commands

**Container Status**:
```bash
docker compose -f deployment/docker-compose/docker-compose.dev.yml ps
```

**Restart Connector**:
```bash
docker compose -f deployment/docker-compose/docker-compose.dev.yml restart pipeshub-ai
```

**ArangoDB Query**:
```bash
curl -s -u "root:PASSWORD" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/query.json | python3 -m json.tool
```

**List Test Files**:
```bash
docker exec docker-compose-pipeshub-ai-1 \
  find /data/pipeshub/test-files -type f
```

**Check Code Deployed**:
```bash
docker exec docker-compose-pipeshub-ai-1 \
  grep -n "_read_file_content" \
  /app/python/app/connectors/sources/local_filesystem/connector.py
```

---

## Files Created

### Plan Document
- `content-extraction-validation-plan.md` - Full detailed plan (4 phases, all tasks)

### Summary
- `SUMMARY.md` - This file (executive summary, quick reference)

---

## References

### Research Input
- `.prompts/001-content-extraction-validation-research/content-extraction-validation-research.md`
  - Critical finding: Wrong sync path
  - Database schema documented
  - Baseline metrics captured

### Implementation
- `.prompts/009-connector-missing-content-fix/SUMMARY.md`
  - Code implementation complete
  - 14 unit tests passing
  - Ready for deployment testing

### Test Suite
- `.prompts/010-connector-missing-content-test/TEST-COMMANDS.md`
  - 17 tests defined
  - Commands documented
  - Test files created

---

## Confidence Assessment

**Plan Completeness**: COMPLETE
- All phases defined
- All tasks detailed
- All commands documented
- All success criteria established

**Ready for Execution**: YES
- Prerequisites identified
- Dependencies verified
- Rollback plans prepared
- Decision frameworks defined

**Estimated Duration**: 3.5-5.0 hours
- Conservative estimate
- Includes troubleshooting buffer
- Based on task breakdown

**Risk Level**: LOW-MEDIUM
- Configuration change is controlled
- Code already tested (14 unit tests)
- Rollback plans in place
- Testing in dev environment

**Confidence**: HIGH
- Research completed thoroughly
- Implementation validated with unit tests
- Test files already created
- Clear path from current state to validated state

---

## Next Action

Execute Phase 0: Pre-Flight Verification

**First Command**:
```bash
docker compose -f deployment/docker-compose/docker-compose.dev.yml ps
```

**Expected**: All 8 containers running

**Then**: Follow Phase 0 checklist in full plan document

---

**Status**: READY_FOR_EXECUTION
**Owner**: Development team
**Created**: 2025-11-27
**Based on**: Research 001-content-extraction-validation
**Executes**: Content extraction validation workflow
**Delivers**: Fully validated content extraction system with comprehensive test evidence
