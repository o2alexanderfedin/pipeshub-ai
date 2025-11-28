# Connect Hupyy Verification Service to Chat UI

## Problem Statement

The Hupyy SMT verification service is integrated into PipesHub with backend infrastructure and UI components built, but **the verification checkbox and metadata display are not connected to the actual chat interface**.

### Current State Analysis

**✅ What Exists:**
- Backend verification orchestrator: `backend/python/app/verification/orchestrator.py`
- Hupyy client with circuit breaker: `backend/python/app/verification/hupyy_client.py`
- Kafka topics for verification events
- UI verification controls component: `frontend/src/sections/knowledgebase/components/verification/hupyy-controls.tsx`
- Verification state hook: `frontend/src/hooks/use-verification.ts`
- Verification types defined

**❌ What's Missing:**
1. **Checkbox NOT in chat UI**: `chat-bot.tsx` doesn't import/render `HupyyControls`
2. **No verification triggering**: Chat queries don't trigger Hupyy verification even if enabled
3. **No metadata display**: No UI components showing SAT/UNSAT verdicts, proofs, models
4. **No backend integration**: Query service doesn't call verification orchestrator
5. **Missing API endpoints**: No REST/GraphQL endpoints to enable verification or fetch results

### Expected Behavior (from Implementation Plan)

Per `.prompts/003-hupyy-integration-implement/003-hupyy-integration-implement-UPDATED.md`:

**Phase 1 Requirements:**
- ✅ Backend: Hupyy client, circuit breaker, Kafka orchestrator (DONE)
- ❌ Frontend: Checkbox to enable/disable Hupyy (EXISTS but NOT INTEGRATED)
- ❌ Frontend: Progress indicators (MISSING)
- ❌ Frontend: Metadata display on click (MISSING)

**User Agreement:**
> "UI checkbox to enable/disable Hupyy"
> "Metadata display on click"
> "The responses must show those artifacts"

---

## Research Phase

### 1. Understand Current Chat Flow

**Tasks:**
- Read `frontend/src/sections/qna/chatbot/chat-bot.tsx` completely
- Identify where query is submitted
- Find where results are rendered
- Locate the proper injection point for HupyyControls checkbox
- Document the data flow: User Query → API → Response → UI

**Expected Output:**
```markdown
## Current Chat Flow
1. User types in [COMPONENT_NAME]
2. Query submitted via [API_CALL]
3. Results rendered in [COMPONENT_NAME]
4. Citations shown in [COMPONENT_NAME]
```

### 2. Trace Backend Query Endpoint

**Tasks:**
- Find the backend endpoint that handles chat queries
- Identify where semantic search/retrieval happens
- Check if there's a "verification enabled" parameter in the request
- See if verification results are included in response payload
- Find where Kafka `verify_chunks` events should be published

**Files to Check:**
- `backend/python/app/api/routes/chatbot.py` (or similar)
- `backend/python/app/query/` (query service)
- `backend/nodejs/apps/src/` (Node.js API layer)

**Expected Output:**
```markdown
## Backend Query Flow
1. Endpoint: POST /api/chat/query
2. Handler: [FILE:LINE]
3. Retrieval: [FILE:LINE]
4. Verification trigger point: [NEEDED HERE]
5. Response format: { answer, sources, verification_results? }
```

### 3. Identify Verification Metadata Storage

**Tasks:**
- Check Qdrant payload schema for verification metadata
- Check ArangoDB document schema for verification results
- Find where `verification_complete` Kafka events update these stores
- Verify if citation responses include verification data

**Expected Output:**
```markdown
## Verification Metadata Location
- Qdrant: chunk.payload.verification_metadata (exists: YES/NO)
- ArangoDB: document.verification_metrics (exists: YES/NO)
- API response includes verification: (YES/NO)
```

### 4. Find Existing Verification Components

**Tasks:**
- List all verification-related UI components already built
- Check if VerificationMetadata display component exists
- Check if VerificationProgress component exists
- Identify what's missing from the implementation plan

**Expected Files:**
- `HupyyControls.tsx` (found ✓)
- `VerificationProgress.tsx` (find)
- `VerificationMetadata.tsx` (find)
- `useVerification.ts` (found ✓)

---

## Plan Phase

### Objective
Create a step-by-step implementation plan to:
1. Add verification checkbox to chat UI
2. Wire checkbox state to backend API
3. Display verification progress during processing
4. Show verification metadata (SAT/UNSAT, proofs, models) in citations
5. Ensure all existing verification infrastructure is utilized

### Plan Structure

