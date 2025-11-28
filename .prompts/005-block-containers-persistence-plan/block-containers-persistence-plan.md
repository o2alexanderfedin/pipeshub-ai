# Block Containers Persistence Fix Plan

## Executive Summary

This plan addresses the block_containers persistence issue by adding the field to the serialization methods in entities.py. The fix is straightforward: update two custom serialization methods to include block_containers in their return dictionaries, ensuring proper JSON serialization of the BlocksContainer object. This will enable content extracted by the local_filesystem connector to persist to ArangoDB and be available for indexing and retrieval.

**Root Cause Addressed**: Custom serialization methods `to_arango_base_record()` and `to_arango_record()` in `/backend/python/app/models/entities.py` use explicit field whitelisting and do NOT include block_containers, causing content to be lost during database persistence (lines 90-116, 170-189).

**Fix Strategy**: Add block_containers field to the `to_arango_base_record()` method with proper Pydantic serialization (model_dump) to convert BlocksContainer objects to JSON-compatible dictionaries.

**Estimated Time**: 2-3 hours total
- Phase 0: 15 minutes (backup, documentation)
- Phase 1: 30 minutes (code changes, rebuild)
- Phase 2: 15 minutes (immediate verification)
- Phase 3: 30 minutes (comprehensive validation of 12 test files)
- Phase 4: 45 minutes (full testing suite - 9 critical tests)
- Phase 5: 15 minutes (final sign-off)

**Critical Decisions**:
1. **Storage location**: Store block_containers in ArangoDB records collection (recommended for simplicity and immediate fix)
2. **JSON serialization**: Use `block_containers.model_dump()` to ensure proper Pydantic serialization
3. **Null handling**: Handle empty/null block_containers gracefully with conditional serialization
4. **Indexing compatibility**: Verify indexing service can consume content from ArangoDB (may need future updates)

## Prerequisites

<phase id="phase-0" name="Pre-Implementation">
<objective>Prepare for fix implementation by backing up current state and documenting baseline behavior</objective>

<tasks>
1. **Backup database state**: Export current ArangoDB records to verify rollback capability
   - Acceptance: JSON export file created with timestamp

2. **Document current behavior**: Run test query to confirm block_containers is missing
   - Acceptance: Query result shows 0 records with block_containers field

3. **Create git branch**: Create feature branch for fix
   - Acceptance: Branch `fix/block-containers-persistence` created

4. **Verify test environment**: Confirm docker containers running and accessible
   - Acceptance: Can exec into container and run Python shell
</tasks>

<success_criteria>
- Database backup created: file exists at `.prompts/005-block-containers-persistence-plan/backup-TIMESTAMP.json`
- Baseline documented: Query confirms 0/12 test records have block_containers
- Git branch created: `git branch` shows `fix/block-containers-persistence`
- Container accessible: `docker exec docker-compose-pipeshub-ai-1 python3 --version` succeeds
</success_criteria>

<estimated_time>15 minutes</estimated_time>

<dependencies>
- Docker containers running
- ArangoDB accessible
- Git repository clean
</dependencies>

<risks>
- **Risk**: Database backup fails due to disk space
  - **Mitigation**: Check disk space before backup, use selective export if needed
</risks>
</phase>

## Phase 1: Core Fix Implementation

<phase id="phase-1" name="Fix Implementation">
<objective>Implement the identified fix by adding block_containers to serialization methods</objective>

<code_changes>
### File 1: /backend/python/app/models/entities.py

**Location**: Lines 90-116 (to_arango_base_record method)

**Current Code**:
```python
def to_arango_base_record(self) -> Dict:
    return {
        "_key": self.id,
        "orgId": self.org_id,
        "recordName": self.record_name,
        "recordType": self.record_type.value,
        "externalRecordId": self.external_record_id,
        "externalRevisionId": self.external_revision_id,
        "externalGroupId": self.external_record_group_id,
        "externalParentId": self.parent_external_record_id,
        "version": self.version,
        "origin": self.origin.value,
        "connectorName": self.connector_name.value,
        "mimeType": self.mime_type,
        "webUrl": self.weburl,
        "createdAtTimestamp": self.created_at,
        "updatedAtTimestamp": self.updated_at,
        "sourceCreatedAtTimestamp": self.source_created_at,
        "sourceLastModifiedTimestamp": self.source_updated_at,
        "indexingStatus": "NOT_STARTED",
        "extractionStatus": "NOT_STARTED",
        "isDeleted": False,
        "isArchived": False,
        "deletedByUserId": None,
        "previewRenderable": self.preview_renderable,
        "isShared": self.is_shared,
    }
```

**Updated Code**:
```python
def to_arango_base_record(self) -> Dict:
    base_dict = {
        "_key": self.id,
        "orgId": self.org_id,
        "recordName": self.record_name,
        "recordType": self.record_type.value,
        "externalRecordId": self.external_record_id,
        "externalRevisionId": self.external_revision_id,
        "externalGroupId": self.external_record_group_id,
        "externalParentId": self.parent_external_record_id,
        "version": self.version,
        "origin": self.origin.value,
        "connectorName": self.connector_name.value,
        "mimeType": self.mime_type,
        "webUrl": self.weburl,
        "createdAtTimestamp": self.created_at,
        "updatedAtTimestamp": self.updated_at,
        "sourceCreatedAtTimestamp": self.source_created_at,
        "sourceLastModifiedTimestamp": self.source_updated_at,
        "indexingStatus": "NOT_STARTED",
        "extractionStatus": "NOT_STARTED",
        "isDeleted": False,
        "isArchived": False,
        "deletedByUserId": None,
        "previewRenderable": self.preview_renderable,
        "isShared": self.is_shared,
    }

    # Add block_containers if populated (handle empty gracefully)
    if self.block_containers and (self.block_containers.blocks or self.block_containers.block_groups):
        base_dict["blockContainers"] = self.block_containers.model_dump(mode='json')

    return base_dict
```

**Rationale**:
- Adds block_containers to ArangoDB serialization while maintaining backward compatibility
- Uses Pydantic's `model_dump(mode='json')` for proper JSON serialization
- Conditional inclusion prevents storing empty containers
- Uses camelCase "blockContainers" to match ArangoDB naming convention

### Note on FileRecord.to_arango_record()

**Decision**: Do NOT modify `FileRecord.to_arango_record()` (lines 170-189)

