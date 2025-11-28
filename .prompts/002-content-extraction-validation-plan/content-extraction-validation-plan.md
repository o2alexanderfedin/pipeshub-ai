# Content Extraction Validation Plan

<metadata>
  <plan_id>002-content-extraction-validation</plan_id>
  <timestamp>2025-11-27T22:00:00Z</timestamp>
  <objective>Fix configuration path mismatch and validate content extraction functionality end-to-end</objective>
  <status>READY_FOR_EXECUTION</status>
  <based_on>001-content-extraction-validation-research</based_on>
  <total_estimated_time>3.5-5.0 hours</total_estimated_time>
  <parallelization_limit>8 cores</parallelization_limit>
</metadata>

## Executive Summary

**Mission**: Fix the connector configuration path mismatch (from `/data/local-files/` to `/data/pipeshub/test-files/`), validate content extraction works correctly across all file types, and achieve "done-done-done" state with comprehensive testing.

**Critical Finding**: Content extraction code is deployed and configured correctly, but NOT executing because the connector syncs an empty directory. This plan provides the complete roadmap from configuration fix through validation to final verification.

**Outcome**: A fully validated content extraction system processing 12 test files with proven functionality across 7 file types, verified through database queries, semantic search, and chat UI integration.

### Plan Overview

| Phase | Objective | Tasks | Time Estimate | Success Criteria |
|-------|-----------|-------|---------------|------------------|
| 0 | Pre-Flight | Environment verification, baseline capture | 15-20 min | All containers running, baseline captured |
| 1 | Configuration Fix | Update connector sync path | 30-45 min | Connector syncing correct directory |
| 2 | Initial Validation | Verify content extraction working | 20-30 min | Test files have content in DB |
| 3 | Comprehensive Testing | Execute 9 critical tests from 17-test suite | 90-120 min | All tests pass with evidence |
| 4 | Final Verification | End-to-end validation and sign-off | 30-45 min | System fully operational |

**Total Time**: 3.5-5.0 hours (including buffer for troubleshooting)

### Key Insights from Research

**From Research Document (.prompts/001-content-extraction-validation-research/)**:
- Code deployed: `_read_file_content()` at line 396 in connector.py
- Configuration: `enabled=True, max_size_mb=10`
- Test files: 12 files at `/data/pipeshub/test-files/` (4 subdirectories)
- Database: 1,673 existing records, 0% have content
- Database name: `es` (not "pipeshub")
- Collection: `records` (lowercase)
- Organization ID: `6928ff5506880ac843ef5a3c`
- **BLOCKER**: Wrong sync path `/data/local-files/` instead of `/data/pipeshub/test-files/`

**From Implementation (.prompts/009-connector-missing-content-fix/)**:
- 14 unit tests passing
- chardet 5.2.0 for encoding detection
- Block structure: `BlockType.TEXT`, `DataFormat.TXT`
- Relative path calculation implemented
- Size limits enforced (default 10MB)

**From Previous Testing (.prompts/010-connector-missing-content-test/)**:
- 17 comprehensive tests defined
- Test files already created (12 files, 7 types, ~130KB)
- Baseline data captured
- Frontend build blocker identified and should be resolved

---

## Phase 0: Pre-Flight Verification

**Objective**: Confirm environment is ready for configuration changes and testing

**Time Estimate**: 15-20 minutes

### Task 0.1: Container Health Check

**Command**:
```bash
docker compose -f deployment/docker-compose/docker-compose.dev.yml ps
```

**Success Criteria**:
- All 8 containers running
- pipeshub-ai container status: "Up"
- ArangoDB accessible (healthy or unhealthy-but-connectable is OK)

**Failure Handling**:
- If containers down: Run `docker compose up -d`
- If persistent failures: Check logs with `docker logs <container>`
- If port conflicts: Stop conflicting services

**Decision Point**: If more than 2 containers failing, investigate root cause before proceeding.

---

### Task 0.2: Verify Test Files Exist

**Command**:
```bash
docker exec docker-compose-pipeshub-ai-1 \
  find /data/pipeshub/test-files -type f -exec ls -lh {} \;
```

**Success Criteria**:
- 12 files found
- 4 subdirectories: documents, edge-cases, source-code, special
- Files have sizes (not all 0 bytes)

**Expected Files**:
```
source-code/app.ts (388 bytes)
source-code/config.json (227 bytes)
source-code/utils.py (693 bytes)
source-code/styles.css (516 bytes)
documents/README.md (539 bytes)
documents/notes.txt (434 bytes)
documents/design.yaml (801 bytes)
edge-cases/empty.txt (0 bytes)
edge-cases/unicode.txt (330 bytes)
edge-cases/large-file.md (~127 KB)
special/.hidden.ts (154 bytes)
special/file with spaces.md (151 bytes)
```

**Failure Handling**:
- If files missing: Re-create using test file creation script from 010-connector-missing-content-test
- If directory doesn't exist: Create `/data/pipeshub/test-files/` and populate

---

### Task 0.3: Capture Current Baseline

**Command**:
```bash
cat > /tmp/baseline_query.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == \"LOCAL_FILESYSTEM\" COLLECT hasContent = (doc.block_containers != null AND LENGTH(doc.block_containers.blocks) > 0) WITH COUNT INTO count RETURN {hasContent, count}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/baseline_query.json | python3 -m json.tool
```

**Success Criteria**:
- Query returns results
- Current state: `{hasContent: false, count: 1673}` (or similar)
- Connection to ArangoDB successful

**Failure Handling**:
- If connection fails: Check ArangoDB container logs
- If wrong password: Update from .env file
- If database "es" not found: Check if database was renamed

**Evidence to Capture**:
```json
{
  "timestamp": "2025-11-27T22:00:00Z",
  "total_records": 1673,
  "records_with_content": 0,
  "records_without_content": 1673,
  "percentage_with_content": 0
}
```

---

### Task 0.4: Verify Current Sync Path

**Command**:
```bash
docker logs docker-compose-pipeshub-ai-1 2>&1 | \
  grep -i "starting local filesystem full sync" | tail -3
```

**Success Criteria**:
- Logs show: "Starting Local Filesystem full sync for: /data/local-files"
- Confirms wrong path (expected finding)

**Expected Output**:
```
2025-11-28 06:07:13,387 - connector_service - INFO - [connector.py:628] - Starting Local Filesystem full sync for: /data/local-files
```

**Decision Point**: If already syncing `/data/pipeshub/test-files/`, skip Phase 1 and proceed to Phase 2.

---

### Task 0.5: Verify Content Extraction Code Deployed

