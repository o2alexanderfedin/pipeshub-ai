# Test: Verify Local Filesystem Connector Content Extraction Fix

## Objective

Comprehensive testing of content extraction fix to ensure:
- All 4 fields populated correctly (content, extension, filePath, fileSize)
- Various file types handled properly
- Error scenarios handled gracefully
- Chat source code search functional
- No performance degradation
- No regressions in existing functionality

## Context

### Implementation Foundation
Implementation completed in: @.prompts/009-connector-missing-content-fix/

Read SUMMARY.md to understand what was implemented and where.

### Testing Scope
- Unit tests (already run during implementation)
- Integration tests (connector → database)
- End-to-end tests (filesystem → chat search)
- Performance tests (processing time, resource usage)
- Regression tests (organization ID, record groups, sync)
- Edge case tests (large files, encoding, permissions)

## Requirements

### Phase 1: Pre-Test Setup

1. **Prepare Test Environment**
   - Create test directory with diverse file types
   - Include edge cases (large files, non-UTF8, binary)
   - Setup monitoring (logs, metrics)

2. **Baseline Capture**
   ```javascript
   // Count records before test
   db._query(`
     FOR doc IN records
       FILTER doc.orgId == "6928ff5506880ac843ef5a3c"
       FILTER doc.connectorName == "LOCAL_FILESYSTEM"
       COLLECT WITH COUNT INTO count
       RETURN count
   `);
   ```

3. **Test File Catalog**
   Create files for testing:
   ```
   test-files/
   ├── source-code/
   │   ├── app.ts          (TypeScript)
   │   ├── config.json     (JSON)
   │   ├── utils.py        (Python)
   │   └── styles.css      (CSS)
   ├── documents/
   │   ├── README.md       (Markdown)
   │   ├── notes.txt       (Plain text)
   │   └── design.yaml     (YAML)
   ├── edge-cases/
   │   ├── large-file.md   (>10MB if limit exists)
   │   ├── non-utf8.txt    (Latin-1 encoded)
   │   ├── binary.pdf      (Binary file)
   │   └── empty.txt       (0 bytes)
   └── special/
       ├── .hidden.ts      (Hidden file)
       ├── file with spaces.md
       └── symlink.ts      (Symlink to app.ts)
   ```

### Phase 2: Functional Testing

#### Test 1: Basic Content Extraction

**Objective:** Verify content is read and stored correctly

```javascript
// 1. Place test file
// test-files/source-code/hello.ts:
// export function hello() { return "Hello World"; }

// 2. Trigger sync

// 3. Verify record
db._query(`
  FOR doc IN records
    FILTER doc.recordName == "hello.ts"
    FILTER doc.orgId == "6928ff5506880ac843ef5a3c"
    RETURN {
      recordName: doc.recordName,
      extension: doc.extension,
      filePath: doc.filePath,
      fileSize: doc.fileSize,
      hasContent: doc.content != null,
      contentPreview: SUBSTRING(doc.content, 0, 50)
    }
`);

// Expected:
// {
//   recordName: "hello.ts",
//   extension: ".ts",
//   filePath: "/data/local-files/test-files/source-code/hello.ts",
//   fileSize: 49,
//   hasContent: true,
//   contentPreview: "export function hello() { return \"Hello World\"; }"
// }
```

**Pass Criteria:**
- ✅ All 4 fields populated
- ✅ Content matches file exactly
- ✅ Extension includes dot (.ts)
- ✅ FilePath is absolute
- ✅ FileSize is accurate

#### Test 2: Multiple File Types

**Objective:** Verify all supported file types processed

For each file type (ts, md, json, py, yaml, txt, css, etc.):
1. Create test file
2. Trigger sync
3. Verify record created with content
4. Check content accuracy

**Pass Criteria:**
- ✅ All file types processed
- ✅ Content extracted correctly for each
- ✅ MIME types handled properly

#### Test 3: Large File Handling

**Objective:** Verify size limit enforced

