<?xml version="1.0" encoding="UTF-8"?>
<plan>
  <metadata>
    <topic>Fix Local Filesystem Connector Content Extraction</topic>
    <date>2025-11-27</date>
    <based_on>@.prompts/007-connector-missing-content-research/connector-missing-content-research.md</based_on>
    <confidence>high</confidence>
    <approach>Eager Loading (Better Fix)</approach>
  </metadata>

  <executive_summary>
    Switch Local Filesystem connector from lazy loading pattern (metadata only) to eager loading pattern (read content during sync). This 4-phase implementation will modify the connector to read file contents and populate block_containers with TextBlock objects during record creation, eliminating the dependency on indexing service HTTP calls for content fetching. All new records will have extension, filePath, fileSize, and content populated. Existing 700+ null records will be cleaned up and reprocessed. Expected outcome: Full semantic search and source code analysis functionality restored.
  </executive_summary>

  <root_cause_recap>
    The Local Filesystem connector follows the cloud storage pattern (like Dropbox, OneDrive), storing only metadata in ArangoDB while delegating content extraction to the indexing service. However, the critical field `fetch_signed_url` (which becomes `signedUrlRoute` in Kafka events) is never set in FileRecord creation. Without this field, the indexing service receives `signedUrl: null` and `buffer: null`, causing content extraction to fail silently. Additionally, the `path` field is never populated and `extension` metadata extraction is incomplete. The eager loading approach will resolve this by reading file content directly during sync, matching the Web connector's proven pattern and making the Local Filesystem connector self-contained.
  </root_cause_recap>

  <solution_design>
    <architecture_decision>
      <chosen_approach>Eager Loading Pattern</chosen_approach>
      <rationale>
        Local Filesystem connector has architectural advantages that make eager loading ideal:
        1. Direct file system access (no auth, no API calls)
        2. Files already on disk (no network latency)
        3. Fast local I/O (no rate limiting)
        4. Eliminates inter-service HTTP dependency
        5. Matches Web connector's proven pattern

        Unlike cloud connectors that need lazy loading for large files and OAuth token management, local files can be read synchronously during discovery. This simplifies the architecture and eliminates the fragile HTTP dependency.

        Constraint: Implement max_file_size_mb configuration to prevent memory exhaustion on very large files (e.g., skip files > 10MB by default).
      </rationale>
      <compared_alternatives>
        - Quick Fix (set fetch_signed_url): Minimal code (2 lines) but maintains HTTP dependency and fragile indexing service integration
        - Lazy Loading with retry logic: More resilient but still depends on inter-service communication
        - Hybrid (eager for small files, lazy for large): Adds complexity; eager loading with size limit is simpler
      </compared_alternatives>
    </architecture_decision>

    <data_flow>
      <step number="1" description="File Discovery">
        Location: connector.py:424-438 (_scan_directory method)
        Input: watch_path from configuration
        Process: Walk filesystem using os.walk(), filter by extension and ignore directories
        Output: List of absolute file paths
        Note: No changes needed here - already working
      </step>

      <step number="2" description="Content Reading (NEW)">
        Location: connector.py - NEW method read_file_content()
        Input: file_path (absolute path), max_size_mb from config
        Process:
          1. Check file size (skip if > max_size_mb)
          2. Detect encoding using chardet library
          3. Open file with detected encoding
          4. Read content with error handling
          5. Return content string or None on error
        Output: File content as string or None
        Error handling: Log warning, continue processing, mark record as partial
      </step>

      <step number="3" description="Record Creation with Content (MODIFIED)">
        Location: connector.py:378-422 (_create_file_record method)
        Input: file_path, existing_record (optional)
        Changes:
          1. After file stat (line 400), call read_file_content() → get content
          2. Set path = relative path from watch_path
          3. Set extension = Path.suffix (already partially done)
          4. Create FileRecord with all fields populated
          5. If content is not None, create TextBlock and add to block_containers
        Output: FileRecord with content in block_containers, all metadata fields set
        Note: If content is None, record still created with metadata for audit trail
      </step>

      <step number="4" description="Record Persistence (VERIFY)">
        Location: data_source_entities_processor.py:95-100 (_handle_new_record method)
        Input: FileRecord with block_containers populated
        Process: Call tx_store.batch_upsert_records([record])
        Verification: Confirm block_containers field is included in ArangoDB schema
        Output: Record stored in ArangoDB with content in block_containers
      </step>

      <step number="5" description="Kafka Event (IMPROVED)">
        Location: data_source_entities_processor.py:86-90 (on_new_records method)
        Input: FileRecord with block_containers
        Process: Call record.to_kafka_record()
        Note: Content already in DB, can be accessed by indexing service if needed
        Output: Kafka event with metadata; content stored separately in ArangoDB
      </step>

      <step number="6" description="Indexing Service Processing">
        Location: External to connector
        Input: Kafka event + record ID
        Process: Service can now fetch content from ArangoDB block_containers instead of calling connector HTTP
        Output: Embeddings stored in Qdrant vector DB
      </step>
    </data_flow>

    <field_population>
      Current State (Broken):
      - extension: Sometimes set (inconsistent)
      - path: Never set (field exists but always null)
      - size_in_bytes: Set from os.stat()
      - content: Never read (not in FileRecord model, stored in block_containers)

      After Implementation:
      - extension: Always extracted from filename using Path.suffix
      - path: Always set as relative path from watch_path
      - size_in_bytes: Always from os.stat()
      - content: Always read into block_containers.blocks[0].text (if readable)
      - Additional: Add metadata like creation_time, modification_time for audit
    </field_population>
  </solution_design>

  <implementation_phases>
    <phase number="1" name="Core Content Reading">
      <goal>
        Implement file content reading with encoding detection, size limits, and error handling. This is the foundation that all other phases depend on.
      </goal>

      <files_to_modify>
        <file path="backend/python/app/connectors/sources/local_filesystem/connector.py">
          <changes>
            1. Add new method read_file_content() after imports (line ~15)
            2. Add import for chardet library
            3. Add import for pathlib.Path (already imported)
            4. Modify _create_file_record() to call read_file_content()
          </changes>
          <line_ranges>1-50 (imports), 275-290 (new method), 378-422 (modify method)</line_ranges>
        </file>
      </files_to_modify>

      <new_code_required>
        <function name="read_file_content">
          <signature>
            async def _read_file_content(
              self,
              file_path: str,
              max_size_bytes: int = 10 * 1024 * 1024
            ) -> Optional[str]:
          </signature>
          <docstring>
            Read file content with encoding detection and size limits.

            Args:
              file_path: Absolute path to file
              max_size_bytes: Skip files larger than this (default 10MB)

            Returns:
              File content as string, or None if unreadable

            Behavior:
              - Returns None if file > max_size_bytes (logs info, not error)
              - Detects encoding using chardet
              - Falls back to UTF-8 if detection fails
              - Catches decode errors and returns None with warning
              - Catches permission errors and returns None with warning
              - Catches other exceptions as errors
          </docstring>
          <implementation>
            1. Check file size with os.path.getsize()
            2. If > max_size_bytes, log info and return None
            3. Open file in binary mode ('rb')
            4. Use chardet.detect() on chunk (first 1MB)
            5. Get encoding from detection result or default to UTF-8
            6. Re-open in text mode with detected encoding
            7. Read all content
            8. Return content
            9. Handle exceptions:
               - UnicodeDecodeError: Log warning "Cannot decode {path}: invalid {encoding}", return None
               - PermissionError: Log warning "Permission denied: {path}", return None
               - FileNotFoundError: Log warning "File disappeared: {path}", return None
               - Exception: Log error with traceback, return None
          </implementation>
          <returns>str or None</returns>
          <error_handling>All exceptions caught and logged, method never raises</error_handling>
        </function>
      </new_code_required>

      <dependencies>
        <library name="chardet" version="latest">
          Used for encoding detection. Command: pip install chardet
          Alternative: Use codecs.detect() but chardet more reliable
        </library>
        <existing_import>pathlib.Path (already imported)</existing_import>
        <existing_import>os module (already imported)</existing_import>
        <existing_import>logging (already imported)</existing_import>
      </dependencies>

      <testing>
        Unit tests for _read_file_content():
        1. test_read_text_file_success - Read valid UTF-8 file, verify content
        2. test_read_file_size_limit - File > max_size, verify returns None
        3. test_read_permission_denied - Mock os.open to raise PermissionError
        4. test_read_file_not_found - File deleted between scan and read
        5. test_read_encoding_detection - File with non-UTF8 encoding (e.g., Latin1)
        6. test_read_binary_file - Binary file with BOM, verify handling
        7. test_read_large_text_file - Large but < limit, verify complete read

        Integration tests:
        1. Create test files with various encodings in test directory
        2. Call connector _read_file_content() on each
        3. Verify content matches expected output
        4. Test with real files from watch_path
      </testing>

      <estimated_effort>4-6 hours including testing</estimated_effort>
    </phase>

    <phase number="2" name="Record Creation Modification">
      <goal>
        Modify _create_file_record() to populate all fields (extension, path, size, content) and populate block_containers with content.
      </goal>

      <files_to_modify>
        <file path="backend/python/app/connectors/sources/local_filesystem/connector.py">
          <changes>
            1. Add configuration reading for max_file_size_mb
            2. Call _read_file_content() in _create_file_record()
            3. Set path field = relative path from watch_path
            4. Ensure extension is always populated
            5. Create TextBlock with content and add to record.block_containers
            6. Add logging for record creation
          </changes>
          <line_ranges>378-422 (_create_file_record method)</line_ranges>
        </file>

        <file path="backend/python/app/connectors/sources/local_filesystem/connector.py">
          <changes>
            Update __init__() to read content extraction configuration from etcd
          </changes>
          <line_ranges>196-210 (init method where config is read)</line_ranges>
        </file>
      </files_to_modify>

      <new_code_required>
        <modification location="connector.py:378-422">
          <before>
            async def _create_file_record(
              self,
              file_path: str,
              existing_record: Optional[FileRecord] = None
            ) -> Tuple[FileRecord, List[Permission]]:
              path_obj = Path(file_path)
              stat = os.stat(file_path)

              record = FileRecord(
                id=file_id,
                record_name=path_obj.name,
                external_record_id=file_path,
                mime_type=self._get_mime_type(file_path),
                extension=path_obj.suffix.lstrip('.'),
                size_in_bytes=stat.st_size,
                # Missing: path, content, signed_url
              )

              return record, permissions
          </before>

          <after>
            async def _create_file_record(
              self,
              file_path: str,
              existing_record: Optional[FileRecord] = None
            ) -> Tuple[FileRecord, List[Permission]]:
              path_obj = Path(file_path)
              stat = os.stat(file_path)

              # Calculate relative path from watch_path for database storage
              try:
                relative_path = str(path_obj.relative_to(Path(self.watch_path)))
              except ValueError:
                # File outside watch_path (shouldn't happen)
                relative_path = file_path

              # NEW: Read file content with size limit and encoding detection
              max_size_bytes = self.max_file_size_mb * 1024 * 1024
              content = await self._read_file_content(file_path, max_size_bytes)

              # Extract extension safely
              extension = path_obj.suffix.lstrip('.') if path_obj.suffix else ""

              record = FileRecord(
                id=file_id,
                record_name=path_obj.name,
                external_record_id=file_path,
                mime_type=self._get_mime_type(file_path),
                extension=extension,  # Ensure always populated
                size_in_bytes=stat.st_size,
                path=relative_path,  # NEW: Set path field
                # signed_url: No longer needed (eager loading)
              )

              # NEW: Populate block_containers with file content
              if content is not None:
                text_block = TextBlock(text=content)
                record.block_containers.blocks.append(text_block)
                self.logger.debug(
                  f"✓ Content loaded: {path_obj.name} ({len(content)} bytes)"
                )
              else:
                self.logger.warning(
                  f"⚠ No content for {path_obj.name} (unreadable or too large)"
                )

              return record, permissions
          </after>

          <rationale>
            - relative_path: Stores human-readable path relative to watch_path, helps debugging
            - max_file_size_bytes: Calculated from config, prevents memory exhaustion
            - await _read_file_content(): Calls Phase 1 content reader
            - extension: Ensure always populated, empty string for files without extension
            - path: Set to relative path so database record is portable/debuggable
            - block_containers: New TextBlock added if content readable, records created even if content null
            - Logging: Clear distinction between successful and failed content reads
          </rationale>
        </modification>

        <configuration>
          <location>connector.py:__init__() around line 196-210</location>
          <code>
            # Read configuration for content extraction
            config = await self.config_service.get_config(
              f"/services/connectors/localfilesystem/config/{self.org_id}"
            )

            content_config = config.get("content_extraction", {})
            self.content_extraction_enabled = content_config.get("enabled", True)
            self.max_file_size_mb = content_config.get("max_file_size_mb", 10)

            self.logger.info(
              f"Content extraction: enabled={self.content_extraction_enabled}, "
              f"max_size_mb={self.max_file_size_mb}"
            )
          </code>
        </configuration>
      </new_code_required>

      <dependencies>
        <import_required>from app.models.entities import TextBlock</import_required>
        <check_required>Verify FileRecord model has block_containers field</check_required>
        <check_required>Verify TextBlock model has text field</check_required>
      </dependencies>

      <testing>
        Unit tests for _create_file_record():
        1. test_create_record_with_content - File readable, verify block_containers populated
        2. test_create_record_without_content - File unreadable, verify block_containers empty
        3. test_path_field_populated - Verify path = relative path from watch_path
        4. test_extension_field_populated - Various file types (txt, py, ts, json)
        5. test_size_field_populated - Verify size_in_bytes matches os.stat()
        6. test_large_file_skipped - File > max_size_mb, content=None, size_in_bytes still set

        Integration tests:
        1. Create test files in watch directory
        2. Run _create_file_record() on each
        3. Verify record.block_containers.blocks[0].text matches file content
        4. Verify record.path is relative and debuggable
      </testing>

      <estimated_effort>3-4 hours including testing</estimated_effort>
    </phase>

    <phase number="3" name="Database Schema and Persistence Verification">
      <goal>
        Verify that all populated fields (extension, path, size, block_containers) are correctly persisted in ArangoDB. No code changes expected here, but schema verification is critical.
      </goal>

      <files_to_modify>
        <file path="backend/python/app/connectors/core/base/data_processor/data_source_entities_processor.py">
          <changes>
            1. Verify that batch_upsert_records() includes block_containers in upsert
            2. Check mapping from FileRecord model to ArangoDB document
            3. Verify no field filtering that would drop content
          </changes>
          <line_ranges>95-100 (_handle_new_record method)</line_ranges>
        </file>

        <file path="backend/python/app/models/entities.py">
          <changes>
            1. Verify FileRecord model has all required fields:
               - is_file: bool
               - size_in_bytes: int
               - extension: str
               - path: str (optional is OK but should be set)
               - block_containers: BlocksContainer with blocks list
            2. Check to_arango_record() serialization includes block_containers
          </changes>
          <line_ranges>158-180 (FileRecord class), 100-120 (to_arango_record method)</line_ranges>
        </file>
      </files_to_modify>

      <schema_verification>
        <query name="Check Record Structure">
          <aql>
            FOR doc IN Records
              FILTER doc.connectorName == "LOCAL_FILESYSTEM"
              LIMIT 1
              RETURN {
                _key: doc._key,
                recordName: doc.recordName,
                extension: doc.extension,
                path: doc.path,
                sizeInBytes: doc.sizeInBytes,
                hasBlocks: LENGTH(doc.blockContainers.blocks) > 0 ? true : false,
                blockCount: LENGTH(doc.blockContainers.blocks),
                contentSize: doc.blockContainers.blocks[0].text ? LENGTH(doc.blockContainers.blocks[0].text) : null
              }
          </aql>
          <expected>
            All fields populated:
            - extension: "ts" (not null)
            - path: "src/index.ts" (not null, relative)
            - sizeInBytes: 4567 (numeric)
            - hasBlocks: true
            - blockCount: 1
            - contentSize: 4500+ (numeric, not null)
          </expected>
        </query>
      </schema_verification>

      <testing>
        Integration test:
        1. Create test file with known content in watch directory
        2. Run connector sync
        3. Query ArangoDB for the record using above query
        4. Verify all fields populated correctly
        5. Query block_containers directly to ensure not dropped

        Database validation:
        1. Check for null values in extension column (should be 0)
        2. Check for null values in path column (should be 0)
        3. Check for records with empty block_containers (should have explicit failure log)
      </testing>

      <estimated_effort>1-2 hours (mostly verification, minimal code changes expected)</estimated_effort>
    </phase>

    <phase number="4" name="Existing Records Migration">
      <goal>
        Reprocess 700+ existing records that have null content. Choose between:
        A) Delete and resync (clean but loses history)
        B) Update in place (preserves record IDs and timestamps)
        C) Mark for background reprocessing (minimal disruption)

        Chosen approach: B) Update in place via resync
      </goal>

      <migration_approach>
        <decision>Delete records with null content, trigger full resync</decision>
        <rationale>
          - Safest approach: Reprocessing files ensures all content readable
          - Clean state: No mix of old null records and new complete records
          - Predictable: Resync timestamp will be clear, before/after metrics clear
          - Time: Full resync ~5-10 minutes, acceptable for fix
          - Alternative (update in place): Would need complex query-and-update logic
        </rationale>
      </migration_approach>

      <implementation>
        <step number="1">
          Backup current records:
          ```bash
          # Export existing records to file for audit
          arangosh --server.endpoint="http://localhost:8529" \
            --server.database=oilfield \
            --server.username=oilfield \
            --server.password=oilfield_dev

          FOR doc IN Records
            FILTER doc.connectorName == "LOCAL_FILESYSTEM"
            RETURN doc

          # Save to: backup-local-filesystem-records-$(date +%s).json
          ```
        </step>

        <step number="2">
          Delete records with null content:
          ```aql
          FOR doc IN Records
            FILTER doc.connectorName == "LOCAL_FILESYSTEM"
            REMOVE doc IN Records

          # Returns: "deleted X records"
          ```

          Verification query after delete:
          ```aql
          FOR doc IN Records
            FILTER doc.connectorName == "LOCAL_FILESYSTEM"
            RETURN doc

          # Should return empty set
          ```
        </step>

        <step number="3">
          Delete associated record groups (directory structure):
          ```aql
          FOR doc IN RecordGroups
            FILTER doc.connectorName == "LOCAL_FILESYSTEM"
            REMOVE doc IN RecordGroups
          ```
        </step>

        <step number="4">
          Trigger full resync:
          - Set connector watch path to same directory
          - Call run_sync() method via API endpoint
          - Monitor logs for:
            - "Found XXX files to sync"
            - "Content loaded" messages (Phase 1 working)
            - Errors loading unreadable files
          - Wait for completion (5-10 minutes for 700+ files)
        </step>

        <step number="5">
          Verification:
          ```aql
          // Count records with content
          FOR doc IN Records
            FILTER doc.connectorName == "LOCAL_FILESYSTEM"
            FILTER LENGTH(doc.blockContainers.blocks) > 0
            RETURN DISTINCT 1

          // Should return: 700+ (all files processed)
          ```
        </step>
      </implementation>

      <rollback>
        If something goes wrong during/after migration:
        1. Stop connector service
        2. Restore from backup: Load backup JSON file back to ArangoDB
        3. Restart connector
        4. Investigate root cause before retry
      </rollback>

      <estimated_time>30-45 minutes including backup, deletion, and full resync</estimated_time>

      <testing>
        Post-migration validation:
        1. Record count check: COUNT(Records with LOCAL_FILESYSTEM) == original 700+
        2. Content check: 100% have block_containers populated (or explicit error logged)
        3. Metadata check: extension, path, size all populated
        4. No orphaned records: All records have valid file paths
        5. Embeddings: Indexing service successfully processes and stores in Qdrant
      </testing>
    </phase>

    <phase number="5" name="Configuration Management">
      <goal>
        Define configuration schema for content extraction and apply defaults.
      </goal>

      <configuration_location>
        etcd path: `/services/connectors/localfilesystem/config/{org_id}`
        Fallback: Environment variables
        Code defaults: Hardcoded in connector.py
      </configuration_location>

      <configuration_schema>
        ```yaml
        content_extraction:
          enabled: true                          # Enable/disable feature
          max_file_size_mb: 10                   # Skip files larger than this
          supported_mime_types:                  # MIME types to process (future extension)
            - text/*
            - application/json
            - application/javascript
          skip_binary: true                      # Skip non-text files
          encoding_fallback: utf-8               # Fallback encoding if detection fails
          log_level: info                        # Logging verbosity
        ```
      </configuration_schema>

      <implementation>
        <etcd_setup>
          Key: `/services/connectors/localfilesystem/config/{org_id}`
          Value (JSON):
          ```json
          {
            "auth": {
              "watch_path": "/data/local-files"
            },
            "content_extraction": {
              "enabled": true,
              "max_file_size_mb": 10,
              "skip_binary": true,
              "encoding_fallback": "utf-8"
            }
          }
          ```
        </etcd_setup>

        <code_defaults>
          Location: connector.py:__init__()
          ```python
          # Apply defaults if not in config
          content_config = config.get("content_extraction", {})
          self.content_extraction_enabled = content_config.get("enabled", True)
          self.max_file_size_mb = content_config.get("max_file_size_mb", 10)
          self.skip_binary = content_config.get("skip_binary", True)
          self.encoding_fallback = content_config.get("encoding_fallback", "utf-8")
          ```
        </code_defaults>
      </implementation>

      <testing>
        1. Test config reading from etcd
        2. Test fallback to defaults
        3. Test override via environment variables
        4. Test max_file_size_mb enforcement (create test file > limit)
        5. Test skip_binary flag (if implemented)
      </testing>

      <estimated_effort>2 hours</estimated_effort>
    </phase>

    <phase number="6" name="Indexing Service Integration (Enhancement, not required)">
      <goal>
        Document how indexing service can now work with local filesystem records. This phase is optional - content is now in ArangoDB, so indexing service can read directly instead of calling HTTP.
      </goal>

      <optional>
        This phase is a documentation/enhancement step only. The indexing service will continue to work as-is. However, it could be optimized to:
        1. Check if block_containers.blocks[0].text exists in record
        2. Use that content directly instead of calling HTTP endpoint
        3. Faster processing, no dependency on connector availability
      </optional>

      <estimated_effort>Documentation only, no code changes needed</estimated_effort>
    </phase>
  </implementation_phases>

  <error_handling>
    <scenario type="file_read_error">
      <description>File cannot be read (permissions, encoding, format)</description>
      <handling>
        1. Log warning with file path and reason
        2. Create record anyway with metadata only
        3. block_containers will be empty
        4. Indexing service can mark with "PARTIAL_CONTENT" status
      </handling>
      <recovery>
        1. Fix file permissions or encoding externally
        2. Trigger incremental resync
        3. Connector will re-read and update record
      </recovery>
      <example>
        "⚠ Cannot decode /data/local-files/binary.bin: invalid utf-8"
        "⚠ Permission denied: /data/local-files/readonly.txt"
      </example>
    </scenario>

    <scenario type="file_not_found">
      <description>File deleted between scan and content read</description>
      <handling>
        1. Log warning
        2. Create record anyway (external_record_id will point to missing file)
        3. Indexing service will handle gracefully
      </handling>
      <recovery>
        Automatic: Next sync will remove record if file gone
      </recovery>
    </scenario>

    <scenario type="file_too_large">
      <description>File larger than max_file_size_mb configuration</description>
      <handling>
        1. Log info (not error) - "Skipping content for large file"
        2. Create record with metadata only
        3. block_containers empty
        4. Can manually increase max_file_size_mb if needed
      </handling>
      <recovery>
        1. Increase max_file_size_mb in config
        2. Trigger resync
      </recovery>
    </scenario>

    <scenario type="encoding_detection_failure">
      <description>Chardet cannot detect encoding, file contains mixed encodings</description>
      <handling>
        1. Fall back to encoding_fallback configuration (default: UTF-8)
        2. If fallback fails, create record with no content
        3. Log warning with file path
      </handling>
      <recovery>
        If file is critical:
        1. Fix encoding manually (convert to UTF-8)
        2. Trigger resync
      </recovery>
    </scenario>

    <scenario type="database_write_failure">
      <description>ArangoDB transaction fails or times out</description>
      <handling>
        1. Retry with exponential backoff (existing connector logic)
        2. Log error with transaction details
        3. Skip record and continue with next
      </handling>
      <recovery>
        1. Check database connectivity
        2. Check database space
        3. Trigger resync
      </recovery>
    </scenario>

    <scenario type="configuration_missing">
      <description>Configuration not found in etcd</description>
      <handling>
        1. Use hardcoded defaults (enabled=true, max_size=10MB)
        2. Log info about using defaults
        3. Continue processing
      </handling>
      <recovery>
        1. Set configuration in etcd (optional optimization)
        2. Restart connector to reload config
      </recovery>
    </scenario>

    <global_error_strategy>
      - All file read errors logged but non-fatal
      - Records created even without content (for audit trail)
      - Connector continues processing remaining files
      - Detailed logs enable troubleshooting
      - No silent failures (all unreadable files logged with reason)
    </global_error_strategy>
  </error_handling>

  <testing_strategy>
    <unit_tests location="backend/python/tests/connectors/local_filesystem/">
      <test name="test_read_file_content_success">
        Fixture: Create test file with known content
        Test: Call _read_file_content(), verify content matches
        Assert: content == file contents exactly
      </test>

      <test name="test_read_file_size_limit">
        Fixture: Create file larger than max_size_bytes
        Test: Call _read_file_content()
        Assert: Returns None, logs info message
      </test>

      <test name="test_read_file_permission_denied">
        Fixture: Create file with no read permissions
        Test: Call _read_file_content()
        Assert: Returns None, logs warning with PermissionError
      </test>

      <test name="test_read_file_encoding_detection">
        Fixture: Create UTF-8, Latin1, and ASCII files
        Test: Call _read_file_content() on each
        Assert: All read correctly despite different encodings
      </test>

      <test name="test_read_binary_file">
        Fixture: Create binary file (PNG, ZIP, etc.)
        Test: Call _read_file_content()
        Assert: Returns None or handles gracefully (based on MIME type)
      </test>

      <test name="test_create_record_with_content">
        Fixture: Text file in watch directory
        Test: Call _create_file_record()
        Assert:
          - record.block_containers.blocks[0].text populated
          - record.path = relative path
          - record.extension = "txt"
      </test>

      <test name="test_create_record_without_content">
        Fixture: Unreadable file (empty, binary, etc.)
        Test: Call _create_file_record()
        Assert:
          - record still created
          - block_containers.blocks is empty
          - record.size_in_bytes still populated
      </test>

      <test name="test_path_field_relative">
        Fixture: File in subdirectory /data/local-files/src/index.ts
        Test: Call _create_file_record() with watch_path=/data/local-files
        Assert: record.path == "src/index.ts" (relative, not absolute)
      </test>
    </unit_tests>

    <integration_tests location="backend/python/tests/connectors/local_filesystem/">
      <test name="test_full_sync_with_content">
        Fixture: Directory with 5 text files (txt, py, ts, md, json)
        Test: Run connector sync
        Assert:
          - All 5 records created
          - All have block_containers.blocks[0].text populated
          - All have correct extension
      </test>

      <test name="test_mixed_file_types">
        Fixture: Directory with readable files (txt), unreadable (binary), large (>limit)
        Test: Run connector sync
        Assert:
          - Readable files have content
          - Unreadable files have empty blocks
          - Large files skipped with info log
          - All records created for audit trail
      </test>

      <test name="test_large_directory_performance">
        Fixture: Directory with 100+ files
        Test: Measure sync time
        Assert: Processing time < 5 minutes for 100 files
      </test>

      <test name="test_kafka_message_with_content">
        Fixture: Single text file
        Test: Run sync, capture Kafka message
        Assert:
          - Message includes recordId, extension, size
          - block_containers stored in ArangoDB, not in Kafka message
      </test>
    </integration_tests>

    <database_tests>
      <test name="test_arangodb_record_schema">
        Query: SELECT * FROM Records WHERE connectorName = 'LOCAL_FILESYSTEM' LIMIT 1
        Assert:
          - extension: string, not null
          - path: string, not null
          - sizeInBytes: number
          - blockContainers.blocks[0].text: string (if readable)
      </test>

      <test name="test_all_records_have_content">
        Query: Count records with LOCAL_FILESYSTEM and empty blockContainers
        Assert: Return set is empty (all have either content or explicit error log)
      </test>

      <test name="test_relative_paths_debuggable">
        Query: Sample 10 path values
        Assert: All are relative paths like "src/index.ts", not absolute paths
      </test>
    </database_tests>

    <e2e_tests>
      <test name="test_connector_to_qdrant">
        Fixtures: Create directory with source code files
        Steps:
          1. Run connector sync
          2. Wait for indexing service to process
          3. Query Qdrant for embeddings
        Assert:
          - Qdrant has embeddings for all files
          - Embeddings can be searched semantically
      </test>

      <test name="test_chat_search_source_code">
        Fixtures: Directory with Python, TypeScript, JSON files
        Steps:
          1. Run connector sync
          2. Query chat API for source code search
          3. Search for function names or code patterns
        Assert:
          - Chat returns relevant files
          - Confidence scores reasonable
      </test>

      <test name="test_existing_records_reprocessed">
        Fixtures: 700+ files
        Steps:
          1. Backup existing records
          2. Delete all LOCAL_FILESYSTEM records from DB
          3. Run full resync
          4. Verify all 700+ reprocessed with content
        Assert:
          - Record count matches original
          - All have block_containers.blocks[0].text
      </test>
    </e2e_tests>

    <regression_tests>
      <test name="test_organization_id_preserved">
        Assertion: All new records have correct org_id from context
      </test>

      <test name="test_record_groups_still_created">
        Assertion: Directory structure in RecordGroups collection still intact
      </test>

      <test name="test_permissions_still_assigned">
        Assertion: Records still have correct permission entries
      </test>

      <test name="test_sync_performance_acceptable">
        Assertion: Processing 100 files takes < 5 minutes (not significantly slower than before)
      </test>
    </regression_tests>

    <test_execution_order>
      1. Unit tests (fastest, no DB needed)
      2. Integration tests (need DB, can run in parallel)
      3. Database validation tests
      4. E2E tests (slowest, need all services)
      5. Regression tests (safety checks)
    </test_execution_order>

    <test_coverage_goal>
      Minimum: 80% line coverage in modified methods
      Target: 90% coverage including error paths
    </test_coverage_goal>
  </testing_strategy>

  <migration_plan>
    <existing_records count="700+">
      <current_state>
        All 700+ LOCAL_FILESYSTEM records have:
        - extension: possibly null (inconsistent)
        - path: null (field never set)
        - size_in_bytes: populated
        - block_containers: empty (no content read)
      </current_state>

      <approach>
        Delete and resync (clean state)
      </approach>

      <rationale>
        - Safest: Reprocessing files ensures all content readable and no stale data
        - Clean: All records created with new code, no mixing old/new
        - Predictable: Before/after metrics clear, timestamps show migration point
        - Acceptable: Full resync takes ~10 minutes for 700+ files
        - Alternative (update in place) would be more complex and risk data corruption
      </rationale>

      <steps>
        1. Backup current state
           ```bash
           # Export records for audit/recovery
           # Save to: backups/local-filesystem-$(date +%Y%m%d-%H%M%S).json
           ```

        2. Delete all LOCAL_FILESYSTEM records
           ```aql
           FOR doc IN Records
             FILTER doc.connectorName == "LOCAL_FILESYSTEM"
             REMOVE doc IN Records

           FOR doc IN RecordGroups
             FILTER doc.connectorName == "LOCAL_FILESYSTEM"
             REMOVE doc IN RecordGroups
           ```

        3. Verify deletion
           ```aql
           FOR doc IN Records
             FILTER doc.connectorName == "LOCAL_FILESYSTEM"
             RETURN COUNT(doc)  # Should be 0
           ```

        4. Trigger full resync
           - Call connector API endpoint or
           - Restart connector service with force-sync flag

        5. Monitor progress
           - Watch connector logs for "Found XXX files to sync"
           - Watch logs for "✓ Content loaded" vs "⚠ No content for" messages
           - Expected time: ~5-10 minutes for 700+ files

        6. Verify success
           ```aql
           // Check all records have content
           FOR doc IN Records
             FILTER doc.connectorName == "LOCAL_FILESYSTEM"
             FILTER LENGTH(doc.blockContainers.blocks) == 0
             RETURN doc._key  # Should be empty (no records without content)

           // Check record count matches
           FOR doc IN Records
             FILTER doc.connectorName == "LOCAL_FILESYSTEM"
             RETURN COUNT(doc)  # Should be 700+
           ```

        7. Validate with chat/search
           - Test semantic search for code patterns
           - Verify chat can find and analyze source code
      </steps>

      <estimated_time>
        - Backup: 2-3 minutes
        - Delete: 1 minute
        - Resync: 5-10 minutes
        - Validation: 5 minutes
        - Total: ~20 minutes
      </estimated_time>

      <rollback_plan>
        If something goes wrong:
        1. Stop connector service
        2. Import backup JSON back to ArangoDB
        3. Restart connector
        4. Investigate root cause

        Backup retention: Keep for 30 days minimum
      </rollback_plan>
    </existing_records>
  </migration_plan>

  <rollout_plan>
    <phase name="Development" duration="2-3 days">
      <steps>
        1. Implement Phase 1 (content reading)
           - Write _read_file_content() method
           - Add chardet dependency
           - Unit tests for reading with various encodings
           - Estimated: 6-8 hours including tests

        2. Implement Phase 2 (record creation)
           - Modify _create_file_record() to use reader
           - Populate block_containers with TextBlock
           - Set path field
           - Integration tests
           - Estimated: 4-5 hours including tests

        3. Implement Phase 3 (schema verification)
           - Verify database schema supports new fields
           - Query ArangoDB to confirm persistence
           - Fix any schema issues
           - Estimated: 2-3 hours

        4. Implement Phase 5 (configuration)
           - Add config reading to __init__()
           - Set defaults
           - Estimated: 2 hours

        5. Manual testing
           - Create test files locally
           - Run connector in development
           - Verify content populated in local ArangoDB
           - Test with various file types
           - Estimated: 3-4 hours
      </steps>

      <validation>
        - All unit tests passing (target: 80%+ coverage)
        - Manual testing confirms content in records
        - No regressions in existing functionality
      </validation>

      <blockers>
        - chardet library availability
        - TextBlock model structure confirmed
        - Database schema supports block_containers
      </blockers>
    </phase>

    <phase name="Pre-deployment" duration="1 day">
      <steps>
        1. Code review
           - Review all changes for SOLID principles
           - Check error handling completeness
           - Verify logging quality
           - Estimated: 2-3 hours

        2. Linting and static analysis
           - Run flake8, pylint on modified files
           - Check type hints completeness
           - Fix any warnings
           - Estimated: 1 hour

        3. Integration testing
           - Run full integration test suite
           - Performance benchmarks (100+ files)
           - Memory usage profiling
           - Estimated: 2-3 hours

        4. Database migration script
           - Write backup script
           - Write deletion script
           - Write validation queries
           - Test on copy of production DB
           - Estimated: 2-3 hours

        5. Documentation
           - Document configuration options
           - Document error scenarios and recovery
           - Create runbook for troubleshooting
           - Estimated: 2 hours
      </steps>

      <validation>
        - All linters passing
        - Integration tests 100% passing
        - Performance acceptable (< 5 min for 100 files)
        - Migration scripts tested on DB copy
      </validation>
    </phase>

    <phase name="Deployment" duration="30 minutes">
      <steps>
        1. Backup current state (2 min)
           ```bash
           # Export all LOCAL_FILESYSTEM records
           # Save to safe location
           ```

        2. Deploy code changes (5 min)
           - Git commit with message: "feat: eager content loading for local filesystem connector"
           - Push to develop branch
           - Trigger CI/CD pipeline

        3. Restart connector service (3 min)
           - Stop running connector
           - Verify shutdown in logs
           - Start new version
           - Verify startup in logs

        4. Execute migration (10 min)
           - Delete existing records with backup script
           - Verify deletion
           - Trigger full resync
           - Monitor sync progress

        5. Validate deployment (5 min)
           - Query ArangoDB to confirm records created with content
           - Check logs for errors
           - Spot check 5-10 records manually

        6. Smoke tests (5 min)
           - Test semantic search
           - Test chat source code search
           - Create small test file, verify it's synced and indexed
      </steps>

      <rollback>
        If issues detected:
        1. Stop connector
        2. Restore from backup (command: arangoimport with backup file)
        3. Checkout previous code version
        4. Restart connector
        5. Verify restoration
        6. Investigate root cause before retry
      </rollback>

      <success_criteria>
        - All new records have block_containers.blocks[0].text populated
        - Record count matches expected (700+)
        - No errors in logs
        - Chat/search functionality works
        - Performance acceptable
      </success_criteria>
    </phase>

    <phase name="Post-deployment" duration="ongoing">
      <monitoring>
        1. Log metrics
           - Files processed per hour
           - Content read success rate (%)
           - Average file read time (ms)
           - Errors encountered (categorized)

        2. Database metrics
           - Record count trending
           - Average block_containers size
           - Query performance

        3. Alerts
           - Error rate > 5%
           - Sync failures
           - Performance degradation
           - Database space concerns

        4. Dashboard
           - Records created in last 24h by status
           - Content extraction success rate chart
           - File types distribution
           - Error breakdown
      </monitoring>

      <validation_window>
        1 week: Monitor for issues
        - Zero critical bugs
        - Error rate < 2%
        - Performance stable
        - Chat/search working reliably
      </validation_window>

      <cleanup>
        After 2 weeks stable operation:
        - Delete backup of old records (if no issues)
        - Archive deployment logs
        - Update documentation with lessons learned
      </cleanup>
    </phase>
  </rollout_plan>

  <success_metrics>
    <metric name="Content Population">
      100% of new LOCAL_FILESYSTEM records have block_containers.blocks[0].text populated
      (or explicit failure log if unreadable)
      Measurement: Query ArangoDB, count records without content vs with content
      Target: 99%+ (allow <1% for unreadable files with logged reasons)
    </metric>

    <metric name="Extension Population">
      100% of new records have extension field populated (non-null, non-empty string)
      Measurement: Query extension IS NULL count
      Target: 0 null values
    </metric>

    <metric name="Path Population">
      100% of new records have path field populated with relative paths
      Measurement: Query path IS NULL count
      Target: 0 null values
      Secondary: All paths are relative (not starting with /)
    </metric>

    <metric name="File Size Population">
      100% of new records have size_in_bytes populated correctly
      Measurement: Spot check 10 random records, compare to actual file sizes
      Target: 100% accuracy within 0 bytes
    </metric>

    <metric name="Chat Search Functionality">
      Chat can successfully search and return source code files
      Measurement: Test search for function names, class names, keywords
      Target: Returns 10+ results for code pattern search
    </metric>

    <metric name="Semantic Search">
      Qdrant has embeddings for all LOCAL_FILESYSTEM records with content
      Measurement: Query Qdrant for documents with local-filesystem-created embeddings
      Target: Embedding count == Record count with content
    </metric>

    <metric name="Processing Performance">
      Connector processing time < 5 minutes for 100 files
      Measurement: Log processing start/end timestamps
      Target: < 50ms per file average
    </metric>

    <metric name="Error Logging">
      All errors explicitly logged with file path and reason
      No silent failures (every unreadable file has corresponding log entry)
      Measurement: Log audit for any null content without error message
      Target: 0 unexplained null records
    </metric>

    <metric name="Migration Success">
      After migration, no LOCAL_FILESYSTEM records with null content (except intentional unreadable)
      Measurement: Query Records collection for null content with no corresponding error log
      Target: 0 unexplained nulls
    </metric>

    <metric name="Regression Check">
      No degradation in other connector functionality
      - Record groups still created properly
      - Permissions still assigned correctly
      - Organization IDs correct
      - Other connectors unaffected
      Target: 100% pass rate on regression tests
    </metric>
  </success_metrics>

  <dependencies>
    <dependency type="library">
      chardet (Python encoding detection)
      Required for Phase 1 content reading
      Install: pip install chardet
    </dependency>

    <dependency type="code">
      TextBlock model from app.models.entities
      Must exist and have 'text' field
      Required for Phase 2 block creation
    </dependency>

    <dependency type="database">
      ArangoDB 3.x+ with support for nested object storage
      block_containers field must be persistable
      Required for all phases
    </dependency>

    <dependency type="service">
      Indexing Service (optional improvement, not required)
      Current code will continue to work
      Can be enhanced later to read from block_containers
    </dependency>

    <dependency type="testing">
      Docker containers for ArangoDB and Kafka (for integration tests)
      Required for Phase 3+ testing
    </dependency>

    <dependency type="verification">
      Research phase findings confirmed (required)
      Root cause identified in .prompts/007-connector-missing-content-research/
    </dependency>
  </dependencies>

  <open_questions>
    <question priority="high">
      Should max_file_size_mb be configurable per file type or global limit?
      Current plan: Global limit (10MB default)
      Alternative: Different limits for text vs binary
      Recommendation: Start with global, can enhance later if needed
    </question>

    <question priority="medium">
      How should binary files be handled (PDF, images, compiled code)?
      Current plan: Skip with info log (content=None)
      Alternatives:
        a) Convert to base64 (wastes space)
        b) Extract metadata only
        c) Use libraries to extract text (adds complexity)
      Recommendation: Skip for initial version, can enhance with better detection
    </question>

    <question priority="medium">
      Should existing 700+ records be migrated automatically on deployment?
      Current plan: Manual deletion + resync during deployment window
      Alternative: Automatic background migration (lower disruption, longer to complete)
      Recommendation: Manual for safety, can automate in future versions
    </question>

    <question priority="low">
      Should content be cached/indexed at sync time or on-demand?
      Current plan: Eager loading at sync time (content in memory during sync)
      Trade-off: Higher memory during sync, but immediate availability
      Recommendation: Eager loading is better for local files, revisit if memory becomes issue
    </question>
  </open_questions>

  <assumptions>
    <assumption>
      ArangoDB schema supports storing large text content in block_containers field
      Verification: Query existing records to check field presence and capacity
      Risk: Low (schema already used by Web connector)
    </assumption>

    <assumption>
      File system has adequate performance for reading 700+ files during resync
      Verification: Monitor resync duration during testing
      Risk: Medium (depends on hardware, file sizes, I/O load)
    </assumption>

    <assumption>
      Indexing service can handle records without signedUrlRoute (now using eager loading)
      Verification: No changes needed to indexing service, it reads from DB
      Risk: Low (indexing service already reads from DB)
    </assumption>

    <assumption>
      chardet library can be added to connector dependencies
      Verification: Check Python requirements.txt and Docker build
      Risk: Low (standard library, well-maintained)
    </assumption>

    <assumption>
      Local file paths remain stable between scans
      Verification: No path renaming/moving between sync cycles
      Risk: Medium (users might move files, but that's acceptable - next sync will clean up)
    </assumption>

    <assumption>
      Memory is sufficient for loading content of 700+ files during resync
      Verification: Monitor memory usage during testing
      Risk: Medium (with 10MB limit, 700 files = ~7GB max, need monitoring)
      Mitigation: Implement batching if memory becomes issue
    </assumption>
  </assumptions>

  <risks>
    <risk severity="high">
      <description>
        Memory exhaustion if many large files (close to max_file_size_mb) are processed simultaneously
      </description>
      <probability>medium</probability>
      <impact>Connector crash, sync incomplete, need to retry</impact>
      <mitigation>
        1. Set max_file_size_mb conservatively (10MB default)
        2. Implement batch processing with memory checks
        3. Monitor memory during resync (alert if > 80% heap)
        4. Can increase batch size if memory is not an issue
      </mitigation>
      <monitoring>
        - Heap usage during sync
        - Memory errors in logs
        - Sync completion rate
      </monitoring>
    </risk>

    <risk severity="high">
      <description>
        Large resync takes too long, blocking indexing service from processing new records
      </description>
      <probability>medium</probability>
      <impact>Search functionality degraded during migration, user wait time</impact>
      <mitigation>
        1. Estimate resync time: 100 files = 2-3 min, 700 files = 10-15 min
        2. Schedule migration during low-traffic window if possible
        3. Can skip migration and let incremental syncs populate content (slower but less disruptive)
        4. Monitor resync progress, alert if taking >20 min
      </mitigation>
      <monitoring>
        - Resync duration
        - Record creation rate (files/sec)
        - Indexing service lag
      </monitoring>
    </risk>

    <risk severity="medium">
      <description>
        Encoding detection fails for files with unusual encodings, content not read
      </description>
      <probability>low</probability>
      <impact>Some files won't be indexed (can search metadata but not content)</impact>
      <mitigation>
        1. Chardet library well-tested for common encodings
        2. Fallback to UTF-8 with error handling
        3. Log all encoding failures for audit
        4. User can fix encoding externally and resync
      </mitigation>
      <monitoring>
        - Encoding detection failures in logs
        - Files with content=None due to encoding
      </monitoring>
    </risk>

    <risk severity="medium">
      <description>
        File permissions prevent reading, content not extracted for some files
      </description>
      <probability>low</probability>
      <impact>Some records created with metadata but no content</impact>
      <mitigation>
        1. Log warning with file path and permission error
        2. User can fix permissions externally
        3. Resync will re-read file
        4. Record still useful for metadata search
      </mitigation>
      <monitoring>
        - Permission errors in logs
        - Files with content=None due to permissions
      </monitoring>
    </risk>

    <risk severity="low">
      <description>
        Connector HTTP endpoint (/api/v1/stream/record/{id}) no longer needed
      </description>
      <probability>high</probability>
      <impact>Technical debt, unused code</impact>
      <mitigation>
        1. Keep endpoint for backward compatibility (may be called by indexing service)
        2. Document that it's legacy, not used for new records
        3. Can deprecate in future version
      </mitigation>
      <timeline>Can address in future refactoring</timeline>
    </risk>

    <risk severity="low">
      <description>
        Rollback complex if something goes wrong during migration
      </description>
      <probability>low</probability>
      <impact>Manual restore from backup, lost data if backup fails</impact>
      <mitigation>
        1. Test rollback procedure before deployment
        2. Verify backup integrity
        3. Keep backup for 30 days minimum
        4. Document rollback steps clearly
      </mitigation>
      <monitoring>
        - Backup creation success
        - Backup file integrity checks
      </monitoring>
    </risk>
  </risks>

  <implementation_readiness>
    <requirement status="ready">
      Research phase completed with root cause identified
      Reference: @.prompts/007-connector-missing-content-research/
    </requirement>

    <requirement status="ready">
      Architecture decision made (eager loading)
      Chosen by user during planning phase
    </requirement>

    <requirement status="pending">
      Code review and approval
      Action: Review plan with team before implementation
    </requirement>

    <requirement status="pending">
      Testing environment setup
      Action: Prepare ArangoDB/Kafka/connectors in dev environment
    </requirement>

    <requirement status="pending">
      Backup procedures ready
      Action: Test backup/restore before deployment
    </requirement>

    <requirement status="ready">
      Configuration management designed
      Etcd paths and defaults documented
    </requirement>

    <requirement status="ready">
      Rollout plan documented
      Deployment steps, validation, rollback defined
    </requirement>

    <requirement status="ready">
      Monitoring strategy defined
      Metrics and alerts specified
    </requirement>
  </implementation_readiness>

  <next_steps>
    <step priority="1">
      Review this plan with team for approval
      Check: Are all phases clear? Any missing details?
      Expected: Sign-off and any clarifications before implementation
    </step>

    <step priority="2">
      Prepare testing environment
      Action: Set up local ArangoDB, Kafka, connector
      Verification: Can run integration tests successfully
    </step>

    <step priority="3">
      Begin Phase 1 implementation (content reading)
      Owner: Backend engineer
      Estimated: 6-8 hours with tests
      Deliverable: Merged PR with _read_file_content() method and tests
    </step>

    <step priority="4">
      Begin Phase 2 implementation (record creation)
      Dependency: Phase 1 complete and merged
      Estimated: 4-5 hours with tests
      Deliverable: Merged PR with _create_file_record() modifications
    </step>

    <step priority="5">
      Execute Phase 3 (schema verification)
      Dependency: Phases 1-2 merged
      Estimated: 2-3 hours
      Deliverable: Verification report confirming schema supports new fields
    </step>

    <step priority="6">
      Execute Phase 5 (configuration)
      Can start in parallel with Phase 2-3
      Estimated: 2 hours
      Deliverable: Config reading code and etcd setup
    </step>

    <step priority="7">
      Pre-deployment checklist
      Estimated: 1 day
      Includes: Code review, linting, integration tests, migration scripts
      Deliverable: Green light for production deployment
    </step>

    <step priority="8">
      Production deployment and migration
      Estimated: 30 minutes
      Deliverable: All 700+ records reprocessed with content
    </step>

    <step priority="9">
      Post-deployment validation
      Estimated: 1 week
      Deliverable: Confirmed no issues, metrics stable
    </step>
  </next_steps>
</plan>