**Command**:
```bash
docker exec docker-compose-pipeshub-ai-1 \
  grep -n "def _read_file_content" \
  /app/python/app/connectors/sources/local_filesystem/connector.py
```

**Success Criteria**:
- Line 396 (or nearby) shows `def _read_file_content`
- Code is deployed in container

**Failure Handling**:
- If not found: Code not deployed, rebuild Docker image
- If old code: Follow deployment steps from 009-connector-missing-content-fix

**Rebuild Command** (if needed):
```bash
cd deployment/docker-compose
docker compose -f docker-compose.dev.yml build pipeshub-ai
docker compose -f docker-compose.dev.yml up -d pipeshub-ai
```

---

### Phase 0 Completion Checklist

- [ ] All containers running
- [ ] Test files verified (12 files in correct location)
- [ ] Baseline captured (1673 records, 0% content)
- [ ] Current sync path confirmed (/data/local-files)
- [ ] Content extraction code deployed (line 396)

**Gate**: All checklist items must be complete before Phase 1.

---

## Phase 1: Configuration Fix

**Objective**: Update connector configuration to sync `/data/pipeshub/test-files/` instead of `/data/local-files/`

**Time Estimate**: 30-45 minutes

**Critical**: This phase resolves the core blocker identified in research.

---

### Task 1.1: Identify Configuration Method

**Research Required**: Determine how to update the connector's sync path configuration.

**Options Investigation**:

**Option A: Docker Compose Environment Variables**
- Location: `deployment/docker-compose/docker-compose.dev.yml`
- Check for: `LOCAL_FILESYSTEM_WATCH_PATH` or similar
- Pros: Fastest, no etcd manipulation needed
- Cons: May not persist across deployments

**Option B: Configuration File in Container**
- Location: `/app/python/config/` or similar
- Check for: JSON/YAML config files
- Pros: Clear, version-controlled
- Cons: May be overridden by etcd

**Option C: Direct etcd Update**
- Key: `/services/connectors/localfilesystem/config/6928ff5506880ac843ef5a3c`
- Pros: Authoritative source
- Cons: Requires encryption/decryption handling

**Option D: Database Configuration Table**
- Collection: Possibly `connectorConfigs` or similar
- Pros: UI-manageable
- Cons: May not exist

**Investigation Commands**:
```bash
# Check docker-compose environment variables
grep -i "watch\|path\|local.*file" deployment/docker-compose/docker-compose.dev.yml

# Check config files in container
docker exec docker-compose-pipeshub-ai-1 find /app/python -name "*.json" -o -name "*.yaml" | grep -i config

# Check etcd for connector config
docker exec docker-compose-etcd-1 etcdctl get --prefix "/services/connectors" 2>/dev/null || echo "etcd access method needed"

# Check for config in database
cat > /tmp/config_check.json << 'EOF'
{
  "query": "FOR col IN collections() FILTER CONTAINS(col.name, 'config') RETURN col.name"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/config_check.json
```

**Time Estimate**: 10-15 minutes

**Decision Framework**:
1. If environment variables found → Use Option A (fastest)
2. Else if config file found → Use Option B (clear)
3. Else if etcd accessible → Use Option C (authoritative)
4. Else → Investigate connector initialization code for config source

---

### Task 1.2: Update Configuration

**This task depends on Task 1.1 findings. Documenting all approaches.**

#### Approach A: Environment Variables (Preferred)

**Steps**:
1. Open `deployment/docker-compose/docker-compose.dev.yml`
2. Find pipeshub-ai service environment section
3. Add or update: `LOCAL_FILESYSTEM_WATCH_PATH=/data/pipeshub/test-files`
4. Save file

**Command**:
```bash
# Backup current config
cp deployment/docker-compose/docker-compose.dev.yml \
   deployment/docker-compose/docker-compose.dev.yml.backup

# Edit file (manual or sed)
# Look for pipeshub-ai service and add under environment:
#   - LOCAL_FILESYSTEM_WATCH_PATH=/data/pipeshub/test-files
```

**Verification**:
```bash
grep -A 10 "pipeshub-ai:" deployment/docker-compose/docker-compose.dev.yml | \
  grep -i "watch\|path"
```

---

#### Approach B: Configuration File

**Steps**:
1. Copy current config from container
2. Update watch_path field
3. Copy updated config back
4. Restart connector

**Commands**:
```bash
# Copy config out
docker cp docker-compose-pipeshub-ai-1:/app/python/config/connector.json \
  /tmp/connector.json.backup

# Edit /tmp/connector.json (manual)
# Update: "watch_path": "/data/pipeshub/test-files"

# Copy config back
docker cp /tmp/connector.json \
  docker-compose-pipeshub-ai-1:/app/python/config/connector.json
```

---

#### Approach C: etcd Direct Update

**Warning**: Requires handling encrypted config values.

**Steps**:
1. Access etcd container
2. Get current config
3. Decrypt (if encrypted)
4. Update watch_path
5. Re-encrypt (if needed)
6. Put updated config

**Commands**:
```bash
# Access etcd
docker exec -it docker-compose-etcd-1 sh

# Get current config
etcdctl get /services/connectors/localfilesystem/config/6928ff5506880ac843ef5a3c

# If encrypted, this is complex - defer to manual method or ask for guidance
```

**Fallback**: If encryption is complex, use connector UI or API to update.

---

### Task 1.3: Restart Connector Service

**Command**:
```bash
docker compose -f deployment/docker-compose/docker-compose.dev.yml restart pipeshub-ai
```

**Time Estimate**: 2-3 minutes

**Success Criteria**:
- Container restarts cleanly
- No crash loops
- Logs show initialization

**Monitor Command**:
```bash
docker logs -f docker-compose-pipeshub-ai-1 | \
  grep -i "local filesystem\|watch\|content extraction"
```

**Expected Output**:
```
2025-11-27 22:15:00,123 - connector_service - INFO - Local Filesystem connector initialized for org 6928ff5506880ac843ef5a3c
2025-11-27 22:15:00,124 - connector_service - INFO - Content extraction: enabled=True, max_size_mb=10
2025-11-27 22:15:00,125 - connector_service - INFO - Starting Local Filesystem full sync for: /data/pipeshub/test-files
```

**Failure Handling**:
- If crash loop: Check logs for error, revert config change
- If old path still showing: Config update didn't work, try different method
- If initialization fails: Check dependencies, permissions

---

### Task 1.4: Verify Configuration Change

**Command**:
```bash
# Check logs for new path
docker logs docker-compose-pipeshub-ai-1 2>&1 | \
  grep "Starting Local Filesystem full sync" | tail -1

# Should show: /data/pipeshub/test-files
```

