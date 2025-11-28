# Phase 2: Implementation Plan - Hupyy Verification Integration

## Overview

This plan implements Hupyy SMT verification integration into the chat UI following TDD, SOLID principles, and strong typing as required by CLAUDE.md.

## Architecture Decisions

### 1. Verification Flow Pattern
**Async Non-Blocking:** Verification happens asynchronously after answer generation to avoid blocking UX.

```
User Query -> Retrieval -> Answer -> Stream to Frontend
                                  \
                                   -> (if enabled) Publish to Kafka -> Hupyy Verification
                                                                     \
                                                                      -> Results via WebSocket/Polling
```

### 2. Data Model Extension
**Extend CustomCitation Interface:**
```typescript
interface VerificationMetadata {
  verdict: VerificationVerdict;
  confidence: number;
  formalization_similarity: number;
  extraction_degradation: number;
  failure_mode?: FailureMode;
  formal_text?: string;
  smt_lib_code?: string;
  model?: Record<string, unknown>;
  metrics?: {
    formalization_attempts: number;
    extraction_attempts: number;
    total_execution_time: number;
  };
}

interface CustomCitation {
  // ... existing fields
  verification?: VerificationMetadata; // NEW
}
```

### 3. Real-time Updates Strategy
**Option A: WebSocket (Preferred)**
- Use existing Socket.io infrastructure
- Create verification namespace
- Emit progress events to specific conversation

**Option B: Polling**
- Frontend polls backend every 5 seconds
- Check verification status by conversation ID

**Decision: Start with Option A (WebSocket), fallback to Option B if time-constrained**

## Implementation Phases

## Phase 3.1: Chat UI Integration (Frontend)

### Task 3.1.1: Add Verification State to ChatInterface
**File:** `/frontend/src/sections/qna/chatbot/chat-bot.tsx`

**Test First:**
```typescript
// __tests__/chat-bot.verification.test.tsx
describe('ChatInterface Verification Integration', () => {
  it('should render HupyyControls checkbox', () => {
    // Test that checkbox is visible
  });

  it('should persist verification state to localStorage', () => {
    // Toggle checkbox, verify localStorage updated
  });

  it('should pass verification_enabled to backend API', () => {
    // Mock API, send message, verify payload includes verification flag
  });
});
```

**Implementation:**
1. Import verification hook and components:
   ```typescript
   import { useVerification } from 'src/hooks/use-verification';
   import { HupyyControls } from 'src/sections/knowledgebase/components/verification';
   ```

2. Add verification state to ChatInterface:
   ```typescript
   const verification = useVerification();
   ```

3. Render HupyyControls below ChatInput (when not showing welcome):
   ```typescript
   <Box sx={{ px: 2, pb: 1 }}>
     <HupyyControls
       enabled={verification.state.enabled}
       onToggle={verification.toggleVerification}
       disabled={isCurrentConversationLoading}
     />
   </Box>
   ```

4. Pass verification flag in handleSendMessage:
   ```typescript
   const streamingUrl = /* ... */;
   await handleStreamingResponse(streamingUrl, {
     query: trimmedInput,
     modelKey: selectedModel?.modelKey,
     modelName: selectedModel?.modelName,
     chatMode,
     filters: filters || currentFilters,
     verification_enabled: verification.state.enabled, // NEW
   }, wasCreatingNewConversation);
   ```

**Acceptance Criteria:**
- [ ] Checkbox visible in chat UI below input
- [ ] Checkbox state persists across page reloads
- [ ] verification_enabled flag sent in API request when enabled
- [ ] All existing tests pass
- [ ] ESLint/Prettier passing

---

### Task 3.1.2: Display Verification Progress
**File:** `/frontend/src/sections/qna/chatbot/components/chat-message.tsx`

**Test First:**
```typescript
describe('ChatMessage Verification Progress', () => {
  it('should show VerificationProgress when verification in progress', () => {
    // Mock verification state with inProgress=true
  });

  it('should update progress bar as chunks complete', () => {
    // Simulate progress updates, verify UI updates
  });
});
```

**Implementation:**
1. Import VerificationProgress component
2. Pass verification state as prop from ChatMessagesArea
3. Render progress indicator above citations when `verification.state.inProgress === true`:
   ```typescript
   {verification.state.inProgress && verification.state.progress && (
     <VerificationProgress progress={verification.state.progress} />
   )}
   ```