```javascript
// 1. Create file larger than limit (e.g., 15MB if limit is 10MB)

// 2. Trigger sync

// 3. Check record
db._query(`
  FOR doc IN records
    FILTER doc.recordName == "large-file.md"
    RETURN {
      recordName: doc.recordName,
      indexingStatus: doc.indexingStatus,
      hasContent: doc.content != null,
      errorMessage: doc.errorMessage
    }
`);

// Expected: Skipped or marked as failed with reason
```

**Pass Criteria:**
- ✅ File not processed or marked as failed
- ✅ Error logged with reason (file too large)
- ✅ Other files still processed normally

#### Test 4: Encoding Detection

**Objective:** Verify non-UTF8 files handled

```javascript
// 1. Create Latin-1 encoded file

// 2. Trigger sync

// 3. Verify content converted or error handled gracefully
```

**Pass Criteria:**
- ✅ Content extracted (converted to UTF-8) OR
- ✅ Skipped with clear error message
- ✅ No crashes or silent failures

#### Test 5: Error Scenarios

Test each error condition:

**Permission Denied:**
1. Create file, remove read permission
2. Trigger sync
3. Verify: Logged as warning, record marked failed

**File Deleted During Sync:**
1. Connector discovers file
2. Delete file before content read
3. Verify: Handled gracefully, no crash

**Corrupted File:**
1. Create file with inconsistent encoding
2. Trigger sync
3. Verify: Error handled, logged clearly

**Pass Criteria:**
- ✅ All errors caught and logged
- ✅ No silent failures
- ✅ Connector continues processing other files

### Phase 3: Integration Testing

#### Test 6: Full Directory Sync

**Objective:** Verify bulk processing works

1. Place 50+ files in test directory
2. Trigger full sync
3. Monitor logs for errors
4. Query database for all records

```javascript
db._query(`
  FOR doc IN records
    FILTER doc.orgId == "6928ff5506880ac843ef5a3c"
    FILTER doc.connectorName == "LOCAL_FILESYSTEM"
    FILTER doc.createdAtTimestamp > ${testStartTime}
    COLLECT
      hasContent = (doc.content != null),
      hasExtension = (doc.extension != null),
      hasPath = (doc.filePath != null),
      hasSize = (doc.fileSize != null)
    WITH COUNT INTO count
    RETURN {hasContent, hasExtension, hasPath, hasSize, count}
`);
```

**Pass Criteria:**
- ✅ All files processed
- ✅ 100% have content (or explicit failure)
- ✅ All metadata fields populated
- ✅ Processing time reasonable (<5s per file)

#### Test 7: Incremental Sync

**Objective:** Verify only new/modified files processed

1. Sync initial directory
2. Add new file
3. Modify existing file
4. Trigger sync
5. Verify only 2 records created/updated

**Pass Criteria:**
- ✅ New file creates new record
- ✅ Modified file updates record
- ✅ Unchanged files not reprocessed

#### Test 8: Record Group Association

**Objective:** Verify directory structure preserved

```javascript
// Verify hierarchical relationships
db._query(`
  FOR doc IN records
    FILTER doc.recordName == "app.ts"
    LET group = FIRST(
      FOR g IN recordGroups
        FILTER g._key == doc.recordGroupId
        RETURN g
    )
    RETURN {
      file: doc.recordName,
      group: group.groupName,
      path: doc.filePath
    }
`);
```

**Pass Criteria:**
- ✅ Records linked to correct groups
- ✅ Directory hierarchy maintained
- ✅ Belongs_to edges created properly

### Phase 4: End-to-End Testing

#### Test 9: Chat Source Code Search

**Objective:** Verify chat can find and analyze code

1. Ensure test files synced with content
2. Open PipesHub chat UI
3. Ask: "Show me TypeScript files with export functions"
4. Verify: Returns results from test files

**Pass Criteria:**
- ✅ Chat returns source code results
- ✅ Code snippets displayed correctly
- ✅ Citations link to correct files

#### Test 10: Semantic Search

**Objective:** Verify embeddings generated and searchable

