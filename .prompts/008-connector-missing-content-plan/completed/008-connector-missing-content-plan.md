# Plan: Fix Local Filesystem Connector Content Extraction

## Objective

Create detailed implementation plan to fix missing content issue in Local Filesystem connector based on root cause analysis from research phase.

Plan must be actionable, testable, and ensure content, extension, filePath, and fileSize are properly populated in all records.

## Context

### Research Foundation
Read the completed research: @.prompts/007-connector-missing-content-research/connector-missing-content-research.md

Base all planning on verified root cause and code analysis from research.

### Current System State
- Organization ID: Fixed (correct org)
- Record creation: Working (700+ records)
- Record groups: Working (directory structure)
- **Content extraction: Broken** (null for all fields)

### Success Criteria for Fix
After implementation:
- All new records have `content` populated with file contents
- All new records have `extension` extracted from filename
- All new records have `filePath` with absolute path
- All new records have `fileSize` in bytes
- Existing null records can be reprocessed
- Chat can search and analyze source code

## Requirements

### Phase 1: Solution Design

Based on research root cause, design the fix:

1. **Architecture Decision**
   - Where to implement: connector.py vs watcher.py vs processor.py
   - When to extract: During discovery vs during record creation
   - How to handle errors: Retry vs skip vs partial save

2. **Implementation Approach**
   - Option A: Add content extraction to existing record creation
   - Option B: Create separate content extraction pipeline
   - Option C: Delegate to indexing service
   - **Decision:** Choose with justification based on research

3. **Data Flow Design**
   ```
   File discovered → Content read → Metadata extracted → Record created → Database write
                    [WHERE?]       [WHERE?]            [MODIFY?]        [VERIFY?]
   ```

   For each step, specify:
   - File and function to modify
   - Input/output
   - Error handling

### Phase 2: Implementation Breakdown

Create phased implementation plan:

#### Phase 1: Core Content Extraction
- **Goal:** Read file content and populate content field
- **Files to modify:** List with line number ranges
- **New functions:** Function signatures with docstrings
- **Dependencies:** Libraries needed (mimetypes, pathlib, etc.)
- **Error handling:** Try/except strategy
- **Testing:** How to verify this phase works

#### Phase 2: Metadata Extraction
- **Goal:** Extract extension, filePath, fileSize
- **Files to modify:** List with line number ranges
- **Logic:**
  - Extension: `Path(filename).suffix`
  - FilePath: Absolute path resolution
  - FileSize: `os.path.getsize()` or `Path.stat().st_size`
- **Edge cases:** Hidden files, symlinks, permission errors
- **Testing:** Verification queries

#### Phase 3: Record Schema Updates
- **Goal:** Ensure all fields written to database
- **Files to check:** data_source_entities_processor.py
- **Verification:** Record upsert includes new fields
- **Database schema:** Confirm ArangoDB schema supports fields
- **Testing:** Query database after creation

#### Phase 4: Existing Record Migration
- **Goal:** Reprocess 700+ existing records with null content
- **Approach:**
  - Option A: Delete and resync
  - Option B: Update in place by re-reading files
  - Option C: Background job to backfill
- **Decision:** Choose with pros/cons
- **Implementation:** Script or API endpoint
- **Verification:** Count records with/without content

### Phase 3: Error Handling Strategy

Define how to handle each failure mode:

1. **File Read Errors**
   - Permission denied → Log warning, mark record as failed
   - File not found → Skip (deleted since discovery)
   - File too large → Configurable size limit, stream or skip
   - Binary files → Store as base64 or skip based on MIME

2. **Encoding Issues**
   - Non-UTF8 files → Detect encoding, convert or skip
   - Binary content → Identify MIME type, handle appropriately

3. **Database Errors**
   - Content too large for ArangoDB → Chunk or store reference
   - Transaction failures → Retry logic

### Phase 4: Configuration

Design configuration options:

```yaml
local_filesystem:
  content_extraction:
    enabled: true
    max_file_size_mb: 10
    supported_mime_types:
      - text/*
      - application/json
      - application/javascript
    encoding_fallback: utf-8
    skip_binary: false
```

