# Phase 1: Research Findings - Hupyy Verification Integration

## Current Chat Flow Analysis

### Frontend Chat Flow (`chat-bot.tsx`)

**Message Submission Flow:**
1. User submits query via `ChatInput` component
2. `handleSendMessage()` is called with query, filters, model selection
3. Temporary user message created and added to conversation
4. Request sent to backend streaming endpoint:
   - New conversation: `POST /api/v1/conversations/stream`
   - Existing conversation: `POST /api/v1/conversations/:conversationId/messages/stream`
5. SSE stream processed with events: `connected`, `status`, `answer_chunk`, `complete`, `error`
6. `StreamingManager` handles per-conversation state and message accumulation
7. Final `complete` event contains full conversation with citations

**Request Payload:**
```typescript
{
  query: string,
  modelKey?: string,
  modelName?: string,
  chatMode?: string,
  filters: { apps: string[], kb: string[] }
}
```

**Key Observations:**
- NO verification_enabled parameter in current payload
- Citations processed in `processStreamingContentLegacy()` utility
- Citations stored in message: `citations: CustomCitation[]`
- No verification metadata in citation interface

### Backend Query Processing (`es_controller.ts` -> Python backend)

**NodeJS Middleware (`streamChat`):**
1. Receives streaming request at `/api/v1/conversations/stream`
2. Creates initial conversation record in MongoDB
3. Proxies request to Python AI backend: `POST ${aiBackend}/api/v1/chat/stream`
4. Streams events back to frontend (answer_chunk, status, etc.)
5. On `complete` event: saves conversation with citations to MongoDB

**Python Chat Endpoint (`/api/v1/chat/stream`):**
- File: `/backend/python/app/api/routes/chatbot.py`
- Entry point: `process_chat_query_with_status()`
- Flow:
  1. Get LLM based on modelKey/modelName
  2. Decompose/expand query (QueryDecompositionExpansionService)
  3. Retrieve documents (RetrievalService)
  4. Rerank results (RerankerService)
  5. Generate answer with LLM
  6. Process citations (`process_citations()` from `utils/citations.py`)
  7. Stream response as SSE events

**Key Integration Points:**
- **Current:** No verification triggering in query processing flow
- **Needed:** After retrieval/reranking, publish chunks to Kafka `verify_chunks` topic
- **Needed:** Include verification results in response metadata

### Verification Backend Infrastructure (Already Exists)

**Kafka Orchestrator (`backend/python/app/verification/orchestrator.py`):**
- Consumes from: `verify_chunks` topic
- Produces to: `verification_complete`, `verification_failed` topics
- Uses `HupyyClient` with circuit breaker for SMT verification
- Handles parallel verification (max concurrency: 5)
- Publishes results with metadata:
  ```python
  {
    request_id, chunk_index, verdict, confidence,
    formalization_similarity, extraction_degradation,
    failure_mode, formal_text, smt_lib_code, model, metrics
  }
  ```

**Hupyy Client (`backend/python/app/verification/hupyy_client.py`):**
- API: `https://verticalslice-smt-service-gvav8.ondigitalocean.app`
- Methods: `verify()`, `verify_parallel()`
- Circuit breaker protection
- Redis caching for results

### Frontend Verification Components (Already Exist, Not Integrated)

**Available Components:**
1. **HupyyControls** (`hupyy-controls.tsx`):
   - Checkbox to enable/disable verification
   - Props: `enabled`, `onToggle`, `disabled`
   - NOT imported/rendered in `chat-bot.tsx`

2. **VerificationProgress** (`verification-progress.tsx`):
   - Progress bar, completed/failed/pending chips
   - Shows percentage completion
   - NOT integrated into chat UI

3. **VerificationMetadata** (`verification-metadata.tsx`):
   - Expandable verdict badge (SAT/UNSAT/UNKNOWN/ERROR)
   - Shows confidence, formalization similarity, extraction quality
   - Displays formal text, SMT-LIB code, metrics
   - NOT integrated with citations

