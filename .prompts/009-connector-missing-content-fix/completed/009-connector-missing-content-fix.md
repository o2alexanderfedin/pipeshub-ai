# Do: Implement Local Filesystem Connector Content Extraction Fix

## Objective

Implement the content extraction fix for Local Filesystem connector based on the detailed plan from planning phase.

Modify connector code to properly extract and store file content, extension, filePath, and fileSize for all records.

## Context

### Plan Foundation
Read and execute the plan: @.prompts/008-connector-missing-content-plan/connector-missing-content-plan.md

Follow all phases, implementation steps, and error handling strategies defined in the plan.

### Current Implementation State
Before starting, verify:
- Research completed and root cause confirmed
- Plan approved and phases defined
- Testing strategy agreed upon
- Migration approach decided

## Requirements

### Phase 0: Pre-Implementation Validation

Before writing any code:

1. **Verify Root Cause**
   - Re-read research findings
   - Confirm file:line references still accurate
   - Check no code changes since research

2. **Review Plan**
   - Understand all phases
   - Identify dependencies between phases
   - Note error handling requirements

3. **Setup Testing**
   - Prepare test files (various types: .ts, .md, .json, .py)
   - Create test directory structure
   - Setup validation queries

### Phase 1-N: Execute Implementation Phases

For each phase defined in the plan:

1. **Read Current Code**
   - Read all files to be modified
   - Understand existing logic
   - Identify insertion points

2. **Implement Changes**
   - Add new functions/methods as specified
   - Modify existing code as planned
   - Follow plan's file:line guidance
   - Maintain code style consistency

3. **Add Error Handling**
   - Implement try/except as designed
   - Add logging statements
   - Handle edge cases from plan

4. **Add Tests**
   - Create unit tests for new functions
   - Add integration tests for flow
   - Follow testing strategy from plan

5. **Verify Phase**
   - Run tests for this phase
   - Check logs for expected behavior
   - Query database to confirm changes
   - Fix any issues before next phase

### Code Quality Requirements

**Type Safety:**
- Add type hints to all new functions
- Use Optional[str] for nullable returns
- Define TypedDict or dataclass for record data

**Error Handling:**
- Never silently fail
- Log all errors with context
- Return meaningful error messages
- Use result types (success/failure)

**Logging:**
- INFO: Normal operations (file processed, record created)
- WARNING: Recoverable errors (file too large, skipped)
- ERROR: Failures (permission denied, db write failed)

**Documentation:**
- Docstrings for all new functions
- Inline comments for complex logic
- Update module-level docs if needed

### Testing Requirements

After each phase, run:

1. **Unit Tests**
   ```bash
   pytest backend/python/tests/connectors/sources/local_filesystem/
   ```

2. **Integration Test**
   - Place test file in watch directory
   - Monitor logs for processing
   - Query database for record
   - Verify all fields populated

3. **Validation Queries**
   ```javascript
   // Check record has content
   db._query(`
     FOR doc IN records
       FILTER doc.recordName == "test-file.ts"
       RETURN {
         name: doc.recordName,
         hasContent: doc.content != null,
         hasExtension: doc.extension != null,
         hasPath: doc.filePath != null,
         hasSize: doc.fileSize != null
       }
   `);
   ```

### Migration Execution

After code changes deployed and tested:

1. **Backup Current State**
   ```javascript
   // Export current records
   db._query(`
     FOR doc IN records
       FILTER doc.orgId == "6928ff5506880ac843ef5a3c"
       FILTER doc.connectorName == "LOCAL_FILESYSTEM"
       RETURN doc
   `).toArray();
   // Save to file
   ```

2. **Execute Migration**
   Follow migration plan from planning phase:
   - Delete records with null content OR
   - Update in place by reprocessing OR
   - Background job to backfill

3. **Verify Migration**
   ```javascript
   // Count records with/without content
   db._query(`
     FOR doc IN records
       FILTER doc.orgId == "6928ff5506880ac843ef5a3c"
       FILTER doc.connectorName == "LOCAL_FILESYSTEM"
       COLLECT hasContent = (doc.content != null) WITH COUNT INTO count
       RETURN {hasContent, count}
   `);
   ```