Specify:
- Where config is stored (etcd path)
- How to read in code
- Default values
- Backward compatibility

### Phase 5: Testing Strategy

Define comprehensive test plan:

#### Unit Tests
- Test content extraction with sample files
- Test metadata extraction (extension, path, size)
- Test error handling (missing file, permission denied)
- Test encoding detection

#### Integration Tests
- Create test file in watch directory
- Verify record created with content
- Query database to confirm fields populated
- Test with various file types (txt, ts, md, json)

#### End-to-End Test
- Sync full directory
- Verify all records have content
- Test chat search functionality
- Confirm semantic search returns results

#### Regression Tests
- Ensure organization ID still correct
- Verify record groups still work
- Check that sync performance acceptable

### Phase 6: Rollout Plan

Define deployment strategy:

1. **Development Testing**
   - Local environment setup
   - Test data preparation
   - Validation criteria

2. **Staging Deployment**
   - Deploy to staging (if applicable)
   - Run full test suite
   - Performance benchmarks

3. **Production Deployment**
   - Backup existing data
   - Deploy code changes
   - Restart connector service
   - Trigger resync or migration
   - Monitor logs for errors
   - Verify chat functionality

4. **Rollback Plan**
   - Revert code changes
   - Restore data backup (if needed)
   - Restart service
   - Verification steps

### Phase 7: Monitoring & Validation

Post-deployment checks:

1. **Immediate Validation**
   - Count records with content vs null
   - Check file size distribution
   - Verify extensions populated
   - Test sample files manually

2. **Ongoing Monitoring**
   - Log metrics: Files processed, errors, avg processing time
   - Alert on: High error rate, content extraction failures
   - Dashboard: Records by status, content size, file types

3. **Success Metrics**
   - 100% of new records have content (or explicit failure reason)
   - Chat returns source code results
   - Semantic search functional
   - No performance degradation

## Output Specification

Write plan to: `.prompts/008-connector-missing-content-plan/connector-missing-content-plan.md`

### Required Structure

