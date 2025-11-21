<objective>
Create a PipesHub connector for local filesystem that:
- Indexes files from `/Users/alexanderfedin/Projects/hapyy`
- Uses real-time file watching (fsevents on macOS)
- Integrates with PipesHub's existing connector architecture

This connector will allow PipesHub to index and search local project files, making them available in the knowledge base alongside other connected sources.
</objective>

<research>
Thoroughly analyze the existing connector architecture:

1. **Examine existing connectors** in `./backend/python/app/connectors/sources/`:
   - Study the structure of at least 2-3 existing connectors (e.g., Google Drive, Dropbox)
   - Understand the base classes, interfaces, and patterns used
   - Note how connectors handle authentication, file listing, content retrieval

2. **Understand the connector registration**:
   - How connectors are registered with the system
   - Configuration and metadata requirements
   - How connectors appear in the UI

3. **Study the indexing pipeline**:
   - How files are passed to the indexing service
   - Required metadata format
   - Content extraction process

4. **Check for existing local/filesystem patterns**:
   - Any existing local file handling code
   - Volume mounting in Docker (the path must be accessible to the container)
</research>

<requirements>
## Core Functionality

1. **File Discovery**:
   - Recursively scan `/Users/alexanderfedin/Projects/hapyy`
   - Support common file types: `.md`, `.txt`, `.py`, `.js`, `.ts`, `.json`, `.yaml`, `.yml`, `.html`, `.css`
   - Respect `.gitignore` patterns
   - Skip `node_modules`, `.git`, `__pycache__`, `venv`, `.env` directories

2. **Real-time Watching**:
   - Use `watchdog` library for cross-platform file system events
   - Detect file creates, modifies, deletes, moves
   - Debounce rapid changes (e.g., 1 second delay)
   - Queue changes for batch processing

3. **Content Extraction**:
   - Read file contents with proper encoding detection
   - Extract metadata: path, filename, extension, size, modified time
   - Generate unique record IDs based on file path

4. **Integration**:
   - Follow existing connector patterns exactly
   - Register as a new connector type in the system
   - Emit events to Kafka for indexing pipeline
   - Support incremental updates (not full re-index)

## Docker Volume Mounting
The target directory must be mounted into the container. Add to docker-compose:
```yaml
volumes:
  - /Users/alexanderfedin/Projects/hapyy:/data/local-files:ro
```
</requirements>

<implementation>
Follow these patterns from existing connectors:

1. Create connector class inheriting from base connector
2. Implement required methods:
   - `connect()` - Initialize watcher
   - `disconnect()` - Stop watcher
   - `list_items()` - Full directory scan
   - `get_item()` - Get single file content
   - `watch()` - Real-time event handling

3. Use `watchdog` for file watching:
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
```

4. Debounce events using asyncio or threading timer

5. Map file changes to connector events:
   - File created → record created
   - File modified → record updated
   - File deleted → record deleted
</implementation>

<output>
Create/modify these files:

1. `./backend/python/app/connectors/sources/local_filesystem/` - New connector directory
   - `__init__.py`
   - `connector.py` - Main connector class
   - `watcher.py` - File system watcher
   - `config.py` - Configuration schema

2. Register connector in the connector registry (find and update the appropriate file)

3. Update `./deployment/docker-compose/docker-compose.prod.yml` to mount the volume

4. Add `watchdog` to Python dependencies if not already present
</output>

<verification>
1. Connector appears in PipesHub UI as available source
2. Can configure and connect to the local directory
3. Files are indexed and searchable
4. File changes are detected and indexed in real-time
5. Deletes remove records from index
</verification>

<success_criteria>
- Connector follows existing architecture patterns
- Real-time file watching works correctly
- Files are properly indexed with metadata
- Integration with Kafka/indexing pipeline is complete
- Docker volume mounting is configured
- No errors in connector or indexing logs
</success_criteria>