**Acceptance Criteria:**
- [ ] Progress bar appears during verification
- [ ] Shows completed/failed/pending counts
- [ ] Updates in real-time as verification proceeds
- [ ] Disappears when verification completes

---

### Task 3.1.3: Add Verification Badges to Citations
**File:** `/frontend/src/sections/qna/chatbot/components/sources-citations.tsx`

**Test First:**
```typescript
describe('SourcesCitations Verification Badges', () => {
  it('should display SAT badge for verified citation', () => {
    // Mock citation with verification.verdict = 'sat'
  });

  it('should display UNSAT badge for failed verification', () => {
    // Mock citation with verification.verdict = 'unsat'
  });

  it('should show metadata drawer on badge click', () => {
    // Click badge, verify drawer opens with details
  });
});
```

**Implementation:**
1. Import VerificationMetadata component
2. For each citation, check if `citation.verification` exists
3. If exists, render VerificationMetadata inline with citation:
   ```typescript
   {citation.verification && (
     <VerificationMetadata result={citation.verification} />
   )}
   ```

**Acceptance Criteria:**
- [ ] Verdict badges visible on citations with verification results
- [ ] Badge color matches verdict (green=SAT, red=UNSAT, yellow=UNKNOWN)
- [ ] Clicking badge expands metadata details
- [ ] No badges shown for unverified citations
- [ ] Graceful degradation if verification fails

---

### Task 3.1.4: Extend TypeScript Types
**File:** `/frontend/src/types/chat-bot.ts`

**Test First:**
```typescript
// Type tests (compile-time verification)
describe('CustomCitation Type Extensions', () => {
  it('should accept verification metadata', () => {
    const citation: CustomCitation = {
      // ... existing fields
      verification: {
        verdict: VerificationVerdict.SAT,
        confidence: 0.95,
        formalization_similarity: 0.92,
        extraction_degradation: 0.03,
      }
    };
    expect(citation.verification).toBeDefined();
  });
});
```

**Implementation:**
1. Import verification types:
   ```typescript
   import type { VerificationResult } from './verification.types';
   ```

2. Extend CustomCitation interface:
   ```typescript
   export interface CustomCitation {
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
     verification?: VerificationResult; // NEW - Optional, only present if verified
   }
   ```

**Acceptance Criteria:**
- [ ] TypeScript compiles without errors
- [ ] No `any` types used
- [ ] verification field optional (backward compatible)
- [ ] Type definitions exported correctly

---

## Phase 3.2: Backend Query Integration (NodeJS + Python)

### Task 3.2.1: Accept verification_enabled in NodeJS Controller
**File:** `/backend/nodejs/apps/src/modules/enterprise_search/controller/es_controller.ts`

**Test First:**
```typescript
describe('streamChat verification parameter', () => {
  it('should accept verification_enabled in request body', async () => {
    const req = mockRequest({ body: { query: 'test', verification_enabled: true } });
    // Verify parameter is passed to Python backend
  });
});
```

**Implementation:**
1. Update streamChat function to extract verification_enabled:
   ```typescript
   const aiPayload = {
     query: req.body.query,
     previousConversations: req.body.previousConversations || [],
     recordIds: req.body.recordIds || [],
     filters: req.body.filters || {},
     modelKey: req.body.modelKey || null,
     modelName: req.body.modelName || null,
     chatMode: req.body.chatMode || 'standard',
     verification_enabled: req.body.verification_enabled || false, // NEW
   };
   ```

2. Forward to Python backend (already happens via aiCommandOptions)

**Acceptance Criteria:**
- [ ] verification_enabled parameter accepted
- [ ] Parameter forwarded to Python AI backend
- [ ] Unit tests passing
- [ ] Integration tests with mock backend

---

### Task 3.2.2: Validate verification_enabled Parameter
**File:** `/backend/nodejs/apps/src/modules/enterprise_search/validators/es_validators.ts`

**Test First:**
```typescript
describe('enterpriseSearchCreateSchema validation', () => {
  it('should accept valid verification_enabled boolean', () => {
    const result = enterpriseSearchCreateSchema.validate({
      query: 'test',
      verification_enabled: true
    });
    expect(result.error).toBeUndefined();
  });

  it('should reject non-boolean verification_enabled', () => {
    const result = enterpriseSearchCreateSchema.validate({
      query: 'test',
      verification_enabled: 'yes' // Invalid
    });
    expect(result.error).toBeDefined();
  });
});
```