**Success Criteria**:
- Logs show: "Starting Local Filesystem full sync for: /data/pipeshub/test-files"
- No errors about path not existing

**Evidence to Capture**:
```
Before: Starting Local Filesystem full sync for: /data/local-files
After:  Starting Local Filesystem full sync for: /data/pipeshub/test-files
```

---

### Task 1.5: Trigger Initial Sync

**Wait for Auto-Sync** (occurs every 5 minutes):
```bash
# Watch for sync activity
docker logs -f docker-compose-pipeshub-ai-1 | \
  grep -i "found.*files to sync\|sync completed"
```

**Or Force Sync** (if API endpoint exists):
```bash
# Attempt to trigger via API
curl -X POST http://localhost:8088/api/v1/connectors/local-filesystem/sync \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" 2>/dev/null || echo "API endpoint may not exist"

# If no API, restart triggers sync immediately
docker compose -f deployment/docker-compose/docker-compose.dev.yml restart pipeshub-ai
```

**Success Criteria**:
- Logs show: "Found 12 files to sync" (or similar non-zero number)
- Logs show: "Content loaded: app.ts (388 chars, 388 bytes)" (and other files)
- Logs show: "Local Filesystem full sync completed"

**Expected Duration**: 5-30 seconds for 12 files

**Failure Handling**:
- If "Found 0 files": Path still wrong or files not accessible
- If no "Content loaded" messages: Content extraction not running
- If errors: Check file permissions, encoding issues

---

### Phase 1 Completion Checklist

- [ ] Configuration method identified
- [ ] Configuration updated (watch_path = /data/pipeshub/test-files)
- [ ] Connector service restarted successfully
- [ ] Logs confirm new sync path
- [ ] Initial sync completed (12 files processed)
- [ ] Logs show "Content loaded" messages

**Gate**: Must see "Found 12 files to sync" before Phase 2.

---

## Phase 2: Initial Validation

**Objective**: Confirm content extraction is working for test files

**Time Estimate**: 20-30 minutes

---

### Task 2.1: Query for New Records

**Command**:
```bash
cat > /tmp/new_records.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == \"LOCAL_FILESYSTEM\" AND CONTAINS(doc.externalRecordId, \"test-files\") COLLECT WITH COUNT INTO count RETURN count"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/new_records.json | python3 -m json.tool
```

**Success Criteria**:
- Count = 12 (matching number of test files)

**Failure Handling**:
- If count = 0: Sync didn't create records, check logs
- If count < 12: Some files failed, check which ones
- If count > 12: Unexpected files in directory

---

### Task 2.2: Verify Content Populated

**Command**:
```bash
cat > /tmp/content_check.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == \"LOCAL_FILESYSTEM\" AND CONTAINS(doc.externalRecordId, \"test-files\") RETURN {recordName: doc.recordName, hasBlockContainers: doc.block_containers != null, blockCount: doc.block_containers != null ? LENGTH(doc.block_containers.blocks) : 0, contentPreview: doc.block_containers != null AND LENGTH(doc.block_containers.blocks) > 0 ? SUBSTRING(doc.block_containers.blocks[0].data, 0, 50) : null}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/content_check.json | python3 -m json.tool
```

**Success Criteria**:
- All 12 records have `hasBlockContainers: true`
- All (except empty.txt) have `blockCount: 1`
- Content previews show actual file content
- empty.txt has `blockCount: 1` with empty string content

**Expected Sample Output**:
```json
{
  "recordName": "app.ts",
  "hasBlockContainers": true,
  "blockCount": 1,
  "contentPreview": "import express from 'express';\nimport { Router } f"
}
```

**Failure Handling**:
- If `hasBlockContainers: false`: Content extraction failed, check logs
- If `blockCount: 0`: Block creation failed, code issue
- If `contentPreview: null`: Content not populated, investigate

---

### Task 2.3: Verify All Expected Fields Populated

**Command**:
```bash
cat > /tmp/field_check.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.recordName == \"app.ts\" AND doc.connectorName == \"LOCAL_FILESYSTEM\" RETURN {recordName: doc.recordName, extension: doc.extension, path: doc.path, sizeInBytes: doc.sizeInBytes, mimeType: doc.mimeType, hasContent: doc.block_containers != null AND LENGTH(doc.block_containers.blocks) > 0, contentLength: doc.block_containers != null && doc.block_containers.blocks[0] != null ? LENGTH(doc.block_containers.blocks[0].data) : 0}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/field_check.json | python3 -m json.tool
```

**Success Criteria**:
- `extension`: ".ts" (not null)
- `path`: Contains relative path like "source-code/app.ts"
- `sizeInBytes`: 388 (matches file size)
- `mimeType`: "text/typescript" or "text/plain"
- `hasContent`: true
- `contentLength`: ~388 (matching sizeInBytes)

**Expected Output**:
```json
{
  "recordName": "app.ts",
  "extension": ".ts",
  "path": "source-code/app.ts",
  "sizeInBytes": 388,
  "mimeType": "text/plain",
  "hasContent": true,
  "contentLength": 388
}
```

**Failure Handling**:
- Missing fields: Implementation incomplete
- Null values: Field population logic failed
- Wrong values: Path calculation or extraction error

---

### Task 2.4: Test Multiple File Types

**Command**:
```bash
cat > /tmp/filetype_test.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == \"LOCAL_FILESYSTEM\" AND doc.recordName IN [\"app.ts\", \"config.json\", \"utils.py\", \"styles.css\", \"README.md\", \"unicode.txt\"] RETURN {recordName: doc.recordName, extension: doc.extension, hasContent: doc.block_containers != null && LENGTH(doc.block_containers.blocks) > 0, contentLength: doc.block_containers != null && doc.block_containers.blocks[0] != null ? LENGTH(doc.block_containers.blocks[0].data) : 0}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/filetype_test.json | python3 -m json.tool
```

**Success Criteria**:
- All 6 files have `hasContent: true`
- Content lengths match expected file sizes
- Different extensions all processed

**Expected Files**:
1. app.ts - TypeScript (388 bytes)
2. config.json - JSON (227 bytes)
3. utils.py - Python (693 bytes)
4. styles.css - CSS (516 bytes)
5. README.md - Markdown (539 bytes)
6. unicode.txt - Unicode text (330 bytes)

---

### Task 2.5: Verify Encoding Detection (Unicode Test)

**Command**:
```bash
cat > /tmp/unicode_test.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.recordName == \"unicode.txt\" AND doc.connectorName == \"LOCAL_FILESYSTEM\" RETURN {recordName: doc.recordName, hasContent: doc.block_containers != null && LENGTH(doc.block_containers.blocks) > 0, contentPreview: doc.block_containers != null && doc.block_containers.blocks[0] != null ? doc.block_containers.blocks[0].data : null}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/unicode_test.json | python3 -m json.tool
```