**Rationale**:
- This method serializes to the `files` collection which stores file-specific metadata only
- Content should be stored in the `records` collection via `to_arango_base_record()`
- Storing content in both collections would cause duplication
- The `files` collection is optimized for file metadata queries, not content storage
</code_changes>

<configuration_changes>
None required - no configuration files need updating
</configuration_changes>

<database_changes>
### Schema Update

**Collection**: records

**Current Schema**: No block_containers field expected

**Updated Schema**:
```json
{
  "_key": "string",
  "orgId": "string",
  "recordName": "string",
  "...": "... (existing 22 fields)",
  "blockContainers": {
    "blocks": [
      {
        "id": "string",
        "type": "string",
        "format": "string",
        "data": "string",
        "...": "... (optional metadata fields)"
      }
    ],
    "block_groups": []
  }
}
```

**Migration**: None required - ArangoDB is schema-less and will accept the new field automatically for new/updated records

**Existing Records**: Will NOT have block_containers field (acceptable - only affects historical data, new syncs will have content)
</database_changes>

<deployment_steps>
1. **Apply code changes**: Edit entities.py to add block_containers serialization
   - Command: `Edit tool` to modify file
   - Expected: File saved successfully

2. **Rebuild Docker container**: Rebuild to include code changes
   - Command: `cd /Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/deployment/docker-compose && docker-compose build pipeshub-ai`
   - Expected: Build completes without errors (~ 2-5 minutes)

3. **Restart services**: Restart container to load new code
   - Command: `docker-compose restart pipeshub-ai`
   - Expected: Container restarts, logs show "Application started"

4. **Verify code loaded**: Check that new code is active
   - Command: `docker exec docker-compose-pipeshub-ai-1 python3 -c "from app.models.entities import Record; import inspect; print('block_containers' in inspect.getsource(Record.to_arango_base_record))"`
   - Expected: Output shows `True`
</deployment_steps>

<success_criteria>
- Code changes applied: entities.py modified with block_containers serialization
- Container rebuilt: Docker build succeeds with exit code 0
- Service restarted: Container running and healthy
- No errors in logs: `docker logs docker-compose-pipeshub-ai-1 --tail 50` shows no exceptions
- Code verification: Can import and inspect modified method successfully
</success_criteria>

<estimated_time>30 minutes (including 5-minute rebuild)</estimated_time>

<rollback_procedure>
If this phase fails:
1. **Revert code changes**: `git checkout backend/python/app/models/entities.py`
2. **Rebuild container**: `docker-compose build pipeshub-ai`
3. **Restart services**: `docker-compose restart pipeshub-ai`
4. **Verify rollback**: Check that original code is active
5. **Investigate failure**: Review build logs and error messages
</rollback_procedure>
</phase>

## Phase 2: Immediate Verification

<phase id="phase-2" name="Immediate Verification">
<objective>Confirm fix works with simple test by creating a new record and verifying content persists</objective>

<verification_steps>
### Step 1: Trigger Content Sync

**Action**:
```bash
# Trigger local filesystem connector sync via API
curl -X POST http://localhost:8080/api/v1/connectors/local-filesystem/sync \
  -H "Content-Type: application/json" \
  -d '{"org_id": "test-org"}'

# OR manually create test file and wait for auto-sync
echo "Test content for persistence verification" > /data/pipeshub/test-files/verification-test.txt
```

**Expected Result**: Sync completes successfully, logs show "Content loaded: verification-test.txt"

### Step 2: Query for Content

**Query**:
```python
# Access ArangoDB via Python shell in container
docker exec -it docker-compose-pipeshub-ai-1 python3 << 'EOF'
from app.connectors.core.base.db.arango_service import ArangoService
from app.config.arango_config import get_arango_config

config = get_arango_config()
service = ArangoService(config)

# Query for test record
query = """
FOR doc IN records
FILTER doc.connectorName == "LOCAL_FILESYSTEM"
  AND CONTAINS(doc.externalRecordId, "verification-test.txt")
RETURN {
  recordName: doc.recordName,
  hasBlockContainers: doc.blockContainers != null,
  blockCount: doc.blockContainers ? LENGTH(doc.blockContainers.blocks) : 0,
  contentPreview: doc.blockContainers && LENGTH(doc.blockContainers.blocks) > 0
    ? SUBSTRING(doc.blockContainers.blocks[0].data, 0, 100)
    : null
}
"""

result = service.execute_query(query)
print(result)
EOF
```

**Expected Result**:
```json
[{
  "recordName": "verification-test.txt",
  "hasBlockContainers": true,
  "blockCount": 1,
  "contentPreview": "Test content for persistence verification"
}]
```

### Step 3: Validate Content Quality

**Checks**:
- [ ] blockContainers field exists in database record
- [ ] blocks array has at least 1 entry
- [ ] data field contains actual file content
- [ ] Content matches source file exactly
- [ ] No truncation or corruption
- [ ] JSON structure is valid (no serialization errors)

**Verification Script**:
```bash
# Compare database content with source file
docker exec docker-compose-pipeshub-ai-1 python3 << 'EOF'
import json
from app.connectors.core.base.db.arango_service import ArangoService
from app.config.arango_config import get_arango_config

# Read source file
with open('/data/pipeshub/test-files/verification-test.txt', 'r') as f:
    source_content = f.read()

# Query database
config = get_arango_config()
service = ArangoService(config)
query = """
FOR doc IN records
FILTER CONTAINS(doc.externalRecordId, "verification-test.txt")
RETURN doc.blockContainers.blocks[0].data
"""
db_content = service.execute_query(query)[0]

# Compare
if source_content == db_content:
    print("SUCCESS: Content matches perfectly")
else:
    print(f"FAILURE: Content mismatch")
    print(f"Source length: {len(source_content)}")
    print(f"DB length: {len(db_content)}")
EOF
```
</verification_steps>

<success_criteria>
- Query returns blockContainers field: Result has `hasBlockContainers: true`
- Content preview shows actual text: Not null, matches source file start
- Block count greater than 0: At least 1 block present
- Content matches file: Byte-for-byte identical to source
- No serialization errors: JSON structure valid, no Python object references
</success_criteria>

<estimated_time>15 minutes</estimated_time>

<failure_handling>
If verification fails:

**Scenario 1: blockContainers field missing**
1. Check logs for serialization errors: `docker logs docker-compose-pipeshub-ai-1 | grep -i error`
2. Verify code change applied: Re-read entities.py in container
3. Test serialization manually in Python shell:
   ```python
   from app.models.entities import FileRecord, RecordType
   from app.models.blocks import Block, BlockType, DataFormat
   from app.config.constants.arangodb import Connectors, OriginTypes

   record = FileRecord(
       record_name='test', record_type=RecordType.FILE,
       external_record_id='test', connector_name=Connectors.LOCAL_FILESYSTEM,
       origin=OriginTypes.CONNECTOR, version=1, org_id='test',
       is_file=True, size_in_bytes=10
   )
   record.block_containers.blocks.append(
       Block(type=BlockType.TEXT, format=DataFormat.TXT, data='test')
   )

   result = record.to_arango_base_record()
   print('blockContainers' in result)
   print(result.get('blockContainers'))
   ```
4. If test fails, code change didn't apply - verify rebuild and restart

**Scenario 2: Content is empty/truncated**
1. Check connector logs for extraction errors
2. Verify file is readable: `cat /data/pipeshub/test-files/verification-test.txt`
3. Check content extraction in connector code
4. May indicate connector issue, not persistence issue

**Scenario 3: Serialization errors (Python objects instead of JSON)**
1. Verify using `model_dump(mode='json')` not `model_dump()`
2. Check BlocksContainer model has proper JSON serialization
3. Test Block.model_dump() in isolation
4. May need to add custom serializers for specific Block metadata fields
</failure_handling>
</phase>

## Phase 3: Comprehensive Validation

<phase id="phase-3" name="Resume Original Phase 2">
<objective>Validate all 12 test files from original validation have content persisted correctly</objective>

<validation_tasks>
### Task 1: Verify All Test Records

**Query**:
```python
docker exec docker-compose-pipeshub-ai-1 python3 << 'EOF'
from app.connectors.core.base.db.arango_service import ArangoService
from app.config.arango_config import get_arango_config

config = get_arango_config()
service = ArangoService(config)

query = """
FOR doc IN records
FILTER doc.connectorName == "LOCAL_FILESYSTEM"
  AND CONTAINS(doc.externalRecordId, "test-files")
COLLECT hasContent = (doc.blockContainers != null && LENGTH(doc.blockContainers.blocks) > 0)
WITH COUNT INTO count
RETURN { hasContent, count }
"""

result = service.execute_query(query)
print("Content Distribution:", result)

# Expected: [{ hasContent: true, count: 12 }]
# If seeing: [{ hasContent: false, count: X }] - records exist but no content
# Fix needed: Re-trigger sync or investigate extraction
EOF
```

**Expected**: All 12 test files show `hasContent: true`

### Task 2: File Type Coverage

Check that each file type has content properly persisted:

**Query**:
```python
query = """
FOR doc IN records
FILTER doc.connectorName == "LOCAL_FILESYSTEM"
  AND CONTAINS(doc.externalRecordId, "test-files")
RETURN {
  file: doc.recordName,
  extension: doc.mimeType,
  hasContent: doc.blockContainers != null,
  blockCount: doc.blockContainers ? LENGTH(doc.blockContainers.blocks) : 0,
  contentLength: doc.blockContainers && doc.blockContainers.blocks[0]
    ? LENGTH(doc.blockContainers.blocks[0].data)
    : 0
}
"""
```

**File Type Validation Table**:

| File Type | File Name | Extension | Has Content | Block Count | Content Length | Status |
|-----------|-----------|-----------|-------------|-------------|----------------|--------|
| TypeScript | calculator.ts | .ts | Required | 1+ | 100+ | [ ] |
| Python | analyzer.py | .py | Required | 1+ | 100+ | [ ] |
| JSON | config.json | .json | Required | 1+ | 50+ | [ ] |
| CSS | styles.css | .css | Required | 1+ | 50+ | [ ] |
| Markdown | README.md | .md | Required | 1+ | 100+ | [ ] |
| Text | sample.txt | .txt | Required | 1+ | 20+ | [ ] |
| YAML | design.yaml | .yaml | Required | 1+ | 50+ | [ ] |
| Large | large-file.md | .md | Required | 1+ | 5000+ | [ ] |
| Empty | empty.txt | .txt | Optional | 0-1 | 0-10 | [ ] |
| Unicode | unicode.md | .md | Required | 1+ | 50+ | [ ] |

### Task 3: Content Quality Validation

For each critical file type, verify content integrity:

**Script**:
```bash
#!/bin/bash
# File: verify-content-quality.sh

FILES=(
  "calculator.ts"
  "analyzer.py"
  "config.json"
  "unicode.md"
  "large-file.md"
)

for file in "${FILES[@]}"; do
  echo "Validating: $file"

  docker exec docker-compose-pipeshub-ai-1 python3 << EOF
import json
from app.connectors.core.base.db.arango_service import ArangoService
from app.config.arango_config import get_arango_config

# Find test file in mounted volume
import os
test_file_path = None
for root, dirs, files in os.walk('/data/pipeshub/test-files'):
    if '$file' in files:
        test_file_path = os.path.join(root, '$file')
        break

if not test_file_path:
    print("SKIP: File not found in test-files")
    exit(0)

# Read source
with open(test_file_path, 'r', encoding='utf-8') as f:
    source = f.read()

# Query database
config = get_arango_config()
service = ArangoService(config)
query = f"""
FOR doc IN records
FILTER CONTAINS(doc.externalRecordId, '$file')
RETURN doc.blockContainers.blocks[0].data
"""
results = service.execute_query(query)

if not results:
    print("FAIL: No database record found")
    exit(1)

db_content = results[0]

# Compare
if source == db_content:
    print("PASS: Content matches")
elif source.strip() == db_content.strip():
    print("PASS: Content matches (whitespace differences)")
else:
    print(f"FAIL: Content mismatch (source: {len(source)} bytes, db: {len(db_content)} bytes)")
    print(f"Source preview: {source[:100]}")
    print(f"DB preview: {db_content[:100]}")
EOF
done
```

**Unicode Test**:
```python
# Special check for Unicode preservation
query = """
FOR doc IN records
FILTER CONTAINS(doc.externalRecordId, "unicode.md")
RETURN doc.blockContainers.blocks[0].data
"""

content = service.execute_query(query)[0]

# Verify UTF-8 characters preserved
test_chars = ['é', 'ñ', '中', '日', '🚀']
for char in test_chars:
    if char in content:
        print(f"PASS: Unicode '{char}' preserved")
    else:
        print(f"FAIL: Unicode '{char}' missing")
```