**Implementation:**
```typescript
export const enterpriseSearchCreateSchema = Joi.object({
  query: Joi.string().required(),
  previousConversations: Joi.array().optional(),
  recordIds: Joi.array().optional(),
  filters: Joi.object().optional(),
  modelKey: Joi.string().optional(),
  modelName: Joi.string().optional(),
  chatMode: Joi.string().optional(),
  verification_enabled: Joi.boolean().optional().default(false), // NEW
});
```

**Acceptance Criteria:**
- [ ] Schema accepts boolean verification_enabled
- [ ] Defaults to false if omitted
- [ ] Rejects invalid types
- [ ] Validation tests pass

---

### Task 3.2.3: Extend Citation Interface in NodeJS
**File:** `/backend/nodejs/apps/src/modules/enterprise_search/types/conversation.interfaces.ts`

**Implementation:**
```typescript
export interface IVerificationMetadata {
  verdict: 'sat' | 'unsat' | 'unknown' | 'error';
  confidence: number;
  formalization_similarity: number;
  extraction_degradation: number;
  failure_mode?: string;
  formal_text?: string;
  smt_lib_code?: string;
  model?: Record<string, any>;
  metrics?: {
    formalization_attempts: number;
    extraction_attempts: number;
    total_execution_time: number;
  };
}

export interface IMessageCitation {
  citationId: string;
  citationData?: ICitation;
  citationType?: string;
  verification?: IVerificationMetadata; // NEW
}
```

**Acceptance Criteria:**
- [ ] TypeScript compiles
- [ ] Interface matches frontend types
- [ ] Optional field (backward compatible)

---

### Task 3.2.4: Python Backend - Accept verification_enabled
**File:** `/backend/python/app/api/routes/chatbot.py`

**Test First:**
```python
def test_chat_query_accepts_verification_enabled():
    query = ChatQuery(
        query="test",
        verification_enabled=True
    )
    assert query.verification_enabled is True

def test_chat_query_defaults_verification_disabled():
    query = ChatQuery(query="test")
    assert query.verification_enabled is False
```

**Implementation:**
1. Update ChatQuery model:
   ```python
   class ChatQuery(BaseModel):
       query: str
       limit: Optional[int] = 50
       previousConversations: List[Dict] = []
       filters: Optional[Dict[str, Any]] = None
       retrievalMode: Optional[str] = "HYBRID"
       quickMode: Optional[bool] = False
       modelKey: Optional[str] = None
       modelName: Optional[str] = None
       chatMode: Optional[str] = "standard"
       mode: Optional[str] = "json"
       verification_enabled: Optional[bool] = False  # NEW
   ```

2. Pass to processing function:
   ```python
   async def process_chat_query_with_status(
       query_info: ChatQuery,
       # ... other params
       verification_enabled: bool = False,  # NEW
   ):
       # ... existing code
   ```

**Acceptance Criteria:**
- [ ] Pydantic model accepts verification_enabled
- [ ] Defaults to False
- [ ] Unit tests pass
- [ ] Type hints correct

---

### Task 3.2.5: Publish Verification Requests to Kafka
**File:** `/backend/python/app/verification/kafka_publisher.py` (NEW)

**Test First:**
```python
@pytest.mark.asyncio
async def test_publish_verification_requests():
    publisher = VerificationKafkaPublisher("localhost:9092")
    await publisher.start()

    chunks = [
        {"content": "test chunk 1", "chunk_id": "c1"},
        {"content": "test chunk 2", "chunk_id": "c2"},
    ]

    await publisher.publish_verification_requests(
        chunks=chunks,
        query="test query",
        conversation_id="conv123",
        org_id="org1",
        user_id="user1"
    )

    # Verify messages published to Kafka
    assert mock_kafka_producer.send.call_count == 2
```