**Success Criteria**:
- Content contains Unicode characters correctly (no mojibake)
- Characters like emoji, accents, Chinese/Japanese preserved
- No replacement characters (� U+FFFD) unless in original file

**Expected Content Sample**:
```
UTF-8 Test File with Unicode Characters
========================================

Emoji: 😀 🎉 🚀 ❤️
Accents: café, naïve, résumé
Chinese: 你好世界
Japanese: こんにちは世界
```

**Failure Handling**:
- If mojibake: Encoding detection failed
- If null content: File not read
- If replacement characters: Encoding fallback used (check logs)

---

### Phase 2 Completion Checklist

- [ ] 12 new test file records created
- [ ] All records have block_containers populated
- [ ] All non-empty files have content
- [ ] All expected fields populated (extension, path, size)
- [ ] Multiple file types processed correctly
- [ ] Unicode content preserved correctly

**Gate**: At least 11/12 files with content (empty.txt can be empty).

---

## Phase 3: Comprehensive Testing

**Objective**: Execute critical tests from 17-test suite to validate all functionality

**Time Estimate**: 90-120 minutes

**Strategy**: Execute 9 most critical tests covering functionality, performance, edge cases, and integration.

---

### Test 3.1: Large File Handling

**Objective**: Verify size limit enforcement (default 10MB)

**From**: Test 3 in 010-connector-missing-content-test

**Command**:
```bash
cat > /tmp/large_file_test.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.recordName == \"large-file.md\" AND doc.connectorName == \"LOCAL_FILESYSTEM\" RETURN {recordName: doc.recordName, fileSize: doc.sizeInBytes, hasContent: doc.block_containers != null && LENGTH(doc.block_containers.blocks) > 0, contentLength: doc.block_containers != null && doc.block_containers.blocks[0] != null ? LENGTH(doc.block_containers.blocks[0].data) : 0}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/large_file_test.json | python3 -m json.tool
```

**Success Criteria**:
- File size: ~127 KB (130,048 bytes)
- Has content: true (under 10MB limit)
- Content length matches file size

**Time Estimate**: 5 minutes

**Evidence**:
```json
{
  "recordName": "large-file.md",
  "fileSize": 130048,
  "hasContent": true,
  "contentLength": 130048
}
```

---

### Test 3.2: Edge Cases

**Objective**: Verify handling of empty files, hidden files, and special characters

**From**: Test 16 in 010-connector-missing-content-test

**Command**:
```bash
cat > /tmp/edge_cases_test.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == \"LOCAL_FILESYSTEM\" AND doc.recordName IN [\"empty.txt\", \".hidden.ts\", \"file with spaces.md\"] RETURN {recordName: doc.recordName, hasContent: doc.block_containers != null && LENGTH(doc.block_containers.blocks) > 0, fileSize: doc.sizeInBytes, contentSize: doc.block_containers != null && doc.block_containers.blocks[0] != null ? LENGTH(doc.block_containers.blocks[0].data) : 0}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/edge_cases_test.json | python3 -m json.tool
```

**Success Criteria**:
- empty.txt: `hasContent: true`, `fileSize: 0`, `contentSize: 0`
- .hidden.ts: `hasContent: true`, `contentSize: 154`
- file with spaces.md: `hasContent: true`, `contentSize: 151`

**Time Estimate**: 5 minutes

**Evidence**:
```json
[
  {"recordName": "empty.txt", "hasContent": true, "fileSize": 0, "contentSize": 0},
  {"recordName": ".hidden.ts", "hasContent": true, "fileSize": 154, "contentSize": 154},
  {"recordName": "file with spaces.md", "hasContent": true, "fileSize": 151, "contentSize": 151}
]
```

---

### Test 3.3: Directory Structure Preservation

**Objective**: Verify record group association maintains directory hierarchy

**From**: Test 8 in 010-connector-missing-content-test

**Command**:
```bash
cat > /tmp/directory_test.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.recordName == \"app.ts\" AND doc.connectorName == \"LOCAL_FILESYSTEM\" AND CONTAINS(doc.externalRecordId, \"test-files\") RETURN {file: doc.recordName, path: doc.path, recordGroupId: doc.recordGroupId}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/directory_test.json | python3 -m json.tool
```

**Success Criteria**:
- Path contains directory: "source-code/app.ts"
- recordGroupId is populated (not null)
- Directory structure reflected in path field

**Time Estimate**: 5 minutes

**Failure Handling**:
- If path doesn't include directory: Relative path calculation wrong
- If recordGroupId null: Group creation not working

---

### Test 3.4: Database Impact Analysis

**Objective**: Verify reasonable content sizes and database impact

**From**: Test 13 in 010-connector-missing-content-test

**Command**:
```bash
cat > /tmp/db_impact_test.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == \"LOCAL_FILESYSTEM\" AND CONTAINS(doc.externalRecordId, \"test-files\") AND doc.block_containers != null AND LENGTH(doc.block_containers.blocks) > 0 COLLECT AGGREGATE avgSize = AVG(LENGTH(doc.block_containers.blocks[0].data)), maxSize = MAX(LENGTH(doc.block_containers.blocks[0].data)), minSize = MIN(LENGTH(doc.block_containers.blocks[0].data)), count = COUNT() RETURN {count, avgSize, maxSize, minSize}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/db_impact_test.json | python3 -m json.tool
```

**Success Criteria**:
- count: 12 (all test files)
- avgSize: ~11,000-12,000 bytes (accounting for large-file.md)
- maxSize: ~130,048 bytes (large-file.md)
- minSize: 0 (empty.txt)

**Time Estimate**: 5 minutes

**Evidence**:
```json
{
  "count": 12,
  "avgSize": 11234,
  "maxSize": 130048,
  "minSize": 0
}
```

---

### Test 3.5: Organization Isolation

**Objective**: Verify records isolated by organization ID

**From**: Test 14 in 010-connector-missing-content-test

**Command**:
```bash
# Verify all test-files records have correct orgId
cat > /tmp/org_isolation_test.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == \"LOCAL_FILESYSTEM\" AND CONTAINS(doc.externalRecordId, \"test-files\") COLLECT orgId = doc.orgId WITH COUNT INTO count RETURN {orgId, count}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/org_isolation_test.json | python3 -m json.tool
```

**Success Criteria**:
- Only one orgId: "6928ff5506880ac843ef5a3c"
- Count: 12 (all test files)

**Time Estimate**: 5 minutes

