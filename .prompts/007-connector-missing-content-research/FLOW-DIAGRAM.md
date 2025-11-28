# Data Flow Diagrams: Local Filesystem Connector

## Current Broken Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Local Filesystem Connector                                       │
│                                                                   │
│  _create_file_record(file_path):                                │
│    ├─ os.stat(file_path)                 ✓ Works                │
│    ├─ FileRecord(                                                │
│    │    record_name = "chat.ts"          ✓ Set                  │
│    │    extension = "ts"                 ✓ Set                  │
│    │    size_in_bytes = 4567             ✓ Set                  │
│    │    external_record_id = "/data/..." ✓ Set                  │
│    │    signed_url = None                ❌ NEVER SET           │
│    │    fetch_signed_url = None          ❌ NEVER SET (ROOT CAUSE) │
│    │  )                                                           │
│    └─ return record, permissions                                 │
└─────────────────────────────────────────────────────────────────┘
                    ↓
                    │ on_new_records()
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│ DataSourceEntitiesProcessor                                      │
│                                                                   │
│  - Stores record in ArangoDB (metadata only)                    │
│  - Sends Kafka event to "record-events" topic:                  │
│                                                                   │
│    {                                                             │
│      "eventType": "newRecord",                                   │
│      "payload": {                                                │
│        "recordId": "abc-123",                                    │
│        "extension": "ts",              ✓ Present                │
│        "sizeInBytes": 4567,            ✓ Present                │
│        "signedUrl": null,              ❌ NULL                  │
│        "signedUrlRoute": null          ❌ NULL (BREAKS INDEXING) │
│      }                                                           │
│    }                                                             │
└─────────────────────────────────────────────────────────────────┘
                    ↓
                    │ Kafka
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│ Indexing Service (events.py)                                    │
│                                                                   │
│  async def process_event(event_data):                           │
│                                                                   │
│    signed_url = event_data.get("signedUrl")    # None ❌       │
│                                                                   │
│    if signed_url:                                                │
│      file_content = await download(signed_url)  # SKIPPED      │
│    else:                                                         │
│      file_content = event_data.get("buffer")    # None ❌      │
│                                                                   │
│    # file_content is None!                                      │
│    # Processing fails silently                                  │
│    # No embeddings created                                      │
│    # Record marked as "COMPLETED" anyway                        │
└─────────────────────────────────────────────────────────────────┘
                    ↓
                    │ FAILURE
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│ Result: Records with metadata but NO content                    │
│                                                                   │
│  ArangoDB: 700+ records with extension, size, etc.              │
│  Qdrant: 0 embeddings for LOCAL_FILESYSTEM                      │
│  Search: Completely broken                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Correct Flow (Google Drive for comparison)

```
┌─────────────────────────────────────────────────────────────────┐
│ Google Drive Connector                                           │
│                                                                   │
│  _create_file_record(drive_item):                               │
│    ├─ FileRecord(...)                                           │
│    └─ kafka_event = {                                           │
│         "signedUrlRoute": "http://connector:8088/..."  ✓ SET   │
│       }                                                          │
└─────────────────────────────────────────────────────────────────┘
                    ↓
                    │ Kafka event with signedUrlRoute
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│ Indexing Service                                                 │
│                                                                   │
│  signed_url_route = event_data.get("signedUrlRoute")  ✓ Present│
│                                                                   │
│  # Calls connector endpoint with auth token                     │
│  response = await http_client.get(signed_url_route)             │
│                                                                   │
│  file_content = await response.read()    ✓ Works               │
│                                                                   │
│  # Extract content → Generate embeddings → Store in Qdrant      │
└─────────────────────────────────────────────────────────────────┘
                    ↓
                    │ SUCCESS
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│ Result: Full indexing pipeline completes                        │
│                                                                   │
│  ArangoDB: Records with metadata                                 │
│  Qdrant: Embeddings created                                     │
│  Search: Works perfectly                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Fixed Flow: Solution 0 (Quick Fix)

```
┌─────────────────────────────────────────────────────────────────┐
│ Local Filesystem Connector (FIXED)                              │
│                                                                   │
│  _create_file_record(file_path):                                │
│    ├─ FileRecord(...)                                           │
│    │                                                             │
│    │  # NEW: Set fetch_signed_url                               │
│    ├─ connector_endpoint = env.get("CONNECTOR_SERVICE_URL")     │
│    └─ record.fetch_signed_url =                                 │
│         f"{connector_endpoint}/api/v1/stream/record/{id}"  ✓   │
└─────────────────────────────────────────────────────────────────┘
                    ↓
                    │ Kafka event now has signedUrlRoute
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│ Indexing Service                                                 │
│                                                                   │
│  signed_url_route = event_data.get("signedUrlRoute")           │
│  # → "http://connector:8088/api/v1/stream/record/abc-123"  ✓  │
│                                                                   │
│  response = await http_client.get(signed_url_route)             │
│  # ↓ Calls connector's stream_record() method                   │
└─────────────────────────────────────────────────────────────────┘
                    ↓
                    │ HTTP GET /api/v1/stream/record/abc-123
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│ Connector: stream_record() (line 271)                           │
│                                                                   │
│  async def stream_record(record):                               │
│    file_path = record.external_record_id  # "/data/chat.ts"    │
│                                                                   │
│    if os.path.exists(file_path):          ✓ Check exists       │
│      with open(file_path, 'rb') as f:     ✓ Read content       │
│        yield chunk                         ✓ Stream back        │
└─────────────────────────────────────────────────────────────────┘
                    ↓
                    │ File content streamed
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│ Indexing Service                                                 │
│                                                                   │
│  file_content = await download_stream(response)  ✓ Works       │
│                                                                   │
│  # Extract text → Generate embeddings → Store in Qdrant         │
└─────────────────────────────────────────────────────────────────┘
                    ↓
                    │ SUCCESS
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│ Result: Pipeline works!                                         │
│                                                                   │
│  ArangoDB: Metadata                                              │
│  Qdrant: Embeddings ✓                                          │
│  Search: Works ✓                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Alternative: Solution 1 (Eager Loading)