**Large File Test**:
```python
# Verify large file not truncated
query = """
FOR doc IN records
FILTER CONTAINS(doc.externalRecordId, "large-file.md")
RETURN {
  blockCount: LENGTH(doc.blockContainers.blocks),
  contentLength: LENGTH(doc.blockContainers.blocks[0].data),
  preview: SUBSTRING(doc.blockContainers.blocks[0].data, 0, 100),
  ending: SUBSTRING(doc.blockContainers.blocks[0].data, -100)
}
"""

result = service.execute_query(query)[0]
print(f"Large file: {result['contentLength']} bytes in {result['blockCount']} blocks")

# Check for truncation indicators
if result['contentLength'] < 1000:
    print("WARNING: Large file may be truncated")
```
</validation_tasks>

<success_criteria>
- All 12 records have blockContainers: Query shows `{ hasContent: true, count: 12 }`
- All content matches source files: Content comparison passes for all critical files
- Unicode properly preserved: All Unicode test characters present in database
- Large files handled correctly: No truncation, full content stored
- Empty files handled gracefully: Empty file has 0 or minimal blocks
- No serialization artifacts: No Python object references, all valid JSON
</success_criteria>

<estimated_time>30 minutes</estimated_time>

<failure_scenarios>
**If records exist but have no content**:
- Cause: Existing records created before fix applied
- Fix: Re-trigger sync to update records with content
- Command: Delete and re-sync, or trigger update for specific files

**If content truncated for large files**:
- Cause: May hit content size limits in connector or ArangoDB
- Investigation: Check connector content_max_size configuration
- Decision: May need to implement chunking or skip very large files

**If Unicode corrupted**:
- Cause: Encoding issues in file read or database write
- Investigation: Check file reading encoding in connector
- Fix: Ensure UTF-8 encoding throughout pipeline
</failure_scenarios>
</phase>

## Phase 4: Full Testing Suite

<phase id="phase-4" name="Execute Comprehensive Tests">
<objective>Run 9 critical tests from original test plan to ensure no regressions and full functionality</objective>

<test_execution>
**Tests from**: `.prompts/010-connector-missing-content-test/TEST-COMMANDS.md`

### Smoke Tests (Must Pass)

**Test 1: Basic Content Extraction**
```bash
# Create simple text file
echo "Simple test content" > /data/pipeshub/test-files/smoke-test-1.txt

# Wait for sync or trigger
# ...

# Verify
docker exec docker-compose-pipeshub-ai-1 python3 -c "
from app.connectors.core.base.db.arango_service import ArangoService
from app.config.arango_config import get_arango_config

service = ArangoService(get_arango_config())
query = '''
FOR doc IN records
FILTER CONTAINS(doc.externalRecordId, \"smoke-test-1.txt\")
RETURN doc.blockContainers.blocks[0].data
'''
result = service.execute_query(query)
assert result[0] == 'Simple test content', f'Expected content not found: {result}'
print('PASS: Basic extraction works')
"
```

**Test 2: Multiple File Types**
```bash
# Test .txt, .md, .json, .py, .ts files all extract correctly
# (Already covered in Phase 3 validation)
```

**Test 3: Large File Handling**
```bash
# Create 1MB test file
python3 -c "print('x' * 1000000)" > /data/pipeshub/test-files/large-1mb.txt

# Verify full content stored
docker exec docker-compose-pipeshub-ai-1 python3 -c "
from app.connectors.core.base.db.arango_service import ArangoService
from app.config.arango_config import get_arango_config

service = ArangoService(get_arango_config())
query = '''
FOR doc IN records
FILTER CONTAINS(doc.externalRecordId, \"large-1mb.txt\")
RETURN LENGTH(doc.blockContainers.blocks[0].data)
'''
result = service.execute_query(query)
assert result[0] >= 1000000, f'Large file truncated: {result[0]} bytes'
print(f'PASS: Large file stored completely ({result[0]} bytes)')
"
```

### Functional Tests

**Test 4: Unicode Preservation**
```bash
# Create file with various Unicode characters
cat > /data/pipeshub/test-files/unicode-test.txt << 'EOF'
English: Hello World
Spanish: Hola Mundo - café, niño
French: Bonjour le monde - élève, français
Chinese: 你好世界
Japanese: こんにちは世界
Emoji: 🚀 🌟 💻 📄
Mathematical: ∑ ∫ ∂ ∞ ≠ ≈
EOF

# Verify all characters preserved
docker exec docker-compose-pipeshub-ai-1 python3 -c "
from app.connectors.core.base.db.arango_service import ArangoService
from app.config.arango_config import get_arango_config

service = ArangoService(get_arango_config())
query = '''
FOR doc IN records
FILTER CONTAINS(doc.externalRecordId, \"unicode-test.txt\")
RETURN doc.blockContainers.blocks[0].data
'''
content = service.execute_query(query)[0]

test_strings = ['café', '你好', 'こんにちは', '🚀', '∑']
for s in test_strings:
    assert s in content, f'Unicode string missing: {s}'
print('PASS: All Unicode preserved')
"
```

**Test 5: Binary File Handling**
```bash
# Verify binary files are skipped or handled appropriately
# (System should skip binary files or handle them gracefully)
dd if=/dev/urandom of=/data/pipeshub/test-files/binary.bin bs=1024 count=1

# Check that either:
# a) File is skipped (no record), OR
# b) File has record but no content extraction (acceptable)
```

**Test 6: Empty File Handling**
```bash
touch /data/pipeshub/test-files/empty-test.txt

# Verify empty file doesn't cause errors
docker exec docker-compose-pipeshub-ai-1 python3 -c "
from app.connectors.core.base.db.arango_service import ArangoService
from app.config.arango_config import get_arango_config

service = ArangoService(get_arango_config())
query = '''
FOR doc IN records
FILTER CONTAINS(doc.externalRecordId, \"empty-test.txt\")
RETURN {
  exists: true,
  hasBlocks: doc.blockContainers != null,
  blockCount: doc.blockContainers ? LENGTH(doc.blockContainers.blocks) : 0
}
'''
result = service.execute_query(query)
assert len(result) > 0, 'Empty file record should exist'
print('PASS: Empty file handled gracefully')
"
```