1. Query Qdrant for vectors:
   ```bash
   curl -X POST http://localhost:6333/collections/records/points/search \
     -H "Content-Type: application/json" \
     -d '{
       "vector": [...],  // Test embedding
       "limit": 5,
       "filter": {
         "must": [
           {"key": "recordName", "match": {"value": "app.ts"}}
         ]
       }
     }'
   ```

2. Verify: Vector exists for test files

**Pass Criteria:**
- ✅ Embeddings generated for content
- ✅ Semantic search returns relevant results
- ✅ Vector database synchronized

#### Test 11: Knowledge Base Stats

**Objective:** Verify UI shows correct counts

1. Navigate to connector settings
2. Check stats display
3. Verify counts match database

**Pass Criteria:**
- ✅ Stats show correct record count
- ✅ Indexed count matches completed records
- ✅ Failed count shows errors if any

### Phase 5: Performance Testing

#### Test 12: Processing Speed

**Objective:** Measure file processing performance

```bash
# Monitor sync of 100 files
time_start=$(date +%s)
# Trigger sync
time_end=$(date +%s)
elapsed=$((time_end - time_start))
echo "Processed 100 files in ${elapsed}s"
```

**Pass Criteria:**
- ✅ Average < 1s per file
- ✅ No memory leaks
- ✅ CPU usage reasonable

#### Test 13: Database Impact

**Objective:** Verify database performance acceptable

```javascript
// Check document sizes
db._query(`
  FOR doc IN records
    FILTER doc.orgId == "6928ff5506880ac843ef5a3c"
    FILTER doc.connectorName == "LOCAL_FILESYSTEM"
    COLLECT WITH COUNT INTO count
    AGGREGATE avgSize = AVG(LENGTH(doc.content)), maxSize = MAX(LENGTH(doc.content))
    RETURN {count, avgSize, maxSize}
`);
```

**Pass Criteria:**
- ✅ Average document size reasonable
- ✅ Database queries performant
- ✅ No timeout errors

### Phase 6: Regression Testing

#### Test 14: Organization Isolation

**Objective:** Verify org ID fix still working

```javascript
// Verify no records for old org
db._query(`
  FOR doc IN records
    FILTER doc.orgId == "692029575c9fa18a5704d0b7"
    FILTER doc.connectorName == "LOCAL_FILESYSTEM"
    COLLECT WITH COUNT INTO count
    RETURN count
`);
// Expected: 0

// Verify all records for correct org
db._query(`
  FOR doc IN records
    FILTER doc.orgId == "6928ff5506880ac843ef5a3c"
    FILTER doc.connectorName == "LOCAL_FILESYSTEM"
    FILTER doc.createdAtTimestamp > ${testStartTime}
    COLLECT WITH COUNT INTO count
    RETURN count
`);
// Expected: > 0
```

**Pass Criteria:**
- ✅ No records for inactive org
- ✅ All records for correct org

#### Test 15: Connector Restart

**Objective:** Verify connector survives restart

1. Restart Docker container
2. Check logs for proper initialization
3. Trigger sync
4. Verify functionality maintained

**Pass Criteria:**
- ✅ Connector initializes correctly
- ✅ No errors in startup logs
- ✅ Sync works after restart

#### Test 16: Edge Cases

**Objective:** Verify special file handling

- Hidden files (.gitignore)
- Files with spaces (file name.ts)
- Symlinks (if supported)
- Empty files (0 bytes)
- Very long filenames

**Pass Criteria:**
- ✅ All handled gracefully
- ✅ Clear behavior documented

### Phase 7: Migration Validation

#### Test 17: Existing Records Updated

**Objective:** Verify 700+ old records now have content

```javascript
// Count records updated vs still null
db._query(`
  FOR doc IN records
    FILTER doc.orgId == "6928ff5506880ac843ef5a3c"
    FILTER doc.connectorName == "LOCAL_FILESYSTEM"
    COLLECT hasContent = (doc.content != null) WITH COUNT INTO count
    RETURN {hasContent, count}
`);

// Expected:
// {hasContent: true, count: 700+}
// {hasContent: false, count: 0} (or only failed files)
```

**Pass Criteria:**
- ✅ 100% of records have content OR explicit failure
- ✅ No orphaned null records

