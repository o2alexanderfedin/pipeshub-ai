<task_objective>
Debug why the Local Filesystem connector settings page shows "0 records" despite:
1. The database containing 1,647 records with correct structure (`origin: "CONNECTOR"`, `connectorName: "LOCAL_FILESYSTEM"`)
2. The Python backend API (`/api/v1/stats`) correctly returning 1,647 records
3. The chat interface working fine (authentication is valid)

This suggests a frontend or Node.js gateway routing issue preventing the connector stats from displaying correctly.
</task_objective>

<context>
## What We Know

### Database State (VERIFIED ✓)
```json
{
  "origin": "CONNECTOR",
  "connectorName": "LOCAL_FILESYSTEM",
  "orgId": "692029575c9fa18a5704d0b7",
  "recordType": "FILE",
  "indexingStatus": "COMPLETED",
  "recordName": "CODE_OF_CONDUCT.md"
}
```
- Total records: 1,647
- Records properly structured with `origin` and `connectorName` fields
- 1,508 completed, 103 not started, 34 unsupported, 2 failed

### Python Backend API (VERIFIED ✓)
```bash
curl "http://localhost:8088/api/v1/stats?org_id=692029575c9fa18a5704d0b7&connector=LOCAL_FILESYSTEM"
```
Returns:
```json
{
  "success": true,
  "data": {
    "connector": "LOCAL_FILESYSTEM",
    "origin": "CONNECTOR",
    "stats": {
      "total": 1647,
      "indexing_status": {
        "COMPLETED": 1508,
        "NOT_STARTED": 103,
        "FAILED": 2,
        "FILE_TYPE_NOT_SUPPORTED": 34
      }
    }
  }
}
```

### Frontend Code Flow
1. **UI Component**: `frontend/src/sections/accountdetails/connectors/components/connector-stats.tsx`
   - Line 176-179: Calls `/api/v1/knowledgeBase/stats/${connector}`
   - For Local Filesystem: `/api/v1/knowledgeBase/stats/LOCAL_FILESYSTEM`

2. **Node.js Gateway**: `backend/nodejs/apps/src/modules/knowledge_base/controllers/kb_controllers.ts:2243`
   - Routes `/api/v1/knowledgeBase/stats/:connector` to Python backend
   - Line 2258-2266: Makes request to `${appConfig.connectorBackend}/api/v1/stats`

3. **Python Backend**: `backend/python/app/connectors/services/base_arango_service.py:482`
   - Queries ArangoDB with filters:
     - `FILTER doc.origin == "CONNECTOR"`
     - `FILTER doc.connectorName == connector`
   - Returns correct data

### Authentication (VERIFIED ✓)
- User is authenticated (chat works fine)
- Token is valid for other API calls
- Screenshot shows user "Alexander!" in UI

## The Problem

The UI shows "0 records" despite all backend APIs working correctly. This suggests:
- Frontend API call is failing silently
- Response parsing issue
- Connector name mismatch (case sensitivity?)
- CORS or middleware issue blocking the request
- Frontend error handling swallowing the response
</context>

<investigation_steps>
## Step 1: Check Browser Network Tab
1. Open browser DevTools (F12) → Network tab
2. Reload the connector settings page
3. Look for API call to `/api/v1/knowledgeBase/stats/LOCAL_FILESYSTEM` or similar
4. Check:
   - Is the request being made?
   - What's the response status code?
   - What's the actual response body?
   - Are there any CORS errors in console?

## Step 2: Check Connector Name Format
The connector name might be transformed between frontend and backend:
- Frontend might use: "localfilesystem", "local_filesystem", "LOCAL_FILESYSTEM"
- Backend expects: "LOCAL_FILESYSTEM"

Search for how connector name is determined:
```bash
# Find where connector name is set for stats API call
grep -r "connectorName\|connector.*name" frontend/src/sections/accountdetails/connectors/
```

## Step 3: Test Node.js Gateway Directly
```bash
# Get a valid auth token from browser (localStorage or cookies)
# Then test the Node.js endpoint
curl -H "Authorization: Bearer <TOKEN>" \
  "http://localhost:8001/api/v1/knowledgeBase/stats/LOCAL_FILESYSTEM"
```

## Step 4: Check Frontend Error Handling
Look at `connector-stats.tsx:197-203`:
```typescript
} catch (err) {
  console.error('Error fetching connector statistics:', err);
  setError(err instanceof Error ? err.message : 'Unknown error occurred');
  // Falls back to mock data!
}
```

The component falls back to mock data on error. Check browser console for errors.

## Step 5: Verify Connector Name in URL
The connector settings page URL should be:
- `/account/company-settings/settings/connector/localfilesystem` or
- `/account/company-settings/settings/connector/LOCAL_FILESYSTEM`

Check the actual URL and verify it matches what the stats API expects.

## Step 6: Check Route Parameter Extraction
In `connector-manager.tsx:411-412`:
```typescript
connectorNames={[connector.name]}
```

And in `use-connector-manager.ts:37`:
```typescript
const { connectorName } = useParams<{ connectorName: string }>();
```

Verify the connector name from URL params matches what's used in the stats API call.
</investigation_steps>

<debugging_approach>
## Systematic Debugging

### Phase 1: Verify API Call is Made
1. Open browser DevTools
2. Navigate to Connector Settings page
3. Check Network tab for `/stats` requests
4. Document:
   - Request URL
   - Request headers (especially Authorization)
   - Response status
   - Response body
   - Any console errors

### Phase 2: Test with Browser Console
```javascript
// Run in browser console on the connector settings page
const orgId = localStorage.getItem('orgId') || '692029575c9fa18a5704d0b7';
const connectorName = 'LOCAL_FILESYSTEM';

fetch(`/api/v1/knowledgeBase/stats/${connectorName}`, {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
    'Content-Type': 'application/json'
  }
})
.then(res => res.json())
.then(data => console.log('Stats response:', data))
.catch(err => console.error('Stats error:', err));
```

### Phase 3: Add Logging to Frontend
Temporarily add console.log statements to `connector-stats.tsx`:
- Before API call (line 172)
- After successful response (line 182)
- In catch block (line 199)

### Phase 4: Check Connector Name Transformation
```bash
# Find connector name source
grep -A5 -B5 "LOCAL_FILESYSTEM\|localfilesystem" \
  frontend/src/sections/accountdetails/connectors/components/connector-manager/connector-manager.tsx
```

### Phase 5: Verify orgId Extraction
The stats API needs orgId. Check where it comes from:
- User context/session?
- JWT token?
- LocalStorage?
</debugging_approach>

<expected_outcomes>
## Possible Root Causes

### Most Likely
1. **Connector name mismatch**: URL param uses "localfilesystem" but API expects "LOCAL_FILESYSTEM"
2. **Missing orgId**: Stats API can't determine which organization's data to query
3. **Silent auth failure**: Request returns 401/403 but error handling shows 0 instead of error

### Less Likely
4. **CORS issue**: Backend blocking request (but chat works, so unlikely)
5. **Response parsing error**: Frontend expecting different data structure
6. **Caching issue**: Frontend showing stale cached "0 records" data
</expected_outcomes>

<success_criteria>
- Identify exact API request being made from browser
- Identify exact response (or error) from backend
- Determine root cause of "0 records" display
- Propose fix (likely connector name normalization or error handling)
</success_criteria>

<deliverables>
1. **Root Cause Analysis**: Document exact reason stats show 0
2. **Fix Implementation**: Code changes to resolve the issue
3. **Verification**: Test that stats display correctly after fix
4. **Report**: Save findings to `./verification/connector-stats-debug-report.md`
</deliverables>