**Implementation:**
```python
from typing import Any, Dict, List
from datetime import datetime
from aiokafka import AIOKafkaProducer
import json
import logging

class VerificationKafkaPublisher:
    """Publishes verification requests to Kafka verify_chunks topic."""

    def __init__(
        self,
        kafka_brokers: str,
        logger: Optional[logging.Logger] = None
    ):
        self.kafka_brokers = kafka_brokers
        self.logger = logger or logging.getLogger(__name__)
        self.producer: Optional[AIOKafkaProducer] = None

    async def start(self) -> None:
        """Initialize Kafka producer."""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.kafka_brokers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()
        self.logger.info("Verification Kafka publisher started")

    async def stop(self) -> None:
        """Stop Kafka producer."""
        if self.producer:
            await self.producer.stop()

    async def publish_verification_requests(
        self,
        chunks: List[Dict[str, Any]],
        query: str,
        conversation_id: str,
        org_id: str,
        user_id: str,
    ) -> None:
        """
        Publish verification requests for each chunk.

        Args:
            chunks: List of retrieved chunks with content and metadata
            query: Original user query (NL)
            conversation_id: Conversation ID
            org_id: Organization ID
            user_id: User ID
        """
        if not self.producer:
            raise RuntimeError("Publisher not started")

        request_id = f"{conversation_id}-{datetime.utcnow().timestamp()}"
        total_chunks = len(chunks)

        for idx, chunk in enumerate(chunks):
            message = {
                "request_id": request_id,
                "chunk_index": idx,
                "total_chunks": total_chunks,
                "content": chunk.get("content", ""),
                "nl_query": query,
                "source_document_id": chunk.get("metadata", {}).get("recordId"),
                "timestamp": datetime.utcnow().isoformat(),
                "org_id": org_id,
                "user_id": user_id,
                "query_id": conversation_id,
                "document_id": chunk.get("citationId"),
            }

            await self.producer.send("verify_chunks", value=message)
            self.logger.info(
                f"Published verification request {idx+1}/{total_chunks} "
                f"for conversation {conversation_id}"
            )
```

**Acceptance Criteria:**
- [ ] Publishes messages to verify_chunks topic
- [ ] Each chunk sent as separate message
- [ ] Message format matches orchestrator expectations
- [ ] Error handling for Kafka failures
- [ ] Unit tests with mocked Kafka
- [ ] Integration tests with real Kafka (optional)

---

### Task 3.2.6: Integrate Publisher into Chat Query Flow
**File:** `/backend/python/app/api/routes/chatbot.py`

**Test First:**
```python
@pytest.mark.asyncio
async def test_chat_stream_publishes_verification_when_enabled(
    mock_kafka_publisher,
    mock_retrieval_service
):
    query = ChatQuery(query="test", verification_enabled=True)
    # ... setup mocks

    async for event in stream_chat_response(query, ...):
        pass

    # Verify publisher called with chunks
    assert mock_kafka_publisher.publish_verification_requests.called
```

**Implementation:**
1. Add Kafka publisher to container:
   ```python
   # In container setup
   from app.verification.kafka_publisher import VerificationKafkaPublisher

   kafka_publisher = VerificationKafkaPublisher(
       kafka_brokers=os.getenv("KAFKA_BROKERS", "localhost:9092")
   )
   await kafka_publisher.start()
   ```

2. Inject into route:
   ```python
   async def get_kafka_publisher(request: Request) -> VerificationKafkaPublisher:
       container: QueryAppContainer = request.app.container
       return await container.kafka_publisher()
   ```

3. In process_chat_query_with_status, after retrieval:
   ```python
   # After reranking
   reranked_results = await reranker_service.rerank(...)

   # Publish for verification if enabled
   if query_info.verification_enabled:
       await kafka_publisher.publish_verification_requests(
           chunks=reranked_results,
           query=query_info.query,
           conversation_id=conversation_id,
           org_id=org_id,
           user_id=user_id,
       )
       logger.info(f"Published {len(reranked_results)} chunks for verification")
   ```

**Acceptance Criteria:**
- [ ] Verification requests published only when enabled
- [ ] Published after retrieval/reranking
- [ ] Does NOT block answer generation
- [ ] Errors logged but don't fail query
- [ ] Integration test with full flow

---

## Phase 3.3: Metadata Display & Progress Tracking

### Task 3.3.1: Create WebSocket Namespace for Verification
**File:** `/backend/nodejs/apps/src/modules/enterprise_search/sockets/verification.socket.ts` (NEW)

