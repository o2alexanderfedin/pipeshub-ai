<objective>
Verify that the Local Filesystem connector is correctly configured to point to the current project directory (/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig), and fix the configuration if it's pointing to an incorrect location.

This ensures that the connector syncs files from the correct directory when indexing documents for search and AI features.
</objective>

<context>
The PipesHub application has been deployed to local Docker containers. A Local Filesystem connector has been configured to sync files from the local machine into the system for indexing and search.

The connector configuration is stored in:
- Database: ArangoDB 'es' database (connector settings and metadata)
- Database: MongoDB (possibly connector state/configuration)
- Environment: May have configuration in .env files or connector service settings

Current project directory: `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig`

The connector should be syncing from this directory to make project files searchable.
</context>

<requirements>
1. **Verify configuration files**:
   - Check environment variables for Local Filesystem connector path
   - Read connector configuration files in the codebase
   - Look for path settings in Docker compose files or .env

2. **Verify database records**:
   - Query ArangoDB 'es' database for connector configurations
   - Check MongoDB for any connector settings
   - Look for Local Filesystem connector entry with path/directory settings

3. **Check consistency**:
   - Compare configuration between files and database
   - Identify any mismatches or incorrect paths
   - Verify the connector is actually pointing to current directory

4. **Fix if incorrect**:
   - If the path is wrong, update it to: `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig`
   - Update both configuration files and database records
   - Ensure consistency across all configuration sources

5. **Trigger re-sync if needed**:
   - If configuration was updated, trigger a fresh sync
   - Verify the connector picks up the new path
</requirements>

<implementation>
Follow this sequence:

1. **Check environment and config files**:
   ```bash
   # Check environment variables
   grep -r "LOCAL.*FILESYSTEM\|CONNECTOR.*PATH" deployment/docker-compose/.env

   # Check connector configuration
   grep -r "localfilesystem\|local_filesystem" backend/python/app/connectors/
   ```

2. **Query ArangoDB** (connector configuration often stored here):
   ```bash
   docker exec -it arango arangosh --server.password 'czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm' --javascript.execute-string "
   db._useDatabase('es');
   db._query('FOR doc IN connectors FILTER doc.type == \"localfilesystem\" OR doc.type == \"local_filesystem\" RETURN doc').toArray()
   "
   ```

3. **Query MongoDB** (may have connector state):
   ```bash
   docker exec -it mongodb mongosh -u admin -p UnZE+hwNwkMg4vvoS7FSBipdxHcIwajr --eval "
   db = db.getSiblingDB('es');
   db.connectors.find({type: {$regex: /local.*filesystem/i}}).pretty()
   "
   ```

4. **Check connector service logs** for current configuration:
   ```bash
   docker logs pipeshub-ai 2>&1 | grep -i "local.*filesystem\|connector.*path"
   ```

5. **If path is incorrect**, update the configuration:
   - For ArangoDB: Update the document with correct path
   - For MongoDB: Update the connector record
   - For config files: Update .env or connector config files
   - Restart connector service if needed: `docker restart pipeshub-ai`

6. **Verify the fix**:
   - Check logs to confirm connector is using new path
   - Trigger a sync to ensure it's working
   - Verify files from current directory appear in search results
</implementation>

<output>
Create a verification report: `./verification/local-filesystem-connector-status.md`

The report should include:
- Current configuration found (files + database)
- Whether path is correct or incorrect
- If incorrect: what was wrong and what was fixed
- Commands used to verify and fix
- Confirmation that connector is now using correct path
- Next steps (if any)
</output>

<verification>
Before declaring complete, verify:

1. **Path is correct**: Connector configuration shows `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig`
2. **Consistency**: Configuration is consistent across all sources (files, ArangoDB, MongoDB)
3. **Connector is active**: Logs show connector is running with correct path
4. **Sync is working**: Evidence that connector is syncing files (check logs or trigger sync)

Test command:
```bash
# Verify connector configuration in ArangoDB
docker exec -it arango arangosh --server.password 'czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm' --javascript.execute-string "
db._useDatabase('es');
print(JSON.stringify(db._query('FOR doc IN connectors FILTER doc.type == \"localfilesystem\" OR doc.type == \"local_filesystem\" RETURN doc').toArray(), null, 2))
"
```
</verification>

<success_criteria>
- Local Filesystem connector configuration verified
- Path is confirmed to be `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig`
- Configuration is consistent across all sources
- If path was wrong, it has been corrected and verified
- Verification report created documenting the status
- Connector service acknowledges the correct configuration
</success_criteria>