4. **useVerification Hook** (`use-verification.ts`):
   - State: `enabled`, `inProgress`, `progress`, `error`
   - Methods: `toggleVerification`, `startVerification`, `updateProgress`, `setError`, `reset`
   - localStorage persistence for `enabled` state

### Citation Data Structure

**CustomCitation Interface (`types/chat-bot.ts`):**
```typescript
interface CustomCitation {
  id: string;
  _id: string;
  citationId: string;
  content: string;
  metadata: Metadata;
  orgId: string;
  citationType: string;
  createdAt: string;
  updatedAt: string;
  chunkIndex: number;
}
```

**Missing Verification Fields:**
- NO `verificationResult` field
- NO `verdict`, `confidence`, `formalization_similarity` fields
- Need to extend interface or add nested `verification` object

### Database Schema Analysis

**MongoDB (NodeJS Backend):**
- Collection: `conversations`
- Schema: `IConversation` with `messages: IMessage[]`
- Each message has `citations: IMessageCitation[]`
- **No verification fields in citation schema**

**Qdrant (Python Backend):**
- Used for vector similarity search
- Metadata stored with chunks
- **No verification metadata currently stored**

**ArangoDB (Python Backend):**
- Used for graph relationships and full record storage
- **No verification integration**

## Key Gaps Identified

### 1. Chat UI Integration
- HupyyControls NOT rendered in chat-bot.tsx
- No verification state management in ChatInterface
- No verification flag passed to backend API

### 2. Backend Query Integration
- Python chatbot endpoint does NOT accept `verification_enabled` parameter
- No Kafka publish to `verify_chunks` topic during query processing
- No consumption of `verification_complete` events
- No verification results included in response

### 3. Metadata Display
- Citations do NOT include verification results
- No VerificationMetadata component in sources-citations
- No badges showing SAT/UNSAT verdicts

### 4. Progress Indicators
- No VerificationProgress component in chat UI
- No WebSocket/polling for real-time updates
- No status updates during verification

### 5. Data Flow
Current flow: `Query -> Retrieval -> LLM -> Citations`
Needed flow: `Query -> Retrieval -> LLM -> Citations -> (if enabled) Verify -> Enriched Citations`

## Files Requiring Modification

### Frontend
1. `/frontend/src/sections/qna/chatbot/chat-bot.tsx` - Add HupyyControls, verification state
2. `/frontend/src/sections/qna/chatbot/components/chat-input.tsx` - Pass verification flag
3. `/frontend/src/sections/qna/chatbot/components/sources-citations.tsx` - Add verification badges
4. `/frontend/src/sections/qna/chatbot/components/chat-message.tsx` - Show progress, metadata
5. `/frontend/src/types/chat-bot.ts` - Extend CustomCitation with verification fields
6. `/frontend/src/hooks/use-verification.ts` - (Already exists, may need enhancements)

### Backend - NodeJS
1. `/backend/nodejs/apps/src/modules/enterprise_search/controller/es_controller.ts` - Accept verification_enabled
2. `/backend/nodejs/apps/src/modules/enterprise_search/types/conversation.interfaces.ts` - Extend citation interface
3. `/backend/nodejs/apps/src/modules/enterprise_search/validators/es_validators.ts` - Add verification validation

### Backend - Python
1. `/backend/python/app/api/routes/chatbot.py` - Accept verification_enabled, publish to Kafka
2. `/backend/python/app/utils/citations.py` - Attach verification results to citations
3. Create new file: `/backend/python/app/verification/kafka_publisher.py` - Publish verification requests
4. Create new file: `/backend/python/app/verification/result_aggregator.py` - Aggregate verification results

## Next Steps (Phase 2)

Create detailed implementation plan with:
1. Step-by-step tasks for each integration point
2. Acceptance criteria per task
3. Test strategy
4. Error handling approach