## Output Specification

### Test Report

Write: `.prompts/010-connector-missing-content-test/connector-missing-content-test-report.md`

```xml
<test_report>
  <metadata>
    <test_date>YYYY-MM-DD HH:MM</test_date>
    <tester>Claude Agent</tester>
    <environment>Development | Staging | Production</environment>
  </metadata>

  <executive_summary>
    <overall_status>PASS | FAIL | PARTIAL</overall_status>
    <tests_run>17</tests_run>
    <tests_passed>16</tests_passed>
    <tests_failed>1</tests_failed>
    <critical_issues>0</critical_issues>
  </executive_summary>

  <test_results>
    <test id="1" name="Basic Content Extraction">
      <status>PASS | FAIL</status>
      <details>
        Sample file created, synced, verified in database.
        All 4 fields populated correctly.
      </details>
      <evidence>
        Query results, log excerpts
      </evidence>
      <issues>None | [Describe problems]</issues>
    </test>

    <!-- Repeat for all 17 tests -->
  </test_results>

  <performance_metrics>
    <metric name="Average processing time per file">0.8s</metric>
    <metric name="Total files processed">150</metric>
    <metric name="Database query response time">45ms</metric>
    <metric name="Memory usage">512MB</metric>
  </performance_metrics>

  <issues_found>
    <issue severity="critical">
      <description>Large files crash connector</description>
      <affected_tests>Test 3</affected_tests>
      <recommended_action>Fix size limit check</recommended_action>
    </issue>

    <!-- List all issues -->
  </issues_found>

  <regression_check>
    <status>PASS</status>
    <details>
      - Organization ID isolation: PASS
      - Record groups: PASS
      - Connector restart: PASS
    </details>
  </regression_check>

  <chat_functionality>
    <source_code_search>PASS | FAIL</source_code_search>
    <semantic_search>PASS | FAIL</semantic_search>
    <details>
      Chat successfully returns TypeScript files.
      Semantic search finds relevant code snippets.
    </details>
  </chat_functionality>

  <recommendations>
    <recommendation priority="high">
      Production deployment approved - all critical tests pass
    </recommendation>

    <recommendation priority="medium">
      Monitor performance with larger datasets
    </recommendation>
  </recommendations>

  <next_steps>
    <step>Fix identified issues if any</step>
    <step>Deploy to production</step>
    <step>Monitor for 24 hours</step>
    <step>Document lessons learned</step>
  </next_steps>
</test_report>
```

## Create SUMMARY.md

Write: `.prompts/010-connector-missing-content-test/SUMMARY.md`

```markdown
# Connector Missing Content Testing

**One-liner:** [Substantive description - e.g., "17 tests executed: 16 passed, 1 failed (large file handling) - chat search functional"]

## Version
v1

## Test Results
- ✅ Content extraction: All file types working
- ✅ Metadata fields: extension, filePath, fileSize populated
- ✅ Error handling: Graceful failures logged
- ✅ Chat search: Source code results returned
- ✅ Performance: <1s per file average
- ❌ Large files: Size limit check needs fix
- ✅ Regression: No issues found

## Decisions Needed
- Approve production deployment (if all critical tests pass)
- Fix non-critical issues (if any)

## Blockers
- None | [Critical test failures preventing deployment]

## Next Step
[Deploy to production | Fix failing tests and retest | Document and close]
```

## Success Criteria

- All 17 tests executed
- Critical tests passing (content extraction, chat search)
- Performance metrics acceptable
- No regressions detected
- Issues documented with severity
- Recommendations clear (deploy vs fix first)
- Test report comprehensive and evidence-based
- SUMMARY.md created with pass/fail counts
- Decision on production deployment

## Notes

**Testing Philosophy:**
- Verify happy path works
- Test edge cases thoroughly
- Validate error handling
- Measure performance
- Check for regressions

**Evidence Collection:**
- Screenshots of chat search results
- Database query results
- Log excerpts showing processing
- Performance metrics

**Continuous Testing:**
- If issues found, fix and retest
- Document all findings
- Track metrics over time
