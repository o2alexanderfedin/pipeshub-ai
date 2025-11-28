# Quick Start Guide: Resume Connector Content Testing

## Current Status
Testing BLOCKED at deployment phase. Test environment fully prepared and ready.

## What's Ready
1. **Test Files:** 12 files in `/data/pipeshub/test-files/` (inside Docker volume)
2. **Baseline Data:** 1,668 records with 0% content captured
3. **Test Plan:** All 17 tests documented in test report
4. **Partial Fix:** httpx dependency updated to 0.28.1

## What's Blocking
Frontend TypeScript build error:
```
error TS2307: Cannot find module '@testing-library/react'
```

## How to Unblock (15 minutes)

### Option A: Exclude Test Files (RECOMMENDED - Fastest)

1. Edit `frontend/tsconfig.json`:
```json
{
  "exclude": [
    "node_modules",
    "**/__tests__/**",
    "**/*.test.ts",
    "**/*.test.tsx"
  ]
}
```

2. Rebuild:
```bash
cd deployment/docker-compose
docker compose -f docker-compose.dev.yml build pipeshub-ai
```

### Option B: Install Missing Dependencies

1. Edit `frontend/package.json`, add to devDependencies:
```json
{
  "devDependencies": {
    "@testing-library/react": "^14.0.0",
    "vitest": "^1.0.0"
  }
}
```

2. Rebuild:
```bash
cd deployment/docker-compose
docker compose -f docker-compose.dev.yml build pipeshub-ai
```

## Deploy Updated Code (5 minutes)

```bash
cd /Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/deployment/docker-compose

# Stop current container
docker compose -f docker-compose.dev.yml down pipeshub-ai

# Start with new code
docker compose -f docker-compose.dev.yml up -d pipeshub-ai

# Verify deployment - should see "Content extraction: enabled=true"
docker logs -f pipeshub-ai | grep "Content extraction:"
```

## Run Test Suite (4-6 hours)

### Quick Verification (5 minutes)
```bash
# Trigger a manual sync (via API or wait for auto-sync)
# Then check one test file was processed:

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" -X POST \
  "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d '{
  "query": "FOR doc IN records FILTER doc.recordName == \"app.ts\" RETURN {recordName: doc.recordName, extension: doc.extension, hasContent: LENGTH(doc.blockContainers.blocks) > 0, contentPreview: SUBSTRING(doc.blockContainers.blocks[0].data, 0, 100)}"
}' | python3 -m json.tool
```

Expected result:
```json
{
  "recordName": "app.ts",
  "extension": "ts",
  "hasContent": true,
  "contentPreview": "// TypeScript Application Entry Point\nexport class Application {\n  private name: string;"
}
```

### Full Test Execution

Use the test plan in `connector-missing-content-test-report.md`:
- Test 1: Basic Content Extraction
- Test 2: Multiple File Types (12 files)
- Test 3: Large File Handling
- Test 4: Encoding Detection (Unicode file)
- Test 5: Error Scenarios
- Test 6-8: Integration tests
- Test 9-11: E2E tests (chat, search, UI)
- Test 12-13: Performance tests
- Test 14-16: Regression tests
- Test 17: Migration validation (1,668 records)

## Expected Timeline

| Task | Duration | Status |
|------|----------|--------|
| Fix frontend build | 15-30 min | PENDING |
| Rebuild Docker image | 5-10 min | PENDING |
| Deploy and restart | 5 min | PENDING |
| Quick verification | 5 min | PENDING |
| Full test suite (17 tests) | 4-6 hours | PENDING |
| Generate final report | 30 min | PENDING |
| **TOTAL** | **5-7 hours** | **PENDING** |

## Test Files Location

Inside Docker container:
```
/data/pipeshub/test-files/
├── source-code/      (4 files: ts, json, py, css)
├── documents/        (3 files: md, txt, yaml)
├── edge-cases/       (3 files: empty, unicode, large)
└── special/          (2 files: hidden, spaces)
```

Host machine:
```bash
# Files are in Docker volume, access via:
docker exec pipeshub-ai ls -lh /data/pipeshub/test-files/
```

## Baseline Queries

### Check total records
```bash
curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" -X POST \
  "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d '{"query": "FOR doc IN records FILTER doc.connectorName == \"LOCAL_FILESYSTEM\" COLLECT WITH COUNT INTO count RETURN count"}' \
  | python3 -m json.tool
```

### Check content status
```bash
cat > /tmp/arango_query.json << 'EOF'
{
  "query": "FOR doc IN records FILTER doc.connectorName == \"LOCAL_FILESYSTEM\" COLLECT hasContent = (doc.blockContainers != null AND doc.blockContainers.blocks != null AND LENGTH(doc.blockContainers.blocks) > 0) WITH COUNT INTO count RETURN {hasContent, count}"
}
EOF

curl -s -u "root:czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm" -X POST \
  "http://localhost:8529/_db/es/_api/cursor" \
  -H "Content-Type: application/json" \
  -d @/tmp/arango_query.json \
  | python3 -m json.tool
```

## Success Criteria

After testing completes, you should see:
- 12 test files synced with content
- All test files have extension, filePath, fileSize populated
- All test files have blockContainers.blocks[0].data with file content
- Chat search returns TypeScript files when queried
- Qdrant has embeddings for test files
- No errors in connector logs
- Migration validation: 1,680 records (1,668 + 12) all with content

## Contact & References

- **Test Report:** `connector-missing-content-test-report.md`
- **Summary:** `SUMMARY.md`
- **Implementation:** `.prompts/009-connector-missing-content-fix/SUMMARY.md`
- **Plan:** `.prompts/008-connector-missing-content-plan/connector-missing-content-plan.md`

---

**Status:** Ready to unblock and test
**Blocker:** Frontend TypeScript build
**ETA to Testing:** 30 minutes (after fixing build)
**Test Duration:** 4-6 hours
**Total ETA:** ~6-7 hours from now
