# Summary: Local Filesystem Connector Content Missing - Root Cause

**One-liner**: Local Filesystem connector never sets `signedUrlRoute` in Kafka events, preventing indexing service from fetching file content via HTTP, resulting in zero embeddings despite 700+ metadata-only records.

## The Problem

700+ records created with complete metadata (name, size, extension) but zero content, preventing vector embeddings and search functionality.

## Root Cause

The connector was designed following the cloud storage pattern (Dropbox, OneDrive) which:
1. Stores only metadata in ArangoDB during sync
2. Provides HTTP streaming endpoint for on-demand content access
3. Relies on separate indexing service to fetch content and generate embeddings

**Critical missing piece**: The connector **never sets `fetch_signed_url` field** in the FileRecord, which becomes `signedUrlRoute` in the Kafka event. Without this field:
- Indexing service receives event with `signedUrl: null` and `signedUrlRoute: null`
- Falls back to checking `buffer` field (also null for connector-sourced records)
- Result: `file_content = None`
- Processing fails silently, no embeddings created

**Contrast with Google Drive connector** which properly sets:
```python
"signedUrlRoute": f"{connector_endpoint}/api/v1/{org_id}/{user_id}/drive/record/{file_key}/signedUrl"
```

## Evidence

1. **FileRecord creation** (connector.py:391-411): Never sets `signed_url` or `fetch_signed_url`
2. **Kafka message** (entities.py:241): `signedUrlRoute` field sent as `null`
3. **Indexing service** (events.py:213-219): When `signedUrl` is null, tries `buffer` which is also null for connectors
4. **Google Drive** (drive_sync_service.py:1415): Properly sets `signedUrlRoute` for comparison
5. **stream_record() exists** (connector.py:271): Has working implementation but never told to indexing service

## Why This Fails

Unlike cloud connectors that need lazy loading due to OAuth tokens, network latency, and API rate limits, local filesystem has:
- Direct file system access (no auth needed)
- Fast local I/O (no network latency)
- Already on disk (no external API)

Yet it uses the same lazy loading pattern, creating unnecessary HTTP round-trip dependency.

## Recommended Fixes (in priority order)

### Quick Fix (2 lines of code)
Add `fetch_signed_url` when creating FileRecord:
```python
connector_endpoint = os.getenv("CONNECTOR_SERVICE_URL", "http://localhost:8088")
record.fetch_signed_url = f"{connector_endpoint}/api/v1/stream/record/{record.id}"
```

This tells indexing service where to fetch content via existing `stream_record()` endpoint.

### Better Fix (for local files)
Switch to eager loading pattern (like Web connector):
- Read file content during `_create_file_record()`
- Populate `block_containers` with TextBlock containing content
- Store content directly in ArangoDB
- Eliminate dependency on indexing service HTTP calls

This makes Local Filesystem connector self-contained and aligns with its architectural advantages (direct disk access).

## Verification Needed

1. Query ArangoDB to confirm actual record structure
2. Check indexing service logs for stream_record() call failures
3. Test connector's HTTP endpoint manually
4. Verify Qdrant has zero embeddings for LOCAL_FILESYSTEM records