```xml
<plan>
  <metadata>
    <topic>Fix Local Filesystem Connector Content Extraction</topic>
    <date>YYYY-MM-DD</date>
    <based_on>@.prompts/007-connector-missing-content-research/connector-missing-content-research.md</based_on>
    <confidence>high|medium|low</confidence>
  </metadata>

  <executive_summary>
    One paragraph: What will be implemented, how, and expected outcome.
  </executive_summary>

  <root_cause_recap>
    Brief summary from research - what's broken and why
  </root_cause_recap>

  <solution_design>
    <architecture_decision>
      Chosen approach with justification
    </architecture_decision>

    <data_flow>
      Step-by-step flow from file → database with file:line references
    </data_flow>

    <alternatives_considered>
      Other approaches and why they were rejected
    </alternatives_considered>
  </solution_design>

  <implementation_phases>
    <phase number="1" name="Core Content Extraction">
      <goal>What this phase accomplishes</goal>

      <files_to_modify>
        <file path="backend/python/app/connectors/sources/local_filesystem/connector.py">
          <changes>
            - Add content reading in process_file() method
            - Handle encoding detection
            - Add error logging
          </changes>
          <line_ranges>123-145, 200-220</line_ranges>
        </file>
      </files_to_modify>

      <new_code_required>
        <function name="read_file_content">
          <signature>def read_file_content(file_path: Path, max_size_mb: int = 10) -> Optional[str]</signature>
          <purpose>Read file with size limit and encoding detection</purpose>
          <returns>File content as string or None if error</returns>
        </function>
      </new_code_required>

      <dependencies>
        <library>chardet</library> <!-- For encoding detection -->
      </dependencies>

      <testing>
        How to verify this phase: Unit tests, sample files
      </testing>

      <estimated_effort>X hours/days</estimated_effort>
    </phase>

    <!-- Repeat for each phase -->
  </implementation_phases>

  <error_handling>
    <scenario type="file_read_error">
      <handling>Log warning, set content to null, mark as failed</handling>
      <recovery>Manual retry or resync</recovery>
    </scenario>

    <!-- Define each error scenario -->
  </error_handling>

  <configuration>
    <config_location>/services/connectors/localfilesystem/config/{orgId}</config_location>

    <new_settings>
      <setting name="content_extraction_enabled">
        <type>boolean</type>
        <default>true</default>
        <description>Enable/disable content extraction</description>
      </setting>

      <setting name="max_file_size_mb">
        <type>integer</type>
        <default>10</default>
        <description>Skip files larger than this</description>
      </setting>
    </new_settings>
  </configuration>

  <testing_strategy>
    <unit_tests>
      - test_read_file_content_success
      - test_read_file_content_large_file
      - test_extract_metadata
      - test_encoding_detection
    </unit_tests>

    <integration_tests>
      - test_create_record_with_content
      - test_multiple_file_types
      - test_error_handling
    </integration_tests>

    <e2e_tests>
      - test_full_directory_sync
      - test_chat_source_code_search
      - test_semantic_search_results
    </e2e_tests>
  </testing_strategy>

  <migration_plan>
    <existing_records count="700+">
      <approach>Delete and resync | Update in place | Background job</approach>
      <rationale>Why this approach chosen</rationale>
      <steps>
        <step>1. Backup current records</step>
        <step>2. Delete records with null content</step>
        <step>3. Trigger full resync</step>
        <step>4. Verify content populated</step>
      </steps>
      <estimated_time>X minutes</estimated_time>
    </existing_records>
  </migration_plan>

  <rollout_plan>
    <phase name="Development">
      <steps>
        1. Implement changes
        2. Run unit tests
        3. Manual testing with sample files
      </steps>
    </phase>

    <phase name="Deployment">
      <steps>
        1. Backup data
        2. Deploy code
        3. Restart service
        4. Trigger migration
        5. Validate results
      </steps>
      <rollback>Revert steps if validation fails</rollback>
    </phase>
  </rollout_plan>

  <success_metrics>
    <metric>100% of new records have content or explicit failure reason</metric>
    <metric>Chat returns source code search results</metric>
    <metric>Semantic search functional</metric>
    <metric>Processing time < 1s per file</metric>
  </success_metrics>

  <dependencies>
    <dependency>Research findings confirmed root cause</dependency>
    <dependency>Code changes approved</dependency>
    <dependency>Testing environment available</dependency>
  </dependencies>

  <open_questions>
    <question>Should we process existing 700+ records or delete and resync?</question>
    <question>What's acceptable file size limit?</question>
  </open_questions>

  <assumptions>
    <assumption>ArangoDB schema supports storing large text content</assumption>
    <assumption>File system has adequate performance for reading files</assumption>
  </assumptions>

  <risks>
    <risk severity="medium">
      <description>Large files could slow down processing</description>
      <mitigation>Implement size limit and async reading</mitigation>
    </risk>

    <risk severity="low">
      <description>Encoding detection might fail for some files</description>
      <mitigation>Fallback to UTF-8 with error handling</mitigation>
    </risk>
  </risks>
</plan>
```

### Quality Requirements

- Plan must be implementation-ready (developer can code directly from it)
- All file:line references must be specific
- Error scenarios must have defined handling
- Testing strategy must be comprehensive
- Rollout must have clear rollback plan

## Create SUMMARY.md

Write: `.prompts/008-connector-missing-content-plan/SUMMARY.md`

### Structure

```markdown
# Connector Missing Content Fix Plan

**One-liner:** [Substantive description - e.g., "4-phase implementation: content extraction → metadata → schema → migration with full test coverage"]

## Version
v1

## Key Decisions
- [Implementation approach chosen]
- [Migration strategy for existing records]
- [Configuration defaults]

## Decisions Needed
- [User choices required before implementation]

## Blockers
- [External dependencies if any]

## Next Step
Execute connector-missing-content-fix.md to implement solution
```

## Success Criteria

- Implementation broken into clear phases
- All code changes specified with file:line
- Error handling strategy defined
- Testing plan comprehensive
- Migration approach decided
- Rollout plan with rollback defined
- SUMMARY.md created with actionable next steps
- Plan suitable for implementation phase (next prompt)