---

### Test 3.6: Processing Speed

**Objective**: Measure sync performance

**From**: Test 12 in 010-connector-missing-content-test

**Method**: Extract from logs

**Command**:
```bash
# Find sync start and completion times
docker logs docker-compose-pipeshub-ai-1 2>&1 | \
  grep -E "Starting Local Filesystem full sync|Local Filesystem full sync completed" | \
  tail -4
```

**Manual Calculation**:
- Parse timestamps from logs
- Calculate duration: end_time - start_time

**Success Criteria**:
- Total sync time < 60 seconds for 12 files
- Average per file < 5 seconds

**Time Estimate**: 5 minutes

**Evidence to Capture**:
```
Start: 2025-11-27 22:15:00,125
End:   2025-11-27 22:15:05,456
Duration: 5.331 seconds
Files: 12
Average: 0.444 seconds/file
```

---

### Test 3.7: Content Quality Sampling

**Objective**: Verify content matches source files

**From**: Test 1 in 010-connector-missing-content-test

**Commands**:
```bash
# Get content from database for app.ts
cat > /tmp/content_quality_test.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.recordName == \"app.ts\" AND doc.connectorName == \"LOCAL_FILESYSTEM\" AND CONTAINS(doc.externalRecordId, \"test-files\") RETURN doc.block_containers.blocks[0].data"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/content_quality_test.json | python3 -m json.tool > /tmp/db_content.txt

# Get actual file content
docker exec docker-compose-pipeshub-ai-1 \
  cat /data/pipeshub/test-files/source-code/app.ts > /tmp/file_content.txt

# Compare (manual or diff)
diff /tmp/db_content.txt /tmp/file_content.txt
```

**Success Criteria**:
- Content matches exactly (allowing for JSON escaping)
- No truncation
- No encoding corruption

**Time Estimate**: 10 minutes

**Repeat for**: config.json, utils.py (different file types)

---

### Test 3.8: Connector Restart Persistence

**Objective**: Verify configuration persists across restarts

**From**: Test 15 in 010-connector-missing-content-test

**Steps**:
1. Restart connector
2. Wait for initialization
3. Verify still syncing correct path
4. Verify content extraction still enabled

**Commands**:
```bash
# Restart
docker compose -f deployment/docker-compose/docker-compose.dev.yml restart pipeshub-ai

# Wait 30 seconds
sleep 30

# Check logs
docker logs docker-compose-pipeshub-ai-1 2>&1 | \
  grep -i "content extraction\|starting local filesystem full sync" | tail -5
```

**Success Criteria**:
- Logs show: "Content extraction: enabled=True, max_size_mb=10"
- Logs show: "Starting Local Filesystem full sync for: /data/pipeshub/test-files"
- No regression to old path

**Time Estimate**: 5 minutes

---

### Test 3.9: Migration Validation

**Objective**: Verify old records vs new records

**From**: Test 17 in 010-connector-missing-content-test

**Command**:
```bash
cat > /tmp/migration_test.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == \"LOCAL_FILESYSTEM\" COLLECT hasContent = (doc.block_containers != null && LENGTH(doc.block_containers.blocks) > 0), hasTestFiles = CONTAINS(doc.externalRecordId, \"test-files\") WITH COUNT INTO count RETURN {hasContent, hasTestFiles, count}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/migration_test.json | python3 -m json.tool
```

**Success Criteria**:
- New test-files records: `hasContent: true, hasTestFiles: true, count: 12`
- Old local-files records: `hasContent: false, hasTestFiles: false, count: 1673`

**Time Estimate**: 5 minutes

**Evidence**:
```json
[
  {"hasContent": true, "hasTestFiles": true, "count": 12},
  {"hasContent": false, "hasTestFiles": false, "count": 1673}
]
```

---

### Phase 3 Test Summary

**Total Tests**: 9 critical tests
**Estimated Time**: 60-90 minutes (including analysis)

**Test Coverage**:
- Functionality: Tests 3.1, 3.2, 3.7 (file types, edge cases, content quality)
- Performance: Test 3.6 (processing speed)
- Data Integrity: Tests 3.3, 3.4, 3.5 (directory structure, DB impact, org isolation)
- Reliability: Test 3.8 (restart persistence)
- Migration: Test 3.9 (old vs new records)

---

### Phase 3 Completion Checklist

- [ ] Large file handling verified (127KB processed)
- [ ] Edge cases passed (empty, hidden, spaces)
- [ ] Directory structure preserved
- [ ] Database impact measured (avg, max, min sizes)
- [ ] Organization isolation verified
- [ ] Processing speed acceptable (<60s for 12 files)
- [ ] Content quality matches source files
- [ ] Configuration persists across restarts
- [ ] Migration validated (old vs new records)

**Gate**: At least 8/9 tests passing.

---

## Phase 4: Final Verification

**Objective**: End-to-end validation and final sign-off

**Time Estimate**: 30-45 minutes

---

### Task 4.1: Complete Content Statistics

**Command**:
```bash
cat > /tmp/final_stats.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == \"LOCAL_FILESYSTEM\" COLLECT hasContent = (doc.block_containers != null && LENGTH(doc.block_containers.blocks) > 0) WITH COUNT INTO count RETURN {hasContent, count, percentage: count * 100.0 / (SELECT COUNT(*) FROM records WHERE connectorName == \"LOCAL_FILESYSTEM\")[0]}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/final_stats.json | python3 -m json.tool
```

**Success Criteria**:
- New records (test-files): 12 with content (100% of new files)
- Old records (local-files): 1673 without content (expected)
- Total: 1685 records (1673 + 12)

**Evidence**:
```json
[
  {"hasContent": true, "count": 12, "percentage": 0.71},
  {"hasContent": false, "count": 1673, "percentage": 99.29}
]
```

**Time Estimate**: 5 minutes

---

### Task 4.2: File Type Distribution

**Command**:
```bash
cat > /tmp/filetype_distribution.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == \"LOCAL_FILESYSTEM\" AND CONTAINS(doc.externalRecordId, \"test-files\") COLLECT ext = doc.extension WITH COUNT INTO count RETURN {extension: ext, count: count} SORT count DESC"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/filetype_distribution.json | python3 -m json.tool
```

**Success Criteria**:
- 7 different extensions represented
- All known file types present: .ts, .json, .py, .css, .md, .txt, .yaml

**Time Estimate**: 5 minutes

---

### Task 4.3: Verify Indexing Status