**Test 7: File Extension Accuracy**
```bash
# Verify extension field correctly populated
docker exec docker-compose-pipeshub-ai-1 python3 -c "
from app.connectors.core.base.db.arango_service import ArangoService
from app.config.arango_config import get_arango_config

service = ArangoService(get_arango_config())

# Test various extensions
test_files = {
    'calculator.ts': 'ts',
    'analyzer.py': 'py',
    'config.json': 'json',
    'styles.css': 'css'
}

for filename, expected_ext in test_files.items():
    query = f'''
    FOR doc IN records
    FILTER CONTAINS(doc.recordName, \"{filename}\")
    RETURN {{
      name: doc.recordName,
      extension: doc.extension
    }}
    '''
    result = service.execute_query(query)
    if result:
        assert result[0]['extension'] == expected_ext, f'Wrong extension for {filename}'
print('PASS: Extensions correct')
"
```

### Integration Tests

**Test 8: Search Functionality**
```bash
# Create searchable content
cat > /data/pipeshub/test-files/search-test.md << 'EOF'
# Important Document

This document contains **critical information** about the project.

Key points:
- Feature A is implemented
- Feature B is pending
- Bug #123 needs attention
EOF

# Verify content is searchable via ArangoDB text search
docker exec docker-compose-pipeshub-ai-1 python3 -c "
from app.connectors.core.base.db.arango_service import ArangoService
from app.config.arango_config import get_arango_config

service = ArangoService(get_arango_config())

# Search for keyword in content
query = '''
FOR doc IN records
FILTER doc.blockContainers != null
  AND CONTAINS(doc.blockContainers.blocks[0].data, \"critical information\")
RETURN doc.recordName
'''
result = service.execute_query(query)
assert 'search-test.md' in str(result), 'Search failed to find content'
print('PASS: Content is searchable')
"
```

**Test 9: Content Indexing**
```bash
# Verify indexing service can access content
# (This may require checking indexing service logs or Qdrant)

# Check that records with content trigger indexing
docker logs docker-compose-pipeshub-ai-1 2>&1 | grep -i "indexing.*search-test.md"

# If indexing service is running, should see:
# "Processing record for indexing: search-test.md"
# "Content extracted: 123 characters"
# etc.
```
</test_execution>

<success_criteria>
- All 9 tests pass: Each test completes without assertion errors
- No regressions in existing functionality: File metadata still correct (name, extension, size)
- Performance acceptable: Query response times < 500ms for single record
- No errors in logs: Container logs show no exceptions during test execution
</success_criteria>

<estimated_time>45 minutes (including test setup and execution)</estimated_time>

<failure_handling>
**If Test 3 (Large Files) fails**:
- Check connector content size limits
- May need to implement chunking or max size configuration
- Document limitation if truly large files (>10MB) cause issues

**If Test 4 (Unicode) fails**:
- Check file reading encoding in connector
- Verify ArangoDB UTF-8 support
- May need to add explicit encoding handling

**If Test 8 (Search) fails**:
- Verify ArangoDB text search configuration
- Check if full-text indexing needed
- May be limitation of query approach, not persistence issue

**If Test 9 (Indexing) fails**:
- Indexing service may need updates to consume from blockContainers
- Check if indexing still using old content fetch method
- May require Phase 6 (Indexing Integration) as follow-up work
</failure_handling>
</phase>

## Phase 5: Final Sign-Off

<phase id="phase-5" name="Done-Done-Done Confirmation">
<objective>Final validation and documentation to confirm system is production-ready</objective>

<final_checks>
### 1. End-to-End Test
**Action**: Create brand new file and verify full pipeline

```bash
# Create unique test file
TIMESTAMP=$(date +%s)
echo "End-to-end test at $TIMESTAMP" > /data/pipeshub/test-files/e2e-test-$TIMESTAMP.txt

# Wait for sync (or trigger)
sleep 10

# Query and verify
docker exec docker-compose-pipeshub-ai-1 python3 -c "
from app.connectors.core.base.db.arango_service import ArangoService
from app.config.arango_config import get_arango_config

service = ArangoService(get_arango_config())
query = '''
FOR doc IN records
FILTER CONTAINS(doc.externalRecordId, \"e2e-test-$TIMESTAMP.txt\")
RETURN {
  name: doc.recordName,
  hasContent: doc.blockContainers != null,
  content: doc.blockContainers.blocks[0].data
}
'''
result = service.execute_query(query)
assert len(result) > 0, 'E2E test record not found'
assert result[0]['hasContent'], 'E2E test has no content'
assert 'End-to-end test' in result[0]['content'], 'E2E content mismatch'
print('PASS: End-to-end pipeline working')
"
```

**Expected**: File created → synced → content extracted → persisted → queryable

### 2. Performance Check
**Action**: Measure query response times

```python
import time
from app.connectors.core.base.db.arango_service import ArangoService
from app.config.arango_config import get_arango_config

service = ArangoService(get_arango_config())

# Test 1: Single record with content
start = time.time()
query = """
FOR doc IN records
FILTER doc._key == "some-known-id"
RETURN doc
"""
result = service.execute_query(query)
duration_ms = (time.time() - start) * 1000
print(f"Single record query: {duration_ms:.2f}ms")
assert duration_ms < 500, "Query too slow"

# Test 2: List records without content
start = time.time()
query = """
FOR doc IN records
FILTER doc.connectorName == "LOCAL_FILESYSTEM"
LIMIT 10
RETURN {
  name: doc.recordName,
  type: doc.recordType
}
"""
result = service.execute_query(query)
duration_ms = (time.time() - start) * 1000
print(f"List query (10 records, no content): {duration_ms:.2f}ms")
assert duration_ms < 200, "List query degraded"

# Test 3: Search in content
start = time.time()
query = """
FOR doc IN records
FILTER doc.blockContainers != null
  AND CONTAINS(doc.blockContainers.blocks[0].data, "test")
LIMIT 10
RETURN doc.recordName
"""
result = service.execute_query(query)
duration_ms = (time.time() - start) * 1000
print(f"Content search: {duration_ms:.2f}ms")
# Note: May be slower, acceptable if < 2000ms
```

**Expected**:
- Single record: < 500ms
- List query: < 200ms (should not be affected by content storage)
- Content search: < 2000ms (depends on dataset size)

### 3. Documentation Updates
**Action**: Update relevant documentation

