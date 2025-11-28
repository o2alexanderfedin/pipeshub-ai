# PipesHub Local Filesystem Connector - Organization Fix Complete

## Date
2025-11-28

## Problem Statement

The Local Filesystem connector was creating records for the wrong organization ID, causing:
- Chat could not find source code files
- Stats showed 0 records for the current user
- All newly synced files went to the wrong organization

## Root Cause

**TWO** organizations were active in the system:
1. `692029575c9fa18a5704d0b7` (old - should be inactive)
2. `6928ff5506880ac843ef5a3c` (current user's organization)

The connector service initializes connectors for **all active organizations** at startup. Since the old organization was still active, it continued creating records for it.

Additionally, the new organization was missing the required edge in the graph database linking it to the Local Filesystem app.

## Solution Applied

### Step 1: Deactivate Old Organization

```javascript
db._useDatabase("es");
UPDATE {_key: "692029575c9fa18a5704d0b7"}
WITH {isActive: false}
IN organizations
RETURN NEW
```

**Result**: Old organization is now inactive

### Step 2: Create Org-App Edge

The `get_org_apps()` function uses a graph traversal to find apps:

```python
FOR app IN OUTBOUND
    'organizations/{org_id}'
    orgAppRelation  # Edge collection
FILTER app.isActive == true
RETURN app
```

Created the missing edge:

```javascript
INSERT {
  _from: "organizations/6928ff5506880ac843ef5a3c",
  _to: "apps/6928ff5506880ac843ef5a3c_LOCAL_FILESYSTEM",
  createdAtTimestamp: DATE_NOW()
} INTO orgAppRelation
```

**Result**: New organization is now linked to the Local Filesystem app

### Step 3: Clean Up Old Edge

```javascript
FOR edge IN orgAppRelation
FILTER edge._from == "organizations/692029575c9fa18a5704d0b7"
REMOVE edge IN orgAppRelation
```

**Result**: Old organization no longer linked to any apps

### Step 4: Restart Connector Service

```bash
docker restart pipeshub-ai
```

**Result**: Connector service reinitializes and now finds only 1 organization

## Verification

### Organization Discovery

**Before**:
```log
Found 2 organizations in the system
App names: [localfilesystem]  # For both orgs
```

**After**:
```log
Found 1 organizations in the system
App names: [localfilesystem]  # Only for correct org
```

### Record Creation

**Before**:
```log
Creating BELONGS_TO edge for RecordGroup ... to Org 692029575c9fa18a5704d0b7  # WRONG
```

**After**:
```log
Creating BELONGS_TO edge for RecordGroup ... to Org 6928ff5506880ac843ef5a3c  # CORRECT
```

### Database Records

```javascript
// Records now being created for correct org
FOR doc IN records
  FILTER doc.orgId == "6928ff5506880ac843ef5a3c"
  COLLECT WITH COUNT INTO count
  RETURN count
// Result: 700+ records (and growing)
```

## Status

✅ **FIXED**: Connector now creates records for the correct organization
✅ **FIXED**: Connector initializes properly at startup
✅ **FIXED**: Graph edges correctly link organization to apps

## Remaining Issue

⚠️ **Records created without content**: All records have:
- `extension: null`
- `filePath: null`
- `fileSize: null`
- `content: null`

This is a **separate issue** from the organization mismatch. Records are being created as placeholders but file content is not being read and stored.

### Impact

While records are now created for the correct organization, they still cannot be searched because:
- No file content → No vector embeddings
- No embeddings → Semantic search returns nothing
- Chat still cannot analyze source code

## Next Steps

The organization ID issue is resolved. The remaining content issue requires investigating:

1. **File reading logic** in Local Filesystem connector
2. **Why `extension`, `filePath`, and `content` are null**
3. **File processing workflow** from filesystem → database

## Files Changed

### Database Changes
- `organizations` collection: Deactivated old org
- `orgAppRelation` collection: Created new edge, deleted old edge
- `apps` collection: No changes (already had correct app document)

### Configuration Changes
- None (configuration was already correct in `apps` and `etcd`)

### Code Changes
- None (issue was data-level, not code-level)

## Lessons Learned

1. **Graph Database Architecture**: PipesHub uses graph traversal to find org-app relationships via edges, not direct document relationships
2. **Startup Initialization**: Connector service processes **all active organizations** at startup
3. **Multi-Tenancy**: Organization-level isolation requires both:
   - Correct data (orgId in documents)
   - Correct relationships (edges in graph)

## Key Collections Involved

- `organizations`: Organization documents with `isActive` flag
- `apps`: Connector/app configurations per organization (key: `{orgId}_{connectorType}`)
- `orgAppRelation`: Edge collection linking organizations to their apps
- `records`: File records with `orgId` field
- `recordGroups`: Directory/folder records with `orgId` field
- `belongsTo`: Edges linking records/groups to organizations

## Related Issues

- [CONNECTOR-ORG-ID-ISSUE.md](./CONNECTOR-ORG-ID-ISSUE.md) - Initial investigation
- [FINAL-SUMMARY-CHAT-ISSUE.md](./FINAL-SUMMARY-CHAT-ISSUE.md) - Chat search failure
- [chat-source-code-search-issue.md](./chat-source-code-search-issue.md) - Content missing issue
