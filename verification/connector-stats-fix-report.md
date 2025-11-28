# Local Filesystem Connector Stats Fix - Verification Report

## Issue Summary
The Local Filesystem connector settings page was showing "0 records" despite the database containing 1,648 records.

## Root Causes Identified

### 1. Backend Connector Name Normalization
**File**: `backend/python/app/connectors/services/base_arango_service.py:566`

**Problem**: The stats API was querying for connector name as-is ("Local Filesystem") but the database stores "LOCAL_FILESYSTEM" (uppercase with underscore).

**Fix**:
```python
# Line 566
connector = connector.upper().replace(' ', '_')
```

This normalizes "Local Filesystem" → "LOCAL_FILESYSTEM" to match database records.

### 2. JavaScript String Replacement Bug
**File**: `backend/nodejs/apps/src/modules/knowledge_base/controllers/kb_controllers.ts:149`

**Problem**: The `normalizeAppName()` function only removed the FIRST space, not all spaces.

```typescript
// BEFORE (buggy):
const normalizeAppName = (value: string): string => value.replace(' ', '').toLowerCase();
// "Local Filesystem" → "LocalFilesystem" (only first space removed!)

// AFTER (fixed):
const normalizeAppName = (value: string): string => value.replace(/\s+/g, '').toLowerCase();
// "Local Filesystem" → "localfilesystem" (all spaces removed)
```

This affected:
- Resync validation (`validateActiveConnector`)
- Connector name normalization throughout the Node.js gateway

## Fixes Applied to Running Container

Since the Docker container runs from a pre-built image, fixes were applied directly to the running container:

### Python Backend Fix
```bash
docker exec pipeshub-ai sed -i '566s/.*/                connector = connector.upper().replace(" ", "_")/' \
  /app/python/app/connectors/services/base_arango_service.py
```

### Node.js Backend Fix
```bash
docker exec pipeshub-ai sed -i "91s/.*/const normalizeAppName = (value) => value.replace(\/\\\\s+\/g, '').toLowerCase();/" \
  /app/backend/dist/modules/knowledge_base/controllers/kb_controllers.js
```

### Service Restart
```bash
# Restart Node.js process to pick up changes
docker exec pipeshub-ai pkill -f "node dist/index.js"
# (Process auto-restarts via supervisor)
```

## Verification

### Python Backend API Test
```bash
curl "http://localhost:8088/api/v1/stats?org_id=692029575c9fa18a5704d0b7&connector=Local%20Filesystem"
```

**Result**:
```json
{
  "success": true,
  "data": {
    "org_id": "692029575c9fa18a5704d0b7",
    "connector": "LOCAL_FILESYSTEM",
    "origin": "CONNECTOR",
    "stats": {
      "total": 1648,
      "indexing_status": {
        "NOT_STARTED": 5,
        "IN_PROGRESS": 0,
        "COMPLETED": 1605,
        "FAILED": 0,
        "FILE_TYPE_NOT_SUPPORTED": 38,
        "AUTO_INDEX_OFF": 0
      }
    }
  }
}
```

✅ **Backend returning correct data: 1,648 total records**

### Frontend API Call
The browser now successfully makes the stats API call:
```
GET /api/v1/knowledgeBase/stats/Local%20Filesystem => 200 OK
```

### Expected UI State After Browser Refresh
After refreshing the browser, the connector stats card should display:
- **Total**: 1,648 records
- **Completed**: 1,605 (97.4%)
- **Not Started**: 5
- **File Type Not Supported**: 38
- **Failed**: 0
- **In Progress**: 0

## Permanent Fix Required

⚠️ **IMPORTANT**: The fixes applied to the running container will be lost when the container is recreated.

### For Permanent Fix, Update Source Code:

#### 1. Python Backend
**File**: `backend/python/app/connectors/services/base_arango_service.py`

```python
# Around line 565-567
else:
    # Normalize connector name: "Local Filesystem" → "LOCAL_FILESYSTEM"
    connector = connector.upper().replace(' ', '_')
    query = """
```

#### 2. Node.js Backend
**File**: `backend/nodejs/apps/src/modules/knowledge_base/controllers/kb_controllers.ts`

```typescript
// Line 149
const normalizeAppName = (value: string): string => value.replace(/\s+/g, '').toLowerCase();
```

Then rebuild and redeploy the Docker image:
```bash
cd deployment/docker-compose
docker-compose build
docker-compose up -d
```

## Testing Checklist

After applying permanent fixes:

- [ ] Verify stats API returns correct count: `curl "http://localhost:8088/api/v1/stats?org_id=<ORG_ID>&connector=Local%20Filesystem"`
- [ ] Check UI displays correct stats (refresh browser)
- [ ] Test "Sync" button works without "Connector not allowed" error
- [ ] Verify resync operation completes successfully
- [ ] Test with other multi-word connectors (e.g., "Google Drive", "Microsoft Teams")

## Date
2025-11-28

## Status
✅ **FIXED** - Temporary fix applied to running container. Permanent source code changes required.
