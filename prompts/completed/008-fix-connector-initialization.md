<objective>
Fix the LocalFilesystemConnector initialization so it gets properly added to `container.connectors_map`, enabling file streaming during indexing.

Currently, files sync to the database and embeddings generate, but the indexing service fails with:
```
Connector 'local_filesystem' not found
```

This happens because the connector isn't in the runtime `connectors_map` that the stream endpoint uses.
</objective>

<context>
Project: PipesHub - enterprise search platform with multiple data connectors
Location: /Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig

Current state:
- LocalFilesystemConnector syncs files successfully (1,592 files)
- Factory registration fixed: `"local_filesystem": LocalFilesystemConnector`
- Permissions fixed: Using `EntityType.ORGANIZATION` with org_id
- BUT: connector not in `container.connectors_map` at runtime

The error occurs in router.py line 375-379:
```python
connector = container.connectors_map.get(connector_name)
if not connector:
    raise HTTPException(detail=f"Connector '{connector_name}' not found")
```

Key files to examine:
- `/backend/python/app/connectors/api/router.py` - where error occurs
- `/backend/python/app/connectors/core/factory/connector_factory.py` - factory registration
- `/backend/python/app/containers/connector.py` - container with connectors_map
- `/backend/python/app/connectors_main.py` - connector service startup
- Other working connectors (dropbox, onedrive) - how they initialize
</context>

<research>
Thoroughly investigate how connectors get initialized and added to connectors_map:

1. **External Documentation**:
   - Search GitHub for PipesHub repository and documentation
   - Look for connector development guides or architecture docs
   - Check if there are README files explaining connector lifecycle

2. **Codebase Analysis**:
   - How does `connectors_map` get populated?
   - What initialization steps do working connectors (Dropbox, OneDrive) go through?
   - Is there a startup sequence that needs to include LocalFilesystem?
   - Are connectors initialized from database configuration or code?

3. **Compare with Working Connectors**:
   - Find where Dropbox/OneDrive connectors are added to connectors_map
   - Identify any registration or initialization hooks they use
   - Check if they have database entries that trigger initialization
</research>

<requirements>
1. Identify the exact mechanism that adds connectors to `connectors_map`
2. Determine what's missing for LocalFilesystemConnector
3. Implement the fix to properly initialize the connector
4. Ensure the connector is available for file streaming during indexing
5. Verify the fix doesn't break existing connector functionality

The fix should:
- Follow existing patterns used by other connectors
- Not require manual database entries if possible
- Work automatically when the connector is configured
</requirements>

<implementation>
After identifying the issue:

1. Modify necessary files to properly initialize LocalFilesystemConnector
2. Ensure it gets added to connectors_map on startup
3. Test that `/api/v1/internal/stream/record/{record_id}` works
4. Verify files can be indexed after the fix

Deploy fixes to container:
```bash
docker cp [fixed_file] pipeshub-ai:/app/python/[path]
docker restart pipeshub-ai
```
</implementation>

<output>
1. Report findings on connector initialization mechanism
2. Implement and deploy the fix
3. Document what was changed and why
4. Verify indexing works end-to-end
</output>

<verification>
Before declaring complete:
1. Container logs show no "Connector not found" errors
2. Stream endpoint returns file content successfully
3. Files get indexed (check "Successfully processed document" logs)
4. AI assistant can search and find file contents

Test with:
```bash
docker logs pipeshub-ai 2>&1 | grep -E "Connector.*not found|Successfully processed"
```
</verification>

<success_criteria>
- LocalFilesystemConnector is in connectors_map at runtime
- File streaming works for indexing
- Documents are fully indexed with embeddings
- Search returns results from local filesystem files
</success_criteria>