```
┌─────────────────────────────────────────────────────────────────┐
│ Local Filesystem Connector (EAGER)                              │
│                                                                   │
│  _create_file_record(file_path):                                │
│    ├─ metadata = os.stat(file_path)                             │
│    │                                                             │
│    │  # NEW: Read content immediately                            │
│    ├─ with open(file_path, 'r') as f:                           │
│    │    content = f.read()                ✓ Content in memory  │
│    │                                                             │
│    ├─ record = FileRecord(...)                                  │
│    │                                                             │
│    │  # NEW: Populate blocks                                     │
│    └─ record.block_containers.blocks.append(                    │
│         TextBlock(text=content)           ✓ Content stored     │
│       )                                                          │
└─────────────────────────────────────────────────────────────────┘
                    ↓
                    │ on_new_records() - content already in record
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│ DataSourceEntitiesProcessor                                      │
│                                                                   │
│  - Stores record in ArangoDB WITH content in block_containers   │
│  - Sends Kafka event (content already in DB, can skip fetch)    │
└─────────────────────────────────────────────────────────────────┘
                    ↓
                    │ Kafka (or direct to indexing)
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│ Indexing Service                                                 │
│                                                                   │
│  # Can read content from ArangoDB directly                      │
│  # OR receive content in Kafka event                            │
│                                                                   │
│  file_content = record.block_containers.blocks[0].text  ✓      │
│                                                                   │
│  # Generate embeddings → Store in Qdrant                        │
└─────────────────────────────────────────────────────────────────┘
                    ↓
                    │ SUCCESS (simpler flow)
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│ Result: Self-contained connector                                │
│                                                                   │
│  - No HTTP dependency                                            │
│  - Content stored in DB                                         │
│  - Faster for small files                                       │
│  - Simpler architecture                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Differences

| Aspect | Current (Broken) | Quick Fix | Eager Loading |
|--------|------------------|-----------|---------------|
| **Content Reading** | Never | On HTTP request | During sync |
| **fetch_signed_url** | ❌ null | ✓ Set | Not needed |
| **HTTP Dependency** | ❌ Fails | ✓ Required | Not needed |
| **Memory Usage** | Low | Low | Higher |
| **Architecture** | Cloud pattern | Cloud pattern | Local pattern |
| **Code Changes** | N/A | 2 lines | ~30 lines |
| **Works for large files** | No | Yes | Maybe (memory limits) |

---

## Recommendation

**For immediate fix**: Use Solution 0 (set `fetch_signed_url`)
- Minimal code change
- Uses existing infrastructure
- Proven pattern from other connectors

**For long-term**: Consider Solution 1 (eager loading)
- Better suited for local files
- Simpler architecture
- No inter-service dependencies
- But need to handle large files (>100MB)