Files to update:
- `/backend/python/README.md` - Note about block_containers persistence
- `.prompts/009-connector-missing-content-fix/SUMMARY.md` - Mark as resolved
- `.prompts/003-content-extraction-validation-do/SUMMARY.md` - Update with completion
- Create migration guide for other connectors (optional)

### 4. Known Issues Documentation
**Action**: Document any limitations discovered

```markdown
## Known Limitations (Block Containers)

1. **Existing Records**: Records created before fix do NOT have content
   - Workaround: Re-sync to populate content
   - Impact: Historical data incomplete

2. **Large Files**: Files > 10MB may impact query performance
   - Consideration: May want to exclude very large files from content extraction
   - Mitigation: Configure content_max_size in connector

3. **Binary Files**: Binary files are [skipped/handled differently]
   - Expected behavior: Only text-extractable files get content

4. **Indexing Service**: May need updates to consume from blockContainers
   - Status: TBD in follow-up work
   - Current: May still fetch from source
```
</final_checks>

<sign_off_criteria>
- Content extraction working end-to-end: New files have content in database
- Database persistence confirmed: blockContainers field present and populated
- Queries return content successfully: Can retrieve and search content
- All critical tests passing: 9/9 tests pass
- No known blockers: All issues documented with workarounds
- System production-ready: Performance acceptable, no critical bugs
- Documentation updated: README and summaries reflect new capability
</sign_off_criteria>

<estimated_time>15 minutes</estimated_time>

<post_deployment_monitoring>
**Week 1 Monitoring**:
- Watch ArangoDB database size growth
- Monitor query performance metrics
- Check connector sync success rates
- Review any content extraction errors

**Metrics to Track**:
- % of records with blockContainers field
- Average content size per record
- Query latency (p50, p95, p99)
- Disk usage trend
</post_deployment_monitoring>
</phase>

## Decisions Required

<decision id="decision-1">
<question>Should we store block_containers in ArangoDB or implement a separate content storage mechanism?</question>

<context>
ArangoDB is a graph database optimized for relationships, not large text storage. However, for immediate fix and simplicity, storing content in ArangoDB is the fastest path. Long-term, a separate content store might be more scalable.
</context>

<options>
  <option id="A">
    <description>Store in ArangoDB (recommended for immediate fix)</description>
    <pros>
      - Simple implementation (just add field to serialization)
      - No architectural changes needed
      - Content immediately available for queries
      - Works with existing ArangoDB infrastructure
      - Fixes the issue for all 12 test files immediately
    </pros>
    <cons>
      - May impact query performance for large content
      - Increases ArangoDB storage requirements
      - Not optimal for very large files (>10MB)
      - Duplicates storage if content also in vector DB
    </cons>
    <effort>Low (2-3 hours total)</effort>
    <risk>Low - minimal code changes, easy to rollback</risk>
  </option>

  <option id="B">
    <description>Implement separate content store (e.g., S3, dedicated content collection)</description>
    <pros>
      - Better separation of concerns (metadata vs content)
      - Scalable for large files
      - Can optimize storage separately (compression, tiering)
      - Cleaner architecture long-term
    </pros>
    <cons>
      - Significant development effort (days not hours)
      - Requires new infrastructure (S3 bucket, service)
      - More complex queries (join metadata + content)
      - Delays fixing the immediate issue
      - Requires indexing service integration
    </cons>
    <effort>High (2-3 days)</effort>
    <risk>Medium - architectural change, more testing needed</risk>
  </option>

  <option id="C">
    <description>Hybrid: Store in ArangoDB for now, plan migration later</description>
    <pros>
      - Quick fix (Option A) unblocks validation immediately
      - Can design proper architecture in parallel
      - Allows testing to proceed while planning long-term solution
      - Minimal risk for current need
    </pros>
    <cons>
      - Creates technical debt (will need migration later)
      - May need to re-architect after testing completes
      - Potential wasted effort if architecture changes significantly
    </cons>
    <effort>Low now (2-3 hours), High later (2-3 days for migration)</effort>
    <risk>Low immediate, Medium long-term (migration complexity)</risk>
  </option>
</options>

<recommendation>Option A (Store in ArangoDB)</recommendation>

<rationale>
For the immediate goal of completing content extraction validation and unblocking testing, storing in ArangoDB is the clear choice:
1. Fixes the problem in 2-3 hours vs days
2. Allows validation workflow to complete
3. Minimal risk - easy to rollback if issues
4. Test files are small-medium size (< 1MB typically)
5. Can always migrate to separate storage later if needed

The research shows this is a new feature (only local_filesystem uses it), so there's no urgent need for production-scale architecture. Get it working first, optimize later if performance issues arise.
</rationale>

<approval_needed>No - proceeding with Option A based on project constraints and research findings</approval_needed>
</decision>

<decision id="decision-2">
<question>Should we modify FileRecord.to_arango_record() or only Record.to_arango_base_record()?</question>

<context>
Records are stored in two collections: 'records' (base metadata) and 'files' (file-specific metadata). We need to decide where to store block_containers.
</context>

<options>
  <option id="A">
    <description>Only modify Record.to_arango_base_record() (recommended)</description>
    <pros>
      - Avoids duplication (content stored once)
      - Follows single source of truth principle
      - 'records' collection is queried for content searches
      - Simpler data model
    </pros>
    <cons>
      - Content not in 'files' collection (might be expected)
    </cons>
    <effort>Low</effort>
    <risk>Low</risk>
  </option>

  <option id="B">
    <description>Modify both methods (store in both collections)</description>
    <pros>
      - Content available from both collections
      - More redundancy
    </pros>
    <cons>
      - Duplicates storage (wastes space)
      - Inconsistency risk if one update fails
      - Against DRY principle
    </cons>
    <effort>Low</effort>
    <risk>Medium (data consistency issues)</risk>
  </option>
</options>

<recommendation>Option A - Only modify to_arango_base_record()</recommendation>

<rationale>
The 'records' collection is the base collection that all queries start from. The 'files' collection stores file-specific metadata (hashes, sizes, etc.) not content. Storing content in 'records' is sufficient and avoids duplication issues.
</rationale>

<approval_needed>No</approval_needed>
</decision>

<decision id="decision-3">
<question>How should we handle empty block_containers?</question>

<context>
Some files may have no extractable content (empty files, binary files, etc.). We need to decide whether to store empty block_containers or omit the field entirely.
</context>