**Test First:**
```typescript
describe('Verification WebSocket', () => {
  it('should emit progress events to conversation room', (done) => {
    const socket = io('ws://localhost:3000/verification');
    socket.on('verification_progress', (data) => {
      expect(data.conversation_id).toBe('conv123');
      done();
    });
    // Trigger event from server
  });
});
```

**Implementation:**
```typescript
import { Server as SocketIOServer, Socket } from 'socket.io';
import { Logger } from '../../../libs/services/logger.service';

const logger = Logger.getInstance({ service: 'Verification Socket' });

export function setupVerificationSocket(io: SocketIOServer): void {
  const verificationNamespace = io.of('/verification');

  verificationNamespace.on('connection', (socket: Socket) => {
    logger.info(`Client connected to verification namespace: ${socket.id}`);

    socket.on('join_conversation', (conversationId: string) => {
      socket.join(`conversation:${conversationId}`);
      logger.debug(`Socket ${socket.id} joined room: conversation:${conversationId}`);
    });

    socket.on('leave_conversation', (conversationId: string) => {
      socket.leave(`conversation:${conversationId}`);
      logger.debug(`Socket ${socket.id} left room: conversation:${conversationId}`);
    });

    socket.on('disconnect', () => {
      logger.info(`Client disconnected: ${socket.id}`);
    });
  });
}

// Helper to emit verification progress
export function emitVerificationProgress(
  io: SocketIOServer,
  conversationId: string,
  progressData: {
    total: number;
    completed: number;
    failed: number;
    percentage: number;
    latest_result?: any;
  }
): void {
  io.of('/verification')
    .to(`conversation:${conversationId}`)
    .emit('verification_progress', {
      conversation_id: conversationId,
      ...progressData,
    });
}

export function emitVerificationComplete(
  io: SocketIOServer,
  conversationId: string,
  results: any[]
): void {
  io.of('/verification')
    .to(`conversation:${conversationId}`)
    .emit('verification_complete', {
      conversation_id: conversationId,
      results,
    });
}

export function emitVerificationError(
  io: SocketIOServer,
  conversationId: string,
  error: string
): void {
  io.of('/verification')
    .to(`conversation:${conversationId}`)
    .emit('verification_error', {
      conversation_id: conversationId,
      error,
    });
}
```

**Acceptance Criteria:**
- [ ] WebSocket namespace created
- [ ] Clients can join/leave conversation rooms
- [ ] Events emitted only to specific conversation
- [ ] Connection/disconnection logged
- [ ] Integration test with Socket.io client

---

### Task 3.3.2: Consume Verification Results from Kafka (NodeJS)
**File:** `/backend/nodejs/apps/src/modules/verification/kafka-consumer.ts` (NEW)

**Test First:**
```typescript
describe('Kafka Verification Consumer', () => {
  it('should consume messages from verification_complete topic', async () => {
    const consumer = new VerificationKafkaConsumer(kafka, io);
    await consumer.start();
    // Publish test message to Kafka
    // Verify WebSocket event emitted
  });
});
```

