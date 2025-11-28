# Connector Missing Content Fix Plan

**One-liner:** 4-phase eager loading implementation: read file content during sync, populate block_containers with TextBlock, migrate 700+ existing records, achieve 100% content population with full test coverage and configurable size limits.

## Version
v1 - Ready for implementation

## Root Cause (from research)
The Local Filesystem connector never sets `fetch_signed_url` field and follows lazy loading pattern (metadata only). This breaks indexing service's ability to fetch content, resulting in zero embeddings despite 700+ records. The connector has `stream_record()` method but never tells indexing service about it.

## Solution Chosen: Eager Loading

**Why:** Local filesystem has unique advantages:
- Direct file system access (no auth needed)
- Files already on disk (fast local I/O)
- No API rate limits or token expiration
- Eliminates inter-service HTTP dependency

Unlike cloud connectors (Dropbox, OneDrive) that need lazy loading for large files and OAuth, local filesystem can read files synchronously during discovery.

## Key Decisions

1. **Implementation Approach**: Eager loading (read content during sync, populate block_containers)
2. **Content Limit**: max_file_size_mb = 10 (configurable, prevents memory exhaustion)
3. **Existing Records**: Delete and resync (clean state, safest approach)
4. **Encoding Handling**: Auto-detect with chardet, fallback to UTF-8
5. **Error Handling**: Non-fatal, log all unreadable files with reason, create records anyway
6. **Field Population**:
   - `extension`: Extract from filename (always)
   - `path`: Relative path from watch_path (always)
   - `size_in_bytes`: From os.stat() (already working)
   - `content`: In block_containers.blocks[0].text (if readable)

## Implementation Phases

### Phase 1: Core Content Reading (6-8 hours)
- Add `_read_file_content()` method with encoding detection
- Use chardet library for auto-detection
- Handle file size limits, permission errors, encoding errors
- All errors logged but non-fatal
- **Deliverable**: Method + unit tests

### Phase 2: Record Creation Modification (4-5 hours)
- Call content reader in `_create_file_record()`
- Set `path` field (relative path)
- Create TextBlock with content, add to block_containers
- Logging for success and failures
- **Deliverable**: Modified method + integration tests

### Phase 3: Database Schema Verification (2-3 hours)
- Verify block_containers persists to ArangoDB
- Verify no field filtering that drops content
- Query database to confirm fields populated
- **Deliverable**: Verification report

### Phase 4: Existing Records Migration (20 minutes)
- Backup 700+ existing records
- Delete all LOCAL_FILESYSTEM records
- Trigger full resync
- Verify all records recreated with content
- **Deliverable**: Migration completed, all records with content

### Phase 5: Configuration Management (2 hours)
- Add config reading for max_file_size_mb
- etcd path: `/services/connectors/localfilesystem/config/{org_id}`
- Defaults: enabled=true, max_file_size_mb=10
- **Deliverable**: Configuration applied

## Testing Strategy

**Unit Tests** (Phase 1-2): 15+ tests for content reading, record creation, error handling
**Integration Tests** (Phase 2-3): Full directory sync, various file types, mixed scenarios
**Database Tests** (Phase 3): Schema verification, field population, content storage
**E2E Tests** (Phase 4): Full pipeline from sync to Qdrant embeddings
**Regression Tests**: Existing functionality (org ID, record groups, permissions)

## Rollout Plan

### Development (2-3 days)
- Implement all 5 phases
- Manual testing with sample files
- Performance testing (100+ files)

### Pre-deployment (1 day)
- Code review
- Linting and static analysis
- Integration test suite
- Database migration scripts tested on copy

### Deployment (30 minutes)
- Backup current state
- Deploy code
- Restart connector
- Delete existing records
- Trigger full resync
- Validate with chat/search

### Post-deployment (1 week)
- Monitor logs and metrics
- Validate semantic search working
- Zero critical bugs before declaring success

## Success Metrics

- ✓ 100% of new records have content populated (or explicit error logged)
- ✓ extension field: 0 null values
- ✓ path field: 0 null values, all relative paths
- ✓ Chat semantic search returns results
- ✓ Processing < 5 minutes for 100 files
- ✓ No regressions in other connectors/features

## Decisions Needed

**None** - User already chose eager loading approach. All other decisions documented in plan.

## Blockers

**None identified** - All dependencies available (chardet, TextBlock model, ArangoDB schema)

## Risks

- **High**: Memory exhaustion with large files
  - Mitigation: 10MB limit, batch processing, monitoring
- **High**: Resync takes too long (could block search during migration)
  - Mitigation: ~10-15 minutes acceptable, schedule during low-traffic
- **Medium**: Encoding detection fails for unusual files
  - Mitigation: Chardet library + UTF-8 fallback, manual fix + resync
- **Medium**: File permissions prevent reading
  - Mitigation: Log all, user can fix externally, resync recovers

## Files Modified

1. `backend/python/app/connectors/sources/local_filesystem/connector.py`
   - Add `_read_file_content()` method (new)
   - Modify `_create_file_record()` (read content, populate path, create TextBlock)
   - Update `__init__()` (read config)

2. No changes needed to:
   - data_source_entities_processor.py (schema already supports)
   - entities.py (FileRecord model already has all fields)
   - Indexing service (works as-is, reads from DB)

## Open Questions

1. Should binary files have special handling? (Current: skip with info log)
2. Should max_file_size_mb vary by file type? (Current: single global limit)
3. Should existing records migrate automatically? (Current: manual during deployment)

All questions documented with recommendations in full plan.

## Next Steps

1. **Approval**: Review plan with team
2. **Setup**: Prepare testing environment
3. **Implement**: Execute phases 1-5 (6-8 days total)
4. **Review**: Code review before deployment
5. **Deploy**: Execute rollout plan (30 min) + validate (1 week)

## Full Plan Reference

See: `.prompts/008-connector-missing-content-plan/connector-missing-content-plan.md`

For implementation execution, see: Create `009-connector-missing-content-fix.md` prompt (next step)
