# Test Commands Reference

Quick reference for all commands needed during testing.

## Environment Variables

```bash
# ArangoDB credentials
ARANGO_USER="root"
ARANGO_PASS="czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm"
ARANGO_URL="http://localhost:8529"
DB_NAME="es"
ORG_ID="6928ff5506880ac843ef5a3c"
```

## Docker Commands

### Check Container Status
```bash
docker ps --filter "name=pipeshub-ai"
```

### View Logs
```bash
# All logs
docker logs -f pipeshub-ai

# Content extraction logs
docker logs pipeshub-ai 2>&1 | grep -i "content extraction\|content loaded\|_read_file_content"

# Connector initialization
docker logs pipeshub-ai 2>&1 | grep -i "local filesystem.*initialized"

# Recent sync activity
docker logs pipeshub-ai 2>&1 | grep -i "sync completed" | tail -20
```

### Access Container
```bash
docker exec -it pipeshub-ai bash
```

### List Test Files (inside container)
```bash
docker exec pipeshub-ai find /data/pipeshub/test-files -type f -exec ls -lh {} \;
```

### Read Test File Content
```bash
docker exec pipeshub-ai cat /data/pipeshub/test-files/source-code/app.ts
```

## ArangoDB Queries

### Helper Function
```bash
# Save this function for easy querying
aql() {
  local query="$1"
  curl -s -u "$ARANGO_USER:$ARANGO_PASS" \
    -X POST "$ARANGO_URL/_db/$DB_NAME/_api/cursor" \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$query\"}" \
    | python3 -m json.tool
}
```

### Test 1: Basic Content Extraction
```bash
# Query: Check if app.ts was synced with content
cat > /tmp/test1.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.recordName == 'app.ts' AND doc.connectorName == 'LOCAL_FILESYSTEM' RETURN {recordName: doc.recordName, extension: doc.extension, filePath: doc.path, fileSize: doc.sizeInBytes, hasContent: doc.blockContainers != null AND LENGTH(doc.blockContainers.blocks) > 0, contentPreview: doc.blockContainers.blocks[0] != null ? SUBSTRING(doc.blockContainers.blocks[0].data, 0, 100) : null}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/test1.json | python3 -m json.tool
```

### Test 2: Multiple File Types
```bash
# Query: Check all test files by extension
cat > /tmp/test2.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == 'LOCAL_FILESYSTEM' AND doc.recordName IN ['app.ts', 'config.json', 'utils.py', 'styles.css', 'README.md', 'notes.txt', 'design.yaml', 'unicode.txt', 'empty.txt', 'large-file.md', '.hidden.ts', 'file with spaces.md'] COLLECT extension = doc.extension, hasContent = (doc.blockContainers != null AND LENGTH(doc.blockContainers.blocks) > 0) WITH COUNT INTO count RETURN {extension, hasContent, count}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/test2.json | python3 -m json.tool
```

### Test 3: Large File Handling
```bash
# Query: Check large-file.md (127 KB)
cat > /tmp/test3.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.recordName == 'large-file.md' AND doc.connectorName == 'LOCAL_FILESYSTEM' RETURN {recordName: doc.recordName, fileSize: doc.sizeInBytes, hasContent: doc.blockContainers != null AND LENGTH(doc.blockContainers.blocks) > 0, contentLength: doc.blockContainers.blocks[0] != null ? LENGTH(doc.blockContainers.blocks[0].data) : 0}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/test3.json | python3 -m json.tool
```

### Test 4: Encoding Detection (Unicode)
```bash
# Query: Check unicode.txt content
cat > /tmp/test4.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.recordName == 'unicode.txt' AND doc.connectorName == 'LOCAL_FILESYSTEM' RETURN {recordName: doc.recordName, hasContent: doc.blockContainers != null AND LENGTH(doc.blockContainers.blocks) > 0, contentPreview: doc.blockContainers.blocks[0] != null ? SUBSTRING(doc.blockContainers.blocks[0].data, 0, 200) : null}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/test4.json | python3 -m json.tool
```

### Test 6: Full Directory Sync
```bash
# Query: Count all test files synced
cat > /tmp/test6.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == 'LOCAL_FILESYSTEM' AND CONTAINS(doc.filePath, 'test-files') COLLECT hasContent = (doc.blockContainers != null AND LENGTH(doc.blockContainers.blocks) > 0), hasExtension = (doc.extension != null AND doc.extension != ''), hasPath = (doc.path != null), hasSize = (doc.sizeInBytes != null) WITH COUNT INTO count RETURN {hasContent, hasExtension, hasPath, hasSize, count}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/test6.json | python3 -m json.tool
```

### Test 8: Record Group Association
```bash
# Query: Verify directory structure preserved
cat > /tmp/test8.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.recordName == 'app.ts' AND doc.connectorName == 'LOCAL_FILESYSTEM' LET group = FIRST(FOR g IN recordGroups FILTER g._key == doc.recordGroupId RETURN g) RETURN {file: doc.recordName, group: group.groupName, path: doc.path}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/test8.json | python3 -m json.tool
```

### Test 13: Database Impact
```bash
# Query: Average and max document sizes
cat > /tmp/test13.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == 'LOCAL_FILESYSTEM' AND doc.blockContainers != null AND LENGTH(doc.blockContainers.blocks) > 0 COLLECT AGGREGATE avgSize = AVG(LENGTH(doc.blockContainers.blocks[0].data)), maxSize = MAX(LENGTH(doc.blockContainers.blocks[0].data)), count = COUNT() RETURN {count, avgSize, maxSize}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/test13.json | python3 -m json.tool
```