**Implementation:**
```typescript
import { Kafka, Consumer, EachMessagePayload } from 'kafkajs';
import { Server as SocketIOServer } from 'socket.io';
import { Logger } from '../../../libs/services/logger.service';
import {
  emitVerificationProgress,
  emitVerificationComplete,
  emitVerificationError,
} from '../sockets/verification.socket';

const logger = Logger.getInstance({ service: 'Verification Kafka Consumer' });

interface VerificationResultMessage {
  request_id: string;
  chunk_index: number;
  verdict: string;
  confidence: number;
  formalization_similarity: number;
  org_id: string;
  user_id: string;
  query_id: string; // conversation_id
  document_id: string;
  // ... other fields
}

export class VerificationKafkaConsumer {
  private consumer: Consumer;
  private io: SocketIOServer;
  private progressTracking: Map<string, any> = new Map();

  constructor(kafka: Kafka, io: SocketIOServer) {
    this.consumer = kafka.consumer({ groupId: 'verification-consumer-nodejs' });
    this.io = io;
  }

  async start(): Promise<void> {
    await this.consumer.connect();
    await this.consumer.subscribe({
      topics: ['verification_complete', 'verification_failed'],
      fromBeginning: false,
    });

    await this.consumer.run({
      eachMessage: async ({ topic, message }: EachMessagePayload) => {
        try {
          const value = message.value?.toString();
          if (!value) return;

          const data: VerificationResultMessage = JSON.parse(value);
          const conversationId = data.query_id;

          if (topic === 'verification_complete') {
            await this.handleVerificationComplete(conversationId, data);
          } else if (topic === 'verification_failed') {
            await this.handleVerificationFailed(conversationId, data);
          }
        } catch (error: any) {
          logger.error('Error processing Kafka message:', error);
        }
      },
    });

    logger.info('Verification Kafka consumer started');
  }

  async stop(): Promise<void> {
    await this.consumer.disconnect();
    logger.info('Verification Kafka consumer stopped');
  }

  private async handleVerificationComplete(
    conversationId: string,
    data: VerificationResultMessage
  ): Promise<void> {
    // Track progress
    if (!this.progressTracking.has(conversationId)) {
      this.progressTracking.set(conversationId, {
        total: 0,
        completed: 0,
        failed: 0,
        results: [],
      });
    }

    const progress = this.progressTracking.get(conversationId);
    progress.completed += 1;
    progress.results.push(data);
    const percentage = Math.round((progress.completed / progress.total) * 100);

    // Emit progress
    emitVerificationProgress(this.io, conversationId, {
      total: progress.total,
      completed: progress.completed,
      failed: progress.failed,
      percentage,
      latest_result: data,
    });

    logger.info(
      `Verification progress: ${progress.completed}/${progress.total} for conversation ${conversationId}`
    );

    // If all complete, emit final event
    if (progress.completed + progress.failed >= progress.total) {
      emitVerificationComplete(this.io, conversationId, progress.results);
      this.progressTracking.delete(conversationId);
    }
  }

  private async handleVerificationFailed(
    conversationId: string,
    data: VerificationResultMessage
  ): Promise<void> {
    const progress = this.progressTracking.get(conversationId);
    if (progress) {
      progress.failed += 1;
    }

    emitVerificationError(
      this.io,
      conversationId,
      `Verification failed for chunk ${data.chunk_index}`
    );
  }
}
```

**Acceptance Criteria:**
- [ ] Consumes from verification_complete and verification_failed topics
- [ ] Tracks progress per conversation
- [ ] Emits WebSocket events on progress
- [ ] Cleans up tracking when complete
- [ ] Error handling for malformed messages
- [ ] Unit tests with mocked Kafka

---

### Task 3.3.3: Frontend WebSocket Integration
**File:** `/frontend/src/hooks/use-verification-socket.ts` (NEW)

**Test First:**
```typescript
describe('useVerificationSocket', () => {
  it('should connect to verification namespace', () => {
    const { result } = renderHook(() => useVerificationSocket('conv123'));
    expect(result.current.connected).toBe(true);
  });

  it('should update progress on verification_progress event', () => {
    const { result } = renderHook(() => useVerificationSocket('conv123'));
    act(() => {
      mockSocket.emit('verification_progress', {
        conversation_id: 'conv123',
        completed: 5,
        total: 10,
      });
    });
    expect(result.current.progress.completed).toBe(5);
  });
});
```

**Implementation:**
```typescript
import { useEffect, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import type { VerificationProgress } from 'src/types/verification.types';

interface UseVerificationSocketReturn {
  connected: boolean;
  progress: VerificationProgress | null;
  error: string | null;
}

export function useVerificationSocket(
  conversationId: string | null
): UseVerificationSocketReturn {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [progress, setProgress] = useState<VerificationProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!conversationId) return undefined;

    // Connect to verification namespace
    const newSocket = io('/verification', {
      transports: ['websocket', 'polling'],
    });

    newSocket.on('connect', () => {
      setConnected(true);
      newSocket.emit('join_conversation', conversationId);
    });

    newSocket.on('disconnect', () => {
      setConnected(false);
    });

    newSocket.on('verification_progress', (data: any) => {
      if (data.conversation_id === conversationId) {
        setProgress({
          total: data.total,
          completed: data.completed,
          failed: data.failed,
          percentage: data.percentage,
          results: data.latest_result ? [data.latest_result] : [],
        });
      }
    });

    newSocket.on('verification_complete', (data: any) => {
      if (data.conversation_id === conversationId) {
        setProgress((prev) => ({
          ...prev!,
          completed: prev!.total,
          percentage: 100,
          results: data.results,
        }));
      }
    });

    newSocket.on('verification_error', (data: any) => {
      if (data.conversation_id === conversationId) {
        setError(data.error);
      }
    });

    setSocket(newSocket);

    return () => {
      newSocket.emit('leave_conversation', conversationId);
      newSocket.disconnect();
    };
  }, [conversationId]);

  return { connected, progress, error };
}
```