```xml
<plan>
  <phase id="1" name="Chat UI Integration">
    <task id="1.1">
      <description>Import and render HupyyControls in chat-bot.tsx</description>
      <file>frontend/src/sections/qna/chatbot/chat-bot.tsx</file>
      <changes>
        - Import HupyyControls and useVerification
        - Add verification state to chat component
        - Render checkbox in appropriate location (near query input or settings)
        - Wire onToggle to update verification state
      </changes>
      <acceptance>
        - Checkbox visible in chat UI
        - State persists to localStorage
        - Console log shows state change
      </acceptance>
    </task>

    <task id="1.2">
      <description>Pass verification flag to backend query</description>
      <file>frontend/src/sections/qna/chatbot/chat-bot.tsx</file>
      <changes>
        - Add verificationEnabled to query request payload
        - Include in API call to backend
      </changes>
      <acceptance>
        - Network tab shows verification: true/false in request
      </acceptance>
    </task>
  </phase>

  <phase id="2" name="Backend Query Integration">
    <task id="2.1">
      <description>Accept verification flag in query endpoint</description>
      <file>backend/python/app/api/routes/chatbot.py (or equivalent)</file>
      <changes>
        - Add verification_enabled: bool parameter
        - Pass to query service
      </changes>
    </task>

    <task id="2.2">
      <description>Trigger verification after retrieval</description>
      <file>backend/python/app/query/[service].py</file>
      <changes>
        - After retrieving top-k chunks, check verification_enabled
        - If true, publish verify_chunks event to Kafka
        - Include chunk IDs, content, query context
      </changes>
      <acceptance>
        - Kafka topic verify_chunks receives messages when enabled
        - Orchestrator logs show consumption
      </acceptance>
    </task>

    <task id="2.3">
      <description>Include verification results in response</description>
      <file>backend/python/app/api/routes/chatbot.py</file>
      <changes>
        - Wait for verification_complete events (with timeout)
        - OR return initial response + stream updates via WebSocket
        - Include verification metadata in sources/citations
      </changes>
      <acceptance>
        - API response includes verification_results field
        - Contains: verdict, confidence, proof/model, solve_time
      </acceptance>
    </task>
  </phase>

  <phase id="3" name="Metadata Display UI">
    <task id="3.1">
      <description>Create VerificationBadge component</description>
      <file>frontend/src/sections/qna/chatbot/components/verification-badge.tsx</file>
      <changes>
        - Display SAT/UNSAT/UNKNOWN badge with color coding
        - Show confidence score
        - Clickable to expand metadata
      </changes>
    </task>

    <task id="3.2">
      <description>Create VerificationMetadataDrawer component</description>
      <file>frontend/src/sections/qna/chatbot/components/verification-metadata-drawer.tsx</file>
      <changes>
        - Show formal specification (SMT-LIB2)
        - Display proof (for UNSAT) or model (for SAT)
        - Show solve time, solver used, theories
        - Display failure mode if UNKNOWN
      </changes>
    </task>

    <task id="3.3">
      <description>Integrate badges into citations</description>
      <file>frontend/src/sections/qna/chatbot/components/sources-citations.tsx</file>
      <changes>
        - Add VerificationBadge to each citation if verified
        - Wire onClick to open VerificationMetadataDrawer
        - Show "Verifying..." spinner for in-progress
      </changes>
    </task>
  </phase>

  <phase id="4" name="Progress Indicators">
    <task id="4.1">
      <description>Create VerificationProgress component</description>
      <file>frontend/src/sections/qna/chatbot/components/verification-progress.tsx</file>
      <changes>
        - Linear progress bar showing X/Y chunks verified
        - Toast notification on completion
        - Error notification on failures
      </changes>
    </task>

    <task id="4.2">
      <description>Add WebSocket or polling for progress updates</description>
      <file>frontend/src/hooks/use-verification.ts</file>
      <changes>
        - Connect to WebSocket endpoint for verification events
        - OR poll /api/verification/status/{query_id}
        - Update progress state in real-time
      </changes>
    </task>

    <task id="4.3">
      <description>Display progress in chat UI</description>
      <file>frontend/src/sections/qna/chatbot/chat-bot.tsx</file>
      <changes>
        - Show VerificationProgress when verification in progress
        - Update as events arrive
        - Hide on completion
      </changes>
    </task>
  </phase>

  <phase id="5" name="Testing & Verification">
    <task id="5.1">
      <description>E2E test verification flow</description>
      <acceptance>
        - Enable checkbox in UI
        - Submit query: "What is the connector integration playbook?"
        - Verify Kafka messages published to verify_chunks
        - Verify Hupyy client called (check logs)
        - Verify verification_complete events published
        - Verify UI shows badges with SAT/UNSAT
        - Click badge → metadata drawer opens with proof/model
      </acceptance>
    </task>

    <task id="5.2">
      <description>Test with verification disabled</description>
      <acceptance>
        - Uncheck verification checkbox
        - Submit query
        - Verify NO Kafka events published
        - Verify NO Hupyy calls made
        - Verify response faster (no verification overhead)
        - Citations show NO verification badges
      </acceptance>
    </task>

    <task id="5.3">
      <description>Test edge cases</description>
      <acceptance>
        - Hupyy timeout (1-2 min): Shows "Verifying..." → "Timeout"
        - Hupyy failure: Shows error badge
        - No chunks to verify: No verification attempted
        - Circuit breaker open: Falls back gracefully
      </acceptance>
    </task>
  </phase>
</plan>
```

---

## Implementation Phase

### Execution Strategy