### Test 14: Organization Isolation
```bash
# Query: Verify no records for old org
cat > /tmp/test14.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.orgId == '692029575c9fa18a5704d0b7' AND doc.connectorName == 'LOCAL_FILESYSTEM' COLLECT WITH COUNT INTO count RETURN count"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/test14.json | python3 -m json.tool

# Should return 0

# Query: Verify all records for correct org
cat > /tmp/test14b.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.orgId == '6928ff5506880ac843ef5a3c' AND doc.connectorName == 'LOCAL_FILESYSTEM' COLLECT WITH COUNT INTO count RETURN count"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/test14b.json | python3 -m json.tool
```

### Test 16: Edge Cases
```bash
# Query: Check edge case files
cat > /tmp/test16.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == 'LOCAL_FILESYSTEM' AND doc.recordName IN ['empty.txt', '.hidden.ts', 'file with spaces.md', 'unicode.txt'] RETURN {recordName: doc.recordName, hasContent: doc.blockContainers != null AND LENGTH(doc.blockContainers.blocks) > 0, fileSize: doc.sizeInBytes, contentSize: doc.blockContainers.blocks[0] != null ? LENGTH(doc.blockContainers.blocks[0].data) : 0}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/test16.json | python3 -m json.tool
```

### Test 17: Migration Validation
```bash
# Query: Count records with vs without content
cat > /tmp/test17.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == 'LOCAL_FILESYSTEM' COLLECT hasContent = (doc.blockContainers != null AND LENGTH(doc.blockContainers.blocks) > 0) WITH COUNT INTO count RETURN {hasContent, count}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/test17.json | python3 -m json.tool

# Expected after migration:
# {hasContent: true, count: 1680}
# {hasContent: false, count: 0}
```

## Qdrant Queries (Test 10)

### Check Collection
```bash
curl -X GET http://localhost:6333/collections/records \
  -H "Content-Type: application/json"
```

### Search for Test File
```bash
# This requires an embedding vector - would need to generate from actual content
curl -X POST http://localhost:6333/collections/records/points/scroll \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "must": [
        {"key": "recordName", "match": {"value": "app.ts"}}
      ]
    },
    "limit": 10,
    "with_payload": true,
    "with_vector": false
  }'
```

## Chat UI Testing (Test 9)

### Open Browser
```bash
open http://localhost:3000
```

### Test Queries
1. "Show me TypeScript files with export functions"
2. "Find Python utility functions"
3. "Search for CSS styling code"
4. "Show files with JSON configuration"

Expected: Should return test files with content and proper citations

## Performance Monitoring

### Measure Sync Time
```bash
# Start time
start_time=$(date +%s)

# Trigger sync (via UI or wait for auto-sync)
# Watch logs
docker logs -f pipeshub-ai | grep -i "sync completed"

# End time
end_time=$(date +%s)

# Calculate
elapsed=$((end_time - start_time))
echo "Sync duration: ${elapsed} seconds"
```

### Monitor Memory
```bash
docker stats pipeshub-ai --no-stream
```

### Monitor CPU
```bash
docker stats pipeshub-ai --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
```

## Connector Restart (Test 15)

```bash
# Restart container
docker compose -f deployment/docker-compose/docker-compose.dev.yml restart pipeshub-ai

# Watch initialization logs
docker logs -f pipeshub-ai | grep -i "content extraction\|initialized"

# Should see:
# "Content extraction: enabled=true, max_size_mb=10"
# "Local Filesystem connector initialized for: /data/local-files"
```

## Migration Commands

### Backup Existing Records
```bash
cat > /tmp/backup_query.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == 'LOCAL_FILESYSTEM' RETURN doc"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/backup_query.json \
  > "backups/local-filesystem-$(date +%Y%m%d-%H%M%S).json"
```

### Delete Records (DANGER!)
```bash
# ONLY RUN AFTER BACKUP
cat > /tmp/delete_query.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == 'LOCAL_FILESYSTEM' REMOVE doc IN records RETURN OLD._key"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/delete_query.json | python3 -m json.tool
```

### Verify Deletion
```bash
cat > /tmp/verify_delete.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == 'LOCAL_FILESYSTEM' COLLECT WITH COUNT INTO count RETURN count"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" \
  -X POST "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/verify_delete.json | python3 -m json.tool

# Should return 0
```

## Troubleshooting

### Check if Code Deployed
```bash
docker exec pipeshub-ai grep -n "Content extraction:" /app/python/app/connectors/sources/local_filesystem/connector.py

# Should show line numbers if deployed
# No output means old code still running
```

### Check chardet Installed
```bash
docker exec pipeshub-ai python3 -c "import chardet; print(chardet.__version__)"

# Should print: 5.2.0
```

### Check Test Files Exist
```bash
docker exec pipeshub-ai test -f /data/pipeshub/test-files/source-code/app.ts && echo "EXISTS" || echo "MISSING"
```

### Force Connector Sync
```bash
# Via API (if endpoint exists)
curl -X POST http://localhost:8088/api/v1/connectors/local-filesystem/sync \
  -H "Content-Type: application/json"

# Or restart connector to trigger auto-sync
docker compose -f deployment/docker-compose/docker-compose.dev.yml restart pipeshub-ai
```

---

**NOTE:** Replace `czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm` with actual ArangoDB password if different.

**TIP:** Save these commands as shell functions in `~/.bashrc` or `~/.zshrc` for easy reuse.