**Acceptance Criteria:**
- [ ] Connects to /verification namespace
- [ ] Joins conversation room
- [ ] Updates progress state on events
- [ ] Cleans up on unmount
- [ ] Handles reconnection
- [ ] TypeScript types correct

---

### Task 3.3.4: Integrate WebSocket into ChatInterface
**File:** `/frontend/src/sections/qna/chatbot/chat-bot.tsx`

**Implementation:**
1. Import hook:
   ```typescript
   import { useVerificationSocket } from 'src/hooks/use-verification-socket';
   ```

2. Use hook in ChatInterface:
   ```typescript
   const verificationSocket = useVerificationSocket(currentConversationId);
   ```

3. Update verification state with socket data:
   ```typescript
   useEffect(() => {
     if (verificationSocket.progress) {
       verification.startVerification(verificationSocket.progress.total);
       // Update with latest progress
       verificationSocket.progress.results.forEach((result) => {
         verification.updateProgress(result);
       });
     }
   }, [verificationSocket.progress]);
   ```

**Acceptance Criteria:**
- [ ] WebSocket connected when conversation loaded
- [ ] Progress updates in real-time
- [ ] No memory leaks on conversation switch
- [ ] Error handling for connection failures

---

## Phase 3.4: Citation Enrichment

### Task 3.4.1: Store Verification Results in MongoDB
**File:** `/backend/nodejs/apps/src/modules/verification/result-updater.ts` (NEW)

**Test First:**
```typescript
describe('VerificationResultUpdater', () => {
  it('should update citation with verification result', async () => {
    const updater = new VerificationResultUpdater();
    await updater.updateCitationVerification(
      'conv123',
      'citation1',
      verificationResult
    );

    const conversation = await Conversation.findById('conv123');
    const citation = conversation.messages[0].citations.find(
      c => c.citationId === 'citation1'
    );
    expect(citation.verification).toBeDefined();
  });
});
```

**Implementation:**
```typescript
import { Conversation } from '../schema/conversation.schema';
import { Logger } from '../../../libs/services/logger.service';

const logger = Logger.getInstance({ service: 'Verification Result Updater' });

interface VerificationResult {
  chunk_index: number;
  verdict: string;
  confidence: number;
  formalization_similarity: number;
  extraction_degradation: number;
  failure_mode?: string;
  formal_text?: string;
  // ... other fields
}

export class VerificationResultUpdater {
  async updateCitationVerification(
    conversationId: string,
    citationId: string,
    verificationResult: VerificationResult
  ): Promise<void> {
    try {
      // Find conversation and update citation
      const result = await Conversation.updateOne(
        {
          _id: conversationId,
          'messages.citations.citationId': citationId,
        },
        {
          $set: {
            'messages.$[].citations.$[citation].verification': {
              verdict: verificationResult.verdict,
              confidence: verificationResult.confidence,
              formalization_similarity: verificationResult.formalization_similarity,
              extraction_degradation: verificationResult.extraction_degradation,
              failure_mode: verificationResult.failure_mode,
              formal_text: verificationResult.formal_text,
            },
          },
        },
        {
          arrayFilters: [{ 'citation.citationId': citationId }],
        }
      );

      if (result.modifiedCount > 0) {
        logger.info(
          `Updated citation ${citationId} with verification result in conversation ${conversationId}`
        );
      } else {
        logger.warn(
          `Citation ${citationId} not found in conversation ${conversationId}`
        );
      }
    } catch (error: any) {
      logger.error('Failed to update citation with verification result:', error);
      throw error;
    }
  }

  async updateMultipleCitations(
    conversationId: string,
    verificationResults: Map<string, VerificationResult>
  ): Promise<void> {
    const promises = Array.from(verificationResults.entries()).map(
      ([citationId, result]) => this.updateCitationVerification(conversationId, citationId, result)
    );

    await Promise.allSettled(promises);
  }
}
```