**Command**:
```bash
cat > /tmp/indexing_status.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == \"LOCAL_FILESYSTEM\" AND CONTAINS(doc.externalRecordId, \"test-files\") COLLECT indexingStatus = doc.indexingStatus, extractionStatus = doc.extractionStatus WITH COUNT INTO count RETURN {indexingStatus, extractionStatus, count}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/indexing_status.json | python3 -m json.tool
```

**Success Criteria**:
- All records have indexingStatus (may be "NOT_STARTED", "IN_PROGRESS", or "COMPLETED")
- All records have extractionStatus

**Note**: If indexing pipeline is running, some may be "COMPLETED". If not running, "NOT_STARTED" is expected.

**Time Estimate**: 5 minutes

---

### Task 4.4: Smoke Test - Sample Full Record

**Command**:
```bash
cat > /tmp/full_record_sample.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.recordName == \"config.json\" AND doc.connectorName == \"LOCAL_FILESYSTEM\" AND CONTAINS(doc.externalRecordId, \"test-files\") RETURN doc"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/full_record_sample.json | python3 -m json.tool > /tmp/full_record.json

# Review manually
cat /tmp/full_record.json
```

**Manual Review Checklist**:
- [ ] _key: UUID present
- [ ] orgId: "6928ff5506880ac843ef5a3c"
- [ ] recordName: "config.json"
- [ ] recordType: "FILE"
- [ ] externalRecordId: Contains "/data/pipeshub/test-files/source-code/config.json"
- [ ] connectorName: "LOCAL_FILESYSTEM"
- [ ] mimeType: "application/json"
- [ ] extension: ".json"
- [ ] path: "source-code/config.json"
- [ ] sizeInBytes: 227
- [ ] indexingStatus: Present
- [ ] extractionStatus: Present
- [ ] block_containers: Not null
- [ ] block_containers.blocks: Array with 1 element
- [ ] block_containers.blocks[0].type: "TEXT"
- [ ] block_containers.blocks[0].format: "TXT"
- [ ] block_containers.blocks[0].data: JSON content (227 chars)

**Time Estimate**: 10 minutes

---

### Task 4.5: Validate Against Research Baseline

**Comparison**:

| Metric | Before (Research) | After (Current) | Change |
|--------|-------------------|-----------------|--------|
| Total LOCAL_FILESYSTEM records | 1,673 | 1,685 | +12 |
| Records with content | 0 (0%) | 12 (0.71%) | +12 |
| Records without content | 1,673 (100%) | 1,673 (99.29%) | 0 |
| Sync path | /data/local-files | /data/pipeshub/test-files | Fixed |
| Files per sync | 0 | 12 | Working |

**Success Criteria**:
- 12 new records created
- 12 records have content populated
- Sync path corrected
- No regression in old records

**Time Estimate**: 5 minutes

---

### Task 4.6: Log Analysis

**Command**:
```bash
# Count successful content loads
docker logs docker-compose-pipeshub-ai-1 2>&1 | \
  grep "Content loaded:" | wc -l

# Count content warnings (files too large or unreadable)
docker logs docker-compose-pipeshub-ai-1 2>&1 | \
  grep "No content for" | wc -l

# Check for errors during sync
docker logs docker-compose-pipeshub-ai-1 2>&1 | \
  grep -i "error" | grep -i "content\|sync" | tail -10
```