<options>
  <option id="A">
    <description>Conditionally include field only if content exists (recommended)</description>
    <pros>
      - Saves storage for records without content
      - Cleaner data model (no empty objects)
      - Easier to query (field presence = has content)
    </pros>
    <cons>
      - Queries must check for field existence
      - Inconsistent schema (some records have field, some don't)
    </cons>
    <effort>Low (add conditional in serialization)</effort>
    <risk>Low</risk>
  </option>

  <option id="B">
    <description>Always include field, use empty array for no content</description>
    <pros>
      - Consistent schema (all records have field)
      - Simpler queries (no null checks)
    </pros>
    <cons>
      - Wastes storage on empty objects
      - Less semantic (presence doesn't indicate content)
    </cons>
    <effort>Low</effort>
    <risk>Low</risk>
  </option>
</options>

<recommendation>Option A - Conditional inclusion</recommendation>

<rationale>
ArangoDB is schema-less, so inconsistent field presence is acceptable and expected. Conditional inclusion:
1. Saves storage (important if scaling)
2. Makes "has content" queries simpler: `doc.blockContainers != null`
3. Follows the pattern already in use (signed_url is optional)
</rationale>

<approval_needed>No</approval_needed>
</decision>

## Risk Management

### Risk 1: Query Performance Degradation

**Probability**: Medium

**Impact**: Medium

**Mitigation**:
- Include only essential content (exclude very large files > 10MB)
- Use projections in queries (don't fetch content unless needed)
- Monitor query latency before/after deployment
- Add database indexes if needed

**Contingency**:
- If queries slow down significantly:
  1. Add content size limit in connector configuration
  2. Exclude large files from content extraction
  3. Consider separating content to different collection
  4. Roll back if critical performance impact

### Risk 2: Database Storage Explosion

**Probability**: Low

**Impact**: Medium

**Mitigation**:
- Start with test files only (small dataset)
- Monitor database size growth
- Set connector content_max_size limit
- Document storage requirements

**Contingency**:
- If storage grows too fast:
  1. Reduce content_max_size limit
  2. Implement content compression
  3. Archive old content
  4. Move to separate storage

### Risk 3: JSON Serialization Errors

**Probability**: Low

**Impact**: High (blocks entire fix)

**Mitigation**:
- Use Pydantic's `model_dump(mode='json')` for proper serialization
- Test with diverse content (Unicode, special characters)
- Add error handling for serialization failures
- Validate JSON structure in Phase 2

**Contingency**:
- If serialization fails:
  1. Check Block model for non-serializable fields
  2. Add custom serializers for specific metadata types
  3. Fall back to basic text-only blocks if needed
  4. Document unsupported content types

### Risk 4: Indexing Service Incompatibility

**Probability**: Medium

**Impact**: Medium

**Mitigation**:
- Check indexing service logs in Phase 5
- Verify content is accessible for indexing
- Document if indexing needs updates
- Plan follow-up work if needed

**Contingency**:
- If indexing can't consume block_containers:
  1. Document as known limitation
  2. Keep existing content fetch mechanism for indexing
  3. Schedule indexing service update as Phase 6
  4. Both paths work in parallel (migration period)

### Risk 5: Breaking Changes to Existing Queries

**Probability**: Low

**Impact**: Medium

**Mitigation**:
- New field is additive (doesn't change existing fields)
- Conditional inclusion (backward compatible)
- Test that existing queries still work
- No schema changes required (ArangoDB is schema-less)

**Contingency**:
- If existing queries break:
  1. Identify which queries are affected
  2. Update queries to handle optional field
  3. Add null checks where needed
  4. Document migration guide for custom queries

## Rollback Plan

### Trigger Conditions

Rollback if:
- Code change causes container build failures
- Serialization errors prevent record creation
- Performance degrades by > 50% (query latency doubles)
- Data corruption detected (content mismatch)
- Critical functionality broken (cannot create records)
- Unable to verify fix works after 2 attempts

### Rollback Procedure

**Step 1: Stop Services**
```bash
cd /Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/deployment/docker-compose
docker-compose stop pipeshub-ai
```

**Step 2: Restore Code**
```bash
cd /Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig
git checkout backend/python/app/models/entities.py
git status  # Verify clean
```

**Step 3: Rebuild Container**
```bash
cd deployment/docker-compose
docker-compose build pipeshub-ai
```

**Step 4: Restart Services**
```bash
docker-compose up -d pipeshub-ai
docker-compose ps  # Verify running
```

**Step 5: Verify Rollback**
```bash
# Check that original code is active
docker exec docker-compose-pipeshub-ai-1 python3 -c "
from app.models.entities import Record
import inspect
source = inspect.getsource(Record.to_arango_base_record)
# Should NOT contain 'blockContainers'
assert 'blockContainers' not in source, 'Rollback failed - new code still present'
print('SUCCESS: Rollback complete, original code active')
"

# Verify basic functionality still works
docker exec docker-compose-pipeshub-ai-1 python3 -c "
from app.models.entities import FileRecord, RecordType
from app.config.constants.arangodb import Connectors, OriginTypes
record = FileRecord(
    record_name='rollback-test',
    record_type=RecordType.FILE,
    external_record_id='test',
    connector_name=Connectors.LOCAL_FILESYSTEM,
    origin=OriginTypes.CONNECTOR,
    version=1,
    org_id='test',
    is_file=True,
    size_in_bytes=100
)
result = record.to_arango_base_record()
print('SUCCESS: Record serialization working')
"
```

**Step 6: Document Rollback Reason**
```bash
# Create rollback report
cat > .prompts/005-block-containers-persistence-plan/ROLLBACK-REPORT.md << 'EOF'
# Rollback Report

**Date**: $(date)
**Reason**: [Describe what went wrong]
**Phase**: [Which phase triggered rollback]
**Error**: [Exact error message or issue]

## Investigation Required
- [ ] Reproduce issue in isolated environment
- [ ] Identify root cause
- [ ] Test alternative implementation
- [ ] Update plan with lessons learned

## Next Steps
[What to do differently on next attempt]
EOF
```

**Step 7: Restore Database (if needed)**
```bash
# Only if database corruption detected
# Restore from Phase 0 backup
docker exec docker-compose-arangodb-1 arangoimport \
  --file /backup/backup-TIMESTAMP.json \
  --collection records \
  --create-collection false \
  --overwrite true
```

### Rollback Verification Checklist

After rollback:
- [ ] Container builds successfully
- [ ] Services start without errors
- [ ] Original code is active (verified via inspection)
- [ ] Basic record creation works
- [ ] No errors in logs
- [ ] Database queries work
- [ ] Connector can sync files
- [ ] No data corruption

## Timeline

**Total Estimated Time**: 2-3 hours

| Phase | Duration | Dependencies | Can Run in Parallel |
|-------|----------|--------------|---------------------|
| Phase 0: Preparation | 15 min | None | No |
| Phase 1: Implementation | 30 min | Phase 0 | No (includes 5-min rebuild) |
| Phase 2: Immediate Verification | 15 min | Phase 1 | No |
| Phase 3: Comprehensive Validation | 30 min | Phase 2 | Partially (queries can run parallel) |
| Phase 4: Full Testing | 45 min | Phase 3 | Yes (tests can run parallel) |
| Phase 5: Sign-Off | 15 min | Phase 4 | No |

**Critical Path**: Phase 0 → Phase 1 → Phase 2 (minimum 1 hour to verify basic fix)

**Parallel Opportunities**:
- Phase 3 queries can run in parallel (multiple file type checks simultaneously)
- Phase 4 tests can be executed concurrently (smoke tests, functional tests, integration tests)

**Blocking Points**:
- Container rebuild in Phase 1 (cannot proceed until build completes)
- Sync trigger in Phase 2 (must wait for connector to process file)
- Each phase must complete successfully before next can start

## Success Metrics

**Minimum for Success**:
- blockContainers field persists to ArangoDB: Field present in database records
- At least 1 test record queryable with content: Query returns content for verification file
- Content matches source file: Byte-for-byte identical
- No errors in persistence path: Logs show successful serialization and storage

**Complete Success** (Done-Done-Done):
- All 12 test files have persisted content: Query shows 12/12 with blockContainers
- All 9 critical tests pass: Each test completes without errors
- Content queryable and usable: Can search within content via AQL
- Performance acceptable: Queries complete in < 2 seconds
- System production-ready: No known critical bugs, limitations documented
- Original validation workflow complete: Can proceed to Phase 3 and Phase 4 of original validation plan

**Quantitative Metrics**:
- Content persistence rate: 100% of text files have content
- Query success rate: 100% of queries return expected results
- Performance: < 500ms for single record, < 2000ms for content search
- Data integrity: 100% match between source files and database content
- Test pass rate: 9/9 tests pass (100%)

## Metadata

<confidence>High (90%)</confidence>

**Confidence Justification**:
- Root cause definitively identified through research (95% confidence)
- Fix is simple and low-risk (add field to serialization method)
- Similar patterns exist in codebase (proven approach)
- Pydantic model_dump() verified working in container tests
- Only uncertainty is potential indexing service compatibility (addressed as follow-up)

<dependencies>
**From Research**:
- Root cause: Custom serialization methods exclude block_containers (entities.py:90-116)
- Architectural understanding: ArangoDB stores metadata, content is new addition
- Connector working: local_filesystem successfully extracts content
- Pydantic serialization: model_dump(mode='json') produces correct output

**External**:
- Docker access for rebuild: Required for Phase 1
- ArangoDB write access: Required for all phases
- Ability to restart services: Required for Phase 1
- Test files exist: Required for validation (/data/pipeshub/test-files/)
- Python 3.9+ in container: Required for Pydantic serialization
</dependencies>

<open_questions>
1. **Indexing service integration**: Does indexing need updates to read from blockContainers?
   - Answer: TBD in Phase 5 testing
   - Impact: May require follow-up work (Phase 6) to fully integrate
   - Mitigation: Document current state, plan future work if needed

2. **Performance at scale**: Will content storage impact query performance with 1000+ records?
   - Answer: Monitor in production after deployment
   - Impact: May need optimization (indexes, projections)
   - Mitigation: Start with small dataset, measure before scaling

3. **Content size limits**: What's the practical limit for content size in ArangoDB?
   - Answer: Test with increasingly large files in Phase 4
   - Impact: May need to exclude very large files
   - Mitigation: Configure content_max_size in connector

4. **Other connectors**: Should Google Drive, OneDrive, etc. adopt this pattern?
   - Answer: Depends on content accessibility and rate limits
   - Impact: Architectural decision for future connector development
   - Mitigation: Document pattern, evaluate per connector
</open_questions>

<assumptions>
1. **ArangoDB is schema-less**: Verified - can add fields without migration
2. **Pydantic model_dump() works**: Verified in container experiments
3. **Test files accessible**: Assumed based on previous validation work
4. **BlocksContainer serializes to JSON**: Verified - Pydantic BaseModel
5. **Connector sync triggers available**: Assumed - or can create test files manually
</assumptions>

<blockers>
None - ready to execute

**All prerequisites met**:
- Code location identified
- Fix approach validated
- Test environment available
- No external dependencies blocking
</blockers>

<next_steps>
1. **Execute Phase 0**: Backup database, create git branch, document baseline
2. **Execute Phase 1**: Apply code change to entities.py, rebuild container, restart services
3. **Execute Phase 2**: Create test file, trigger sync, verify content persists
4. **Execute Phase 3**: Validate all 12 test files have content
5. **Execute Phase 4**: Run 9 critical tests from test plan
6. **Execute Phase 5**: Final sign-off, documentation, production readiness
7. **Follow-up (if needed)**: Phase 6 - Indexing service integration with blockContainers
</next_steps>

## References

**Research Documents**:
- `.prompts/004-block-containers-persistence-research/block-containers-persistence-research.md` - Root cause analysis
- `.prompts/004-block-containers-persistence-research/SUMMARY.md` - Executive summary

**Code Files**:
- `/backend/python/app/models/entities.py` - Record model with serialization methods
- `/backend/python/app/models/blocks.py` - BlocksContainer and Block models
- `/backend/python/app/connectors/sources/local_filesystem/connector.py` - Content extraction
- `/backend/python/app/connectors/core/base/data_store/arango_data_store.py` - Persistence layer

**Test Resources**:
- `.prompts/010-connector-missing-content-test/TEST-COMMANDS.md` - Test suite
- `.prompts/003-content-extraction-validation-do/` - Original validation plan
- `/data/pipeshub/test-files/` - Test file directory

**Configuration**:
- `/deployment/docker-compose/docker-compose.yml` - Container orchestration
- `/backend/python/app/config/arango_config.py` - ArangoDB configuration
