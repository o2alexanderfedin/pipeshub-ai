# PipesHub Local Filesystem Connector - Organization ID Hardcoding Issue

## Critical Issue

The Local Filesystem connector is **hardcoded** to use organization ID `692029575c9fa18a5704d0b7` regardless of:
- etcd configuration changes
- Database configuration updates
- Container restarts

## Evidence

Even after:
1. ✅ Updating connector config in `apps` collection
2. ✅ Migrating etcd configuration from old to new orgId
3. ✅ Restarting the container

The connector **STILL** creates records for the wrong organization:

```log
Creating BELONGS_TO edge for RecordGroup f37e3c5c-8825-49f2-9356-428e6f982769 to Org 692029575c9fa18a5704d0b7
```

## Root Cause

The organization ID is being passed to the connector during initialization, likely from:

1. **Connector Instance Registration**: When the connector is first created/registered
2. **Startup Configuration**: Read from database during service initialization
3. **Hardcoded in Connector Initialization**: Passed as parameter when connector is instantiated

## Where the OrgId Comes From

Based on logs, the connector is initialized with:
```
Local Filesystem connector initialized for org 692029575c9fa18a5704d0b7
```

This happens in `connectors_main.py` during startup.

## Solutions

### Option A: Update Connector Instance in Database (Recommended)

The connector instance itself (not just configuration) stores the orgId. This needs to be updated:

1. **Find connector instance**:
```javascript
db._useDatabase("es");
FOR doc IN connectorInstances
  FILTER doc.type == "LOCAL_FILESYSTEM" OR doc.connectorId == "local_filesystem"
  RETURN doc
```

2. **Update orgId**:
```javascript
FOR doc IN connectorInstances
  FILTER doc.type == "LOCAL_FILESYSTEM"
  UPDATE doc WITH { orgId: "6928ff5506880ac843ef5a3c" } IN connectorInstances
  RETURN NEW
```

3. **Restart connector service**

### Option B: Delete and Recreate Connector

1. Delete the connector completely from UI
2. Re-add it (will use current user's orgId)
3. Configure settings
4. Trigger sync

### Option C: Fix at Code Level

Update the connector initialization to use the **current user's organization** instead of a stored/hardcoded one.

**File**: `backend/python/app/connectors_main.py`

The connector should be initialized per-user-request, not per-stored-organization.

## What We've Tried

### ✅ Completed
1. Migrated all existing records from old org to new org
2. Updated connector configuration in `apps` collection
3. Migrated etcd configuration
4. Deleted incomplete/wrong records
5. Restarted container

### ❌ Still Failing
- Connector continues to use old orgId during initialization
- Records created for wrong organization
- Stats show 0 for current user

## Impact

**Complete blocker** for:
- Chat source code search
- Knowledge base functionality
- Any connector-based indexing

## Recommended Action

**Immediate**: Find and update `connectorInstances` collection in ArangoDB

**Long-term**: Fix connector architecture to be user-scoped, not org-scoped at registration

## Next Steps

1. Search for `connectorInstances` or similar collection
2. Update orgId in connector instance record
3. Restart connector service
4. Verify new records use correct orgId
5. Trigger fresh sync

## Date
2025-11-28

## Status
🔴 **BLOCKED** - Connector hardcoded to wrong organization, requires database fix