**Use Parallel Subtasks:**
- Phase 1 & 2 can run in parallel (frontend + backend)
- Phase 3 tasks (3.1, 3.2) can run in parallel
- Phase 4 tasks sequential (4.1 → 4.2 → 4.3)
- Phase 5 after all phases complete

**TDD Requirements:**
- Write tests FIRST for each component
- Unit tests for UI components
- Integration tests for API endpoints
- E2E tests for full flow

**Type Safety:**
- Define `VerificationResult` interface
- Define `VerificationMetadata` interface
- Ensure strict typing throughout

**Rollback Plan:**
- Feature flag: `VERIFICATION_UI_ENABLED=false` to hide checkbox
- Backend flag: `VERIFICATION_ENABLED=false` to disable processing
- All changes behind flags for safe rollout

---

## Success Criteria

**Functional:**
- ✅ Checkbox visible in chat UI
- ✅ Checkbox state persists across sessions
- ✅ When enabled, Hupyy verification triggered on queries
- ✅ Progress indicator shows during verification (1-2 min)
- ✅ Citations display verification badges (SAT/UNSAT/UNKNOWN)
- ✅ Clicking badge shows detailed metadata (proof/model/spec)
- ✅ When disabled, no verification overhead

**Technical:**
- ✅ All tests passing (unit, integration, E2E)
- ✅ Type safety enforced (no `any`)
- ✅ Linters passing (ESLint, Prettier)
- ✅ Kafka events flowing correctly
- ✅ Orchestrator consuming and processing
- ✅ Metadata stored in Qdrant/ArangoDB
- ✅ API response includes verification results

**Performance:**
- ✅ Verification async (doesn't block chat response)
- ✅ Progress updates in real-time (<1s latency)
- ✅ Graceful degradation if Hupyy slow/failing

**User Experience:**
- ✅ Clear indication of verification status
- ✅ Easy to enable/disable
- ✅ Informative metadata display
- ✅ No confusion when verification pending

---

## Output Requirements

### SUMMARY.md

Track progress with:

```markdown
# Connect Hupyy to Chat UI - Implementation Summary

**One-liner:** [Current status in one sentence]

**Version:** v1.0 (update as phases complete)

## Current Status
- Phase 1: [NOT_STARTED | IN_PROGRESS | COMPLETED]
- Phase 2: [NOT_STARTED | IN_PROGRESS | COMPLETED]
- Phase 3: [NOT_STARTED | IN_PROGRESS | COMPLETED]
- Phase 4: [NOT_STARTED | IN_PROGRESS | COMPLETED]
- Phase 5: [NOT_STARTED | IN_PROGRESS | COMPLETED]

## Key Findings

### Chat UI Integration
- Checkbox injection point: [LOCATION]
- Query API call: [ENDPOINT]
- State management: [APPROACH]

### Backend Integration
- Verification trigger: [FILE:LINE]
- Kafka publishing: [WORKING | ISSUE]
- Response format: [STRUCTURE]

### Metadata Display
- Verification badges: [STATUS]
- Metadata drawer: [STATUS]
- Progress indicator: [STATUS]

## Files Created/Modified

### Frontend
- [ ] chat-bot.tsx (modified)
- [ ] verification-badge.tsx (created)
- [ ] verification-metadata-drawer.tsx (created)
- [ ] verification-progress.tsx (created)
- [ ] use-verification.ts (modified)
- [ ] sources-citations.tsx (modified)

### Backend
- [ ] chatbot.py (modified)
- [ ] [query_service].py (modified)
- [ ] verification_endpoints.py (created if needed)

## Issues Encountered
- [List any blockers or unexpected findings]

## Decisions Needed
- [ ] WebSocket vs polling for progress?
- [ ] Where to inject checkbox (header vs query input)?
- [ ] Real-time vs batch verification results?

## Next Steps
1. [Next immediate action]
2. [Following action]

## Testing Evidence
- [ ] Screenshot: Checkbox visible
- [ ] Screenshot: Verification badge on citation
- [ ] Screenshot: Metadata drawer open
- [ ] Logs: Kafka events published
- [ ] Logs: Hupyy client called
```

---

## Constraints & Guidelines

**From CLAUDE.md:**
- TDD: Write tests first
- Strong typing: No `any`
- SOLID principles
- Code review via subtask
- Linting before commit
- Git commit + push after each phase

**From Implementation Plan:**
- UI checkbox mandatory
- Metadata display on click
- Progress indicators required
- Async/parallel processing
- enrich=false always
- Top-5 to top-10 sampling

**Performance:**
- Verification 1-2 minutes (don't block UX)
- Circuit breaker on failures
- Graceful degradation

---

## Begin Execution

**Your Task:**

1. **Research Phase:** Investigate current chat flow and backend integration points
2. **Plan Phase:** Create detailed implementation plan with file-level changes
3. **Implementation Phase:** Execute with parallel subtasks, TDD, and type safety
4. **Testing Phase:** E2E verification of complete flow
5. **SUMMARY.md:** Comprehensive status report

**Start with Research Phase and report findings before proceeding to implementation.**