**Acceptance Criteria:**
- [ ] Updates MongoDB citation documents
- [ ] Uses arrayFilters for nested updates
- [ ] Handles missing citations gracefully
- [ ] Logs success/failure
- [ ] Unit tests with mocked MongoDB

---

### Task 3.4.2: Call Updater from Kafka Consumer
**File:** `/backend/nodejs/apps/src/modules/verification/kafka-consumer.ts`

**Implementation:**
Update `handleVerificationComplete`:
```typescript
import { VerificationResultUpdater } from './result-updater';

private updater = new VerificationResultUpdater();

private async handleVerificationComplete(
  conversationId: string,
  data: VerificationResultMessage
): Promise<void> {
  // ... existing progress tracking

  // Update citation in database
  await this.updater.updateCitationVerification(
    conversationId,
    data.document_id,
    data
  );

  // ... emit WebSocket events
}
```

**Acceptance Criteria:**
- [ ] Citations updated in MongoDB when verification completes
- [ ] Errors logged but don't stop consumer
- [ ] Integration test verifying DB update

---

## Phase 4: Testing Strategy

### Unit Tests
- **Frontend:** Jest + React Testing Library
  - Component rendering
  - State management
  - Event handlers
  - Type checking

- **Backend NodeJS:** Jest + Supertest
  - Route handlers
  - Validation
  - Business logic
  - Error handling

- **Backend Python:** Pytest + pytest-asyncio
  - Pydantic models
  - Kafka publisher
  - Async functions
  - Error scenarios

### Integration Tests
- **E2E Frontend:** Playwright
  - User enables verification
  - Sends query
  - Sees progress bar
  - Views verification badges

- **API Integration:** Supertest/pytest
  - Full request/response cycle
  - Kafka message flow (mocked)
  - WebSocket events
  - Database persistence

### Manual Testing
- [ ] Enable verification checkbox
- [ ] Send query with verification enabled
- [ ] Verify Kafka messages published
- [ ] Check orchestrator logs
- [ ] Verify WebSocket events received
- [ ] Check citations display badges
- [ ] Click badge to see metadata
- [ ] Disable verification and verify no overhead

## Error Handling

### Graceful Degradation
- If verification fails, chat should still work
- If Kafka down, log error but don't block query
- If WebSocket fails, allow polling fallback
- If verification timeout, show UNKNOWN verdict

### Circuit Breaker
- Already implemented in HupyyClient
- Frontend should handle partial verification results
- Show progress even if some chunks fail

### Logging
- All verification events logged with conversation_id
- Errors logged with stack traces
- Performance metrics (verification duration)

## Deployment Checklist

### Environment Variables
- [ ] KAFKA_BROKERS configured
- [ ] HUPYY_API_URL configured
- [ ] REDIS_URL for verification cache
- [ ] Feature flag for verification enabled

### Dependencies
- [ ] kafkajs (NodeJS)
- [ ] aiokafka (Python)
- [ ] socket.io-client (Frontend)
- [ ] socket.io (Backend)

### Database Migrations
- [ ] Add verification field to citation schema (optional, no migration needed for optional field)

### Kafka Topics
- [ ] verify_chunks topic created
- [ ] verification_complete topic created
- [ ] verification_failed topic created
- [ ] verify_chunks_dlq topic created

## Timeline Estimate

| Phase | Tasks | Estimated Time | Priority |
|-------|-------|----------------|----------|
| 3.1: Chat UI Integration | 4 tasks | 4 hours | HIGH |
| 3.2: Backend Integration | 6 tasks | 6 hours | HIGH |
| 3.3: Real-time Updates | 4 tasks | 5 hours | MEDIUM |
| 3.4: Citation Enrichment | 2 tasks | 2 hours | MEDIUM |
| Testing & Debugging | - | 3 hours | HIGH |
| **Total** | **16 tasks** | **20 hours** | - |

## Next Steps

1. Review and approve plan
2. Set up Kafka topics
3. Begin Phase 3.1 (Chat UI Integration) with TDD
4. Implement in order: 3.1 -> 3.2 -> 3.3 -> 3.4
5. Run full E2E tests
6. Create SUMMARY.md documentation