**Success Criteria**:
- "Content loaded:" count = 12 (or 11 if empty.txt doesn't log)
- "No content for" count = 0 (all files readable)
- No errors related to content extraction or sync

**Time Estimate**: 5 minutes

---

### Task 4.7: Create Validation Report

**Document**:
- All test results (Phase 3)
- Final statistics (Phase 4)
- Evidence artifacts (queries, logs)
- Success criteria met
- Any issues encountered

**Template**:
```markdown
# Content Extraction Validation Report

**Date**: 2025-11-27
**Objective**: Validate content extraction post-configuration fix

## Summary
- Configuration Fix: ✅ COMPLETE
- Content Extraction: ✅ WORKING
- Test Files Processed: 12/12 (100%)
- Tests Passed: 9/9 (100%)

## Key Metrics
- Sync Path: /data/pipeshub/test-files (corrected)
- Records Created: 12
- Content Populated: 12 (100%)
- Processing Speed: X.XX seconds for 12 files
- Average File Size: XX KB
- Max File Size: 127 KB

## Test Results
[Detailed results from Phase 3]

## Evidence
[Query outputs, log excerpts]

## Issues Encountered
[Any problems and resolutions]

## Conclusion
Content extraction validated and working correctly.
```

**Time Estimate**: 10 minutes

---

### Phase 4 Completion Checklist

- [ ] Final statistics captured
- [ ] File type distribution verified
- [ ] Indexing status checked
- [ ] Sample full record reviewed (all fields correct)
- [ ] Baseline comparison complete
- [ ] Log analysis complete (no errors)
- [ ] Validation report created

**Gate**: All checklist items complete.

---

## Success Criteria Summary

### Configuration Fix Success
- [ ] Connector syncing `/data/pipeshub/test-files/`
- [ ] Logs confirm new path
- [ ] Sync finding 12 files (not 0)

### Content Extraction Success
- [ ] All 12 test files have records in database
- [ ] All records have `block_containers` populated
- [ ] All non-empty files have content
- [ ] Content matches source files
- [ ] Unicode preserved correctly

### Comprehensive Testing Success
- [ ] 8/9 critical tests passing
- [ ] Processing speed acceptable
- [ ] Edge cases handled correctly
- [ ] Configuration persists across restarts

### Final Verification Success
- [ ] Statistics match expectations
- [ ] No errors in logs
- [ ] All fields populated correctly
- [ ] Validation report created

---

## Failure Handling

### Configuration Fix Failures

**Scenario**: Config update doesn't work (still syncing old path)

**Actions**:
1. Verify config method chosen was correct
2. Try alternative config method (env vars → etcd → config file)
3. Check file permissions and ownership
4. Review connector initialization code for config source
5. Consider manual intervention via database/UI

**Escalation**: If all methods fail, need developer support to understand config precedence.

---

### Content Extraction Failures

**Scenario**: Files synced but no content populated

**Actions**:
1. Check logs for "Content loaded:" messages (should see 12)
2. Verify `_read_file_content()` code deployed (grep in container)
3. Check chardet dependency installed (python3 -c "import chardet")
4. Review logs for "No content for" warnings
5. Test manual file read in container: `cat /data/pipeshub/test-files/source-code/app.ts`

**Escalation**: If code deployed and files readable but content still null, investigate Block creation logic.

---

### Partial Success Scenario

**Scenario**: Some files have content, others don't

**Actions**:
1. Identify which files failed (query by hasContent=false and test-files path)
2. Check file types, sizes, encoding
3. Review logs for specific file errors
4. Test problematic files manually
5. Investigate pattern (e.g., all .yaml fail, or all files >100KB)

**Resolution**: May need to adjust size limits, add file type filters, or fix encoding detection.

---

### Performance Issues

**Scenario**: Sync taking too long (>60s for 12 files)

**Actions**:
1. Check system resources (CPU, memory, disk I/O)
2. Review logs for delays (network calls, DB writes)
3. Test file read speed manually
4. Check if other services consuming resources
5. Monitor database write performance

**Acceptable**: Up to 2 minutes for 12 files (including large-file.md)
**Concerning**: >5 minutes (investigate database or I/O issues)

---

## Rollback Plan

### If Configuration Fix Breaks Connector

**Steps**:
```bash
# 1. Restore backup config
cp deployment/docker-compose/docker-compose.dev.yml.backup \
   deployment/docker-compose/docker-compose.dev.yml

# 2. Restart connector
docker compose -f deployment/docker-compose/docker-compose.dev.yml restart pipeshub-ai

# 3. Verify back to old state
docker logs docker-compose-pipeshub-ai-1 2>&1 | \
  grep "Starting Local Filesystem full sync" | tail -1
# Should show: /data/local-files
```

**Time**: 5 minutes

---

### If Content Extraction Causes Crashes

**Steps**:
```bash
# 1. Check crash loop
docker ps | grep pipeshub-ai

# 2. Get crash logs
docker logs docker-compose-pipeshub-ai-1 --tail=100

# 3. If crashes, disable content extraction via config
# Update config to: "content_extraction": {"enabled": false}

# 4. Restart
docker compose -f deployment/docker-compose/docker-compose.dev.yml restart pipeshub-ai
```

**Note**: This would revert to metadata-only mode (acceptable for emergency).

---

## Decision Points

### Decision 1: Configuration Method

**Trigger**: Task 1.1 - After investigating config methods

**Options**:
A. Environment variables (docker-compose.yml)
B. Configuration file in container
C. Direct etcd update
D. Database/UI configuration

**Decision Framework**:
- Choose A if env vars exist and are simple
- Choose B if config file found and not overridden
- Choose C if etcd accessible and encryption manageable
- Choose D if UI/API available

**Impact**: Method determines Task 1.2 implementation

---

### Decision 2: Acceptable Content Percentage

**Trigger**: Task 2.2 - After checking content population

**Question**: What percentage of files need content to proceed?

**Options**:
- 100% (12/12 files) - Ideal
- 95%+ (11+/12 files) - Acceptable (e.g., if one file has encoding issue)
- 90%+ (10+/12 files) - Concerning but investigate
- <90% - STOP and troubleshoot

**Decision Framework**:
- If 12/12: Proceed immediately
- If 11/12: Identify failed file, proceed if edge case (e.g., binary file)
- If 10/12: Investigate pattern before proceeding
- If <10: STOP, major issue

**Impact**: Determines whether to proceed to Phase 3 or pause for troubleshooting

---

### Decision 3: Test Suite Scope

**Trigger**: Phase 3 - Before executing comprehensive tests

**Question**: Execute all 17 tests or subset of 9?

**Options**:
- Full 17 tests (~4-6 hours) - Most thorough
- Critical 9 tests (~90-120 minutes) - Balanced
- Quick 5 tests (~45 minutes) - Fast validation

**Decision Framework**:
- Choose Full if: First deployment, high risk, production prep
- Choose Critical if: Development testing, time-limited, core functionality focus
- Choose Quick if: Emergency validation, known working state

**Current Plan**: Critical 9 tests (balanced approach)

**Impact**: Time estimate and coverage depth

---

### Decision 4: Old Records Migration

**Trigger**: Phase 4 - After validating test files work

**Question**: Should we delete/migrate the 1,673 old records without content?

**Options**:
A. Leave as-is (1,673 without content, 12 with content)
B. Delete old records (clean slate, only new 12)
C. Trigger re-sync of old path (if files still exist)
D. Defer decision to later

**Decision Framework**:
- Choose A if: No impact on testing, production not affected
- Choose B if: Old files don't exist anymore, want clean state
- Choose C if: Old files exist and should have content
- Choose D if: Out of scope for validation task

**Current Plan**: Choose A (validation focused, don't touch old data)

**Impact**: Database state and total record count

---

## Dependencies and Prerequisites

### External Dependencies
- Docker containers running (all 8 services)
- ArangoDB accessible on localhost:8529
- Test files exist at /data/pipeshub/test-files/
- Correct credentials in .env file

### Code Dependencies
- Content extraction code deployed (line 396 in connector.py)
- chardet==5.2.0 installed in container
- Block, BlockType, DataFormat imports working

### Configuration Dependencies
- Connector configuration mechanism accessible
- Permissions to update configuration
- Ability to restart connector service

---

## Timing and Parallelization

### Sequential Tasks (Cannot Parallelize)
- Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4
- Within Phase 1: Task 1.1 → 1.2 → 1.3 → 1.4 → 1.5

### Parallelizable Tasks
- Phase 3 tests can run in parallel (up to 8 concurrent queries)
- Phase 4 verification tasks mostly independent

### Bottlenecks
- Connector restart (2-3 minutes)
- Initial sync (5-30 seconds for 12 files)
- Large file processing (large-file.md may take longer)

### Critical Path
1. Configuration fix (Phase 1): 30-45 minutes
2. Initial validation (Phase 2): 20-30 minutes
3. Comprehensive testing (Phase 3): 90-120 minutes

**Total Critical Path**: ~2.5-3.5 hours

---

## Evidence Collection

### Artifacts to Capture

**Phase 0**:
- Container status output
- Test files list
- Baseline statistics JSON
- Current sync path log

**Phase 1**:
- Configuration before/after diff
- Restart logs
- New sync path confirmation
- Initial sync logs showing "Found X files"

**Phase 2**:
- Query results for all 12 files
- Content preview samples
- Field validation results
- Unicode content sample

**Phase 3**:
- All 9 test query results
- Log excerpts for processing speed
- Content quality diff outputs
- Restart persistence logs

**Phase 4**:
- Final statistics
- File type distribution
- Full sample record JSON
- Validation report

---

## Risk Assessment

### High Risk Items
1. **Configuration Change**: Could break connector if done incorrectly
   - Mitigation: Backup config before change, test in dev first
   - Rollback: 5 minutes to restore backup

2. **Sync Path Wrong**: Could sync wrong directory or cause errors
   - Mitigation: Verify path exists before restart
   - Detection: Logs will show "path does not exist" error

### Medium Risk Items
3. **Content Extraction Memory**: Large files could cause OOM
   - Mitigation: 10MB size limit enforced
   - Detection: Container crash/restart, OOM in logs

4. **Encoding Issues**: Unicode files could fail to decode
   - Mitigation: chardet with fallback to UTF-8
   - Detection: "No content for" warnings in logs

### Low Risk Items
5. **Database Write Performance**: Large volume could slow down
   - Mitigation: Only 12 files, small volume
   - Impact: Sync takes longer but completes

6. **Test Query Performance**: Complex queries could timeout
   - Mitigation: Queries tested in research phase
   - Impact: Query takes longer but returns results

---

## Post-Validation Actions

### Immediate (After Phase 4 Complete)
1. **Create summary report** (10 minutes)
   - Consolidate all evidence
   - Document any issues
   - Record final metrics

2. **Communicate results** (5 minutes)
   - Share validation status
   - Highlight any concerns
   - Recommend next steps

### Short-term (Within 24 hours)
3. **Monitor connector stability** (ongoing)
   - Watch for errors in logs
   - Check memory usage trends
   - Verify syncs continue working

4. **Decide on old records** (decision needed)
   - Keep as-is vs. migrate vs. delete
   - Based on production requirements

### Medium-term (Within 1 week)
5. **Production deployment plan** (if applicable)
   - Schedule deployment window
   - Prepare rollback procedures
   - Notify stakeholders

6. **Performance optimization** (if needed)
   - Based on observed metrics
   - Tune batch sizes, limits
   - Add monitoring/alerts

---

## Appendix A: Command Reference

### Quick Commands

**Container Status**:
```bash
docker compose -f deployment/docker-compose/docker-compose.dev.yml ps
```

**Container Logs**:
```bash
docker logs -f docker-compose-pipeshub-ai-1
```

**Restart Connector**:
```bash
docker compose -f deployment/docker-compose/docker-compose.dev.yml restart pipeshub-ai
```

**ArangoDB Query Template**:
```bash
cat > /tmp/query.json << 'EOF'
{
  "query": "YOUR AQL QUERY HERE"
}
EOF

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

## Appendix B: AQL Queries

### Query: Total Records with Content
```aql
FOR doc IN records
FILTER doc.connectorName == "LOCAL_FILESYSTEM"
COLLECT hasContent = (
  doc.block_containers != null AND
  LENGTH(doc.block_containers.blocks) > 0
)
WITH COUNT INTO count
RETURN {hasContent, count}
```

### Query: Test Files Content Check
```aql
FOR doc IN records
FILTER doc.connectorName == "LOCAL_FILESYSTEM"
  AND CONTAINS(doc.externalRecordId, "test-files")
RETURN {
  recordName: doc.recordName,
  hasContent: doc.block_containers != null AND
              LENGTH(doc.block_containers.blocks) > 0,
  contentLength: doc.block_containers != null &&
                 doc.block_containers.blocks[0] != null
                 ? LENGTH(doc.block_containers.blocks[0].data)
                 : 0
}
```

### Query: Content Statistics
```aql
FOR doc IN records
FILTER doc.connectorName == "LOCAL_FILESYSTEM"
  AND CONTAINS(doc.externalRecordId, "test-files")
  AND doc.block_containers != null
  AND LENGTH(doc.block_containers.blocks) > 0
COLLECT AGGREGATE
  avgSize = AVG(LENGTH(doc.block_containers.blocks[0].data)),
  maxSize = MAX(LENGTH(doc.block_containers.blocks[0].data)),
  minSize = MIN(LENGTH(doc.block_containers.blocks[0].data)),
  count = COUNT()
RETURN {count, avgSize, maxSize, minSize}
```

---

## Appendix C: Troubleshooting Guide

### Issue: "Found 0 files to sync"

**Symptoms**:
- Logs show sync completed but 0 files
- No "Content loaded:" messages

**Diagnosis**:
```bash
# Check if path exists
docker exec docker-compose-pipeshub-ai-1 \
  ls -la /data/pipeshub/test-files/

# Check logs for path
docker logs docker-compose-pipeshub-ai-1 2>&1 | \
  grep "Starting Local Filesystem full sync"
```

**Solutions**:
1. Path doesn't exist: Create test files
2. Path correct but empty: Populate test files
3. Wrong path in config: Update configuration
4. Permissions issue: Check file ownership/permissions

---

### Issue: No content in block_containers

**Symptoms**:
- Records created (12 files found)
- But all have `block_containers: null` or `blocks: []`

**Diagnosis**:
```bash
# Check if code deployed
docker exec docker-compose-pipeshub-ai-1 \
  grep -A 20 "def _read_file_content" \
  /app/python/app/connectors/sources/local_filesystem/connector.py

# Check logs for content extraction
docker logs docker-compose-pipeshub-ai-1 2>&1 | \
  grep -i "content extraction\|content loaded"
```

**Solutions**:
1. Code not deployed: Rebuild Docker image
2. Content extraction disabled: Check config
3. Files unreadable: Check permissions, encoding
4. Implementation bug: Review code, check unit tests

---

### Issue: Container crash loop

**Symptoms**:
- Container keeps restarting
- Status shows "Restarting"

**Diagnosis**:
```bash
# Get crash logs
docker logs docker-compose-pipeshub-ai-1 --tail=100

# Check for OOM
docker inspect docker-compose-pipeshub-ai-1 | grep -i oom
```

**Solutions**:
1. OOM error: Increase memory limit or reduce file size limit
2. Python error: Review traceback, fix code bug
3. Dependency error: Check chardet installation
4. Config error: Verify JSON syntax, field types

---

## Conclusion

This plan provides a complete, executable roadmap for:

1. **Fixing** the configuration path mismatch (Phase 1)
2. **Validating** content extraction works (Phase 2)
3. **Testing** comprehensively across file types and scenarios (Phase 3)
4. **Verifying** end-to-end system functionality (Phase 4)

**Key Success Factors**:
- Systematic approach with clear gates between phases
- Evidence-driven validation at each step
- Comprehensive testing covering functionality, performance, edge cases
- Clear decision frameworks for issues
- Rollback plans for safety

**Expected Outcome**: A fully validated content extraction system with 12 test files successfully processed, proven through database queries, log analysis, and comprehensive testing.

**Ready to Execute**: All prerequisites identified, commands documented, success criteria defined, and failure handling planned.

---

<status>
  <plan_completeness>COMPLETE</plan_completeness>
  <ready_for_execution>YES</ready_for_execution>
  <estimated_duration>3.5-5.0 hours</estimated_duration>
  <risk_level>LOW-MEDIUM</risk_level>
  <confidence>HIGH</confidence>
</status>