### Deployment Steps

1. **Prepare Environment**
   - Ensure Docker volumes mounted correctly
   - Check file permissions
   - Verify configuration in etcd

2. **Deploy Code**
   ```bash
   docker-compose down pipeshub-ai
   docker-compose up -d pipeshub-ai
   ```

3. **Monitor Startup**
   ```bash
   docker logs -f pipeshub-ai | grep -i "local\|filesystem\|connector"
   ```

4. **Trigger Sync**
   - Use UI sync button OR
   - Call API endpoint OR
   - Wait for scheduled sync

5. **Validate Results**
   - Check logs for content extraction
   - Query database for populated fields
   - Test chat search functionality

### Rollback Procedure

If deployment fails:

1. **Revert Code**
   ```bash
   git revert <commit-hash>
   docker-compose down pipeshub-ai
   docker-compose up -d pipeshub-ai
   ```

2. **Restore Data** (if migration ran)
   - Re-import backup records
   - Verify count matches pre-deployment

3. **Verify Rollback**
   - Check service starts
   - Confirm no errors in logs
   - Test basic connector functionality

## Output Specification

### Code Changes

Write all modifications to appropriate files:
- `backend/python/app/connectors/sources/local_filesystem/connector.py`
- `backend/python/app/connectors/sources/local_filesystem/watcher.py` (if needed)
- `backend/python/app/connectors/core/base/data_processor/data_source_entities_processor.py` (if needed)
- Any other files identified in plan

### Tests

Create test files:
- `backend/python/tests/connectors/sources/local_filesystem/test_content_extraction.py`
- Additional test files as needed

### Documentation

Update if needed:
- README for connector
- Configuration documentation
- Troubleshooting guide

### No Plan File Output

Implementation prompts (Do) do NOT create output `.md` files. The code changes are the output.

## Create SUMMARY.md

Write: `.prompts/009-connector-missing-content-fix/SUMMARY.md`

### Structure

```markdown
# Connector Missing Content Fix Implementation

**One-liner:** [Substantive description - e.g., "Content extraction implemented in connector.py with read_file_content() - all 4 fields now populated"]

## Version
v1

## Files Created/Modified
- backend/python/app/connectors/sources/local_filesystem/connector.py (modified: +120 lines)
- backend/python/app/connectors/core/base/data_processor/data_source_entities_processor.py (modified: +15 lines)
- backend/python/tests/connectors/sources/local_filesystem/test_content_extraction.py (created)
- [List all changes]

## Key Changes
- Added read_file_content() method with encoding detection
- Modified process_file() to extract metadata
- Updated record creation to include content field
- Implemented size limit check (10MB default)

## Migration Status
- [700+ existing records deleted and resynced | Updated in place | Pending]
- [Number of records now with content]

## Validation Results
- ✅ Unit tests pass (15/15)
- ✅ Integration test: Sample files processed correctly
- ✅ Database query: All new records have content
- ✅ Chat search: Returns source code results
- [List validation outcomes]

## Decisions Needed
- None | [User approval for production deployment] | [Other]

## Blockers
- None | [Issues preventing completion]

## Next Step
Execute connector-missing-content-test.md for comprehensive testing
```

## Success Criteria

- All phases from plan implemented
- Code changes follow plan specifications
- Unit tests created and passing
- Integration test successful
- Database records have all 4 fields populated
- Chat source code search functional
- Migration completed successfully
- No regressions in existing functionality
- SUMMARY.md created with file changes listed
- Ready for comprehensive testing phase

## Execution Notes

**TDD Approach:**
- Write tests first when possible
- Implement minimal code to pass
- Refactor for quality

**Incremental Deployment:**
- Deploy phase by phase if possible
- Validate each phase before next
- Keep working state after each phase

**Communication:**
- Log progress clearly
- Report issues immediately
- Update SUMMARY.md as you go
