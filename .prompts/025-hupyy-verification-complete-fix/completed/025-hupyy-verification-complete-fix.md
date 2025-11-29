# Complete Hupyy SMT Verification Integration - Fix API Mismatch and Backend Flow

## Objective

Fix the critical API mismatch in the Hupyy integration and complete the remaining backend phases (3.2-3.4) to enable end-to-end SMT verification in the PipesHub chat UI. This is a surgical fix to make an existing, well-researched integration actually work.

**Why it matters**: Users see a verification checkbox but it doesn't work because the backend can't communicate with the Hupyy service due to wrong endpoint and data format.

## Context

### Referenced Files

**Research and Planning:**
- @prompts/004-connect-hupyy-to-chat-ui/RESEARCH-FINDINGS.md - Detailed analysis of chat flow and verification architecture
- @prompts/004-connect-hupyy-to-chat-ui/IMPLEMENTATION-PLAN.md - 16-task implementation plan with phases
- @prompts/004-connect-hupyy-to-chat-ui/SUMMARY.md - Current status: Phase 3.1 complete, 3.2-3.4 pending

**API Investigation:**
- !Current hupyy_client.py calls POST /verify with {nl_query, smt_query, enrich, timeout_seconds}
- !Actual Hupyy API is POST /pipeline/process with {informal_text, skip_formalization?, enrich?}
- !Actual Hupyy response: {check_sat_result, model, proof, formalization_similarity, smt_lib_code, formal_text}
- !Current HupyyResponse expects: {verdict, confidence, formalization_similarity, explanation, metadata, duration_ms}

**Infrastructure Already Exists:**
- ✅ Verification orchestrator (orchestrator.py) - Kafka consumer ready
- ✅ Circuit breaker and caching (hupyy_client.py)
- ✅ Frontend checkbox and UI (chat-bot.tsx)
- ✅ Hupyy service running at https://verticalslice-smt-service-gvav8.ondigitalocean.app
- ✅ Kafka topics and Redis for caching
- ✅ Verification UI components (VerificationBadge, VerificationMetadataDrawer)

**What's Broken:**
- ❌ API endpoint mismatch (/verify vs /pipeline/process)
- ❌ Request data format mismatch (nl_query/smt_query vs informal_text)
- ❌ Response parsing mismatch (verdict vs check_sat_result)
- ❌ NodeJS doesn't forward verification_enabled to Python backend
- ❌ Python backend doesn't publish to Kafka when verification requested

## Requirements

### Phase 1: Fix API Mismatch (CRITICAL - Do This First)

**1.1 Update HupyyRequest Model** (`backend/python/app/verification/models.py`)
- Change from `nl_query` and `smt_query` to `informal_text`
- Add optional `skip_formalization: bool = False`
- Keep `enrich: bool = False` (already correct)
- Remove `timeout_seconds` (not in Hupyy API)

**1.2 Update HupyyResponse Model** (`backend/python/app/verification/models.py`)
- Map `check_sat_result` → `verdict` (SAT/UNSAT/UNKNOWN)
- Extract confidence from formalization_similarity (0.0-1.0)
- Store `model`, `proof`, `smt_lib_code`, `formal_text` in metadata dict
- Keep existing fields for backward compatibility

**1.3 Fix API Call** (`backend/python/app/verification/hupyy_client.py:232`)
- Change endpoint from `f"{self.api_url}/verify"` to `f"{self.api_url}/pipeline/process"`
- Update request body to use HupyyRequest (which now has informal_text)
- Update response parsing to handle new ProcessResponse format

**1.4 Update Request Construction** (`backend/python/app/verification/hupyy_client.py:218`)
- Change from:
  ```python
  hupyy_request = HupyyRequest(
      nl_query=request.nl_query,
      smt_query=request.content,
      enrich=False,
      timeout_seconds=self.timeout_seconds,
  )
  ```
- To:
  ```python
  hupyy_request = HupyyRequest(
      informal_text=request.content,  # Use content as informal text
      skip_formalization=False,
      enrich=False,
  )
  ```

### Phase 2: Complete Backend Integration (Phases 3.2 from Plan)

**2.1 NodeJS Backend** (`backend/nodejs/`)
- Accept `verification_enabled` parameter in chat query endpoint
- Validate as boolean in request schema
- Forward to Python backend in query payload

**2.2 Python Backend** (`backend/python/app/api/routes/chatbot.py`)
- Accept `verification_enabled: bool = False` in ChatQuery model
- After retrieving chunks, if `verification_enabled=True`:
  - Import VerificationPublisher
  - Publish each chunk to `verify_chunks` Kafka topic
  - Include: request_id, content, chunk_index, total_chunks, nl_query

**Files to modify:**
- `backend/nodejs/src/validators/es_validators.ts` - Add verification_enabled to schema
- `backend/nodejs/src/api/controllers/chatbot/streamChat.ts` - Forward parameter
- `backend/python/app/api/routes/chatbot.py` - Accept parameter and publish to Kafka

### Phase 3: Environment Configuration

**3.1 Add Missing Environment Variable**
- Add to `deployment/docker-compose/.env`:
  ```
  HUPYY_API_URL=https://verticalslice-smt-service-gvav8.ondigitalocean.app
  ```

**3.2 Update docker-compose.dev.yml**
- Pass HUPYY_API_URL to pipeshub-ai service environment

### Phase 4: Testing and Validation

**4.1 Unit Tests**
- Test HupyyRequest/HupyyResponse model transformations
- Test API endpoint and data format
- Mock Hupyy service responses

**4.2 Integration Test**
- Enable verification checkbox in UI
- Send chat query
- Verify Kafka message published to verify_chunks
- Verify orchestrator processes and calls Hupyy
- Verify response stored and displayed

**4.3 End-to-End Manual Test**
1. Start Docker containers
2. Navigate to chat UI (http://localhost:3000)
3. Enable verification checkbox
4. Ask question: "What is the LLM optimization module?"
5. Verify:
   - Chunks published to Kafka (check logs)
   - Hupyy API called (check orchestrator logs)
   - Verification results appear in UI

## Output Specification

### Implementation Files

Save all changes to their respective locations (modify in place):
- `backend/python/app/verification/models.py` - Updated data models
- `backend/python/app/verification/hupyy_client.py` - Fixed endpoint and parsing
- `backend/python/app/api/routes/chatbot.py` - Kafka publishing logic
- `backend/nodejs/src/validators/es_validators.ts` - Schema validation
- `backend/nodejs/src/api/controllers/chatbot/streamChat.ts` - Parameter forwarding
- `deployment/docker-compose/.env` - Environment variable
- `deployment/docker-compose/docker-compose.dev.yml` - Service config

### Test Files

Create new test files:
- `backend/python/tests/verification/test_hupyy_api_integration.py`
- `backend/python/tests/verification/test_verification_e2e.py`

### Documentation

Create in `.prompts/025-hupyy-verification-complete-fix/`:
- **hupyy-verification-complete-fix.md** - Detailed implementation log with:
  - Each file modified and why
  - API transformation logic explanation
  - Test results with screenshots/logs
  - Verification of end-to-end flow

- **SUMMARY.md** - Executive summary with:
  - One-liner: What was fixed and outcome
  - Files Modified: List with brief description
  - API Changes: Before/after comparison
  - Test Results: Pass/fail with evidence
  - Decisions Needed: Any outstanding items
  - Blockers: Issues encountered
  - Next Step: What to do after this fix

## Success Criteria

**API Mismatch Fixed:**
- [ ] HupyyRequest uses `informal_text` field
- [ ] HupyyClient calls `/pipeline/process` endpoint
- [ ] HupyyResponse correctly maps `check_sat_result` to `verdict`
- [ ] All Hupyy response fields stored in metadata
- [ ] Unit tests pass for model transformations

**Backend Integration Complete:**
- [ ] NodeJS accepts and validates `verification_enabled` parameter
- [ ] Python backend publishes to Kafka when verification enabled
- [ ] Orchestrator processes messages and calls Hupyy API
- [ ] Verification results stored and returned to frontend

**Environment Configured:**
- [ ] HUPYY_API_URL set in .env
- [ ] Environment variable passed to Docker service
- [ ] Orchestrator uses correct Hupyy API URL

**Testing Validated:**
- [ ] Unit tests pass for API integration
- [ ] Integration tests verify Kafka flow
- [ ] Manual E2E test shows verification working in UI
- [ ] Logs confirm Hupyy API calls succeeding

**Documentation Complete:**
- [ ] Implementation log documents all changes
- [ ] SUMMARY.md has substantive one-liner (not generic)
- [ ] API transformation logic clearly explained
- [ ] Test evidence included (logs/screenshots)

## Execution Strategy

### Approach
- **Test-Driven**: Write/update tests FIRST for API changes
- **Incremental**: Fix API → Test API → Add Kafka → Test E2E
- **Verify at Each Step**: Don't move to next phase until current works

### Order of Operations
1. **Phase 1** (API Fix): Update models → Update client → Test with mock
2. **Phase 2** (Backend): NodeJS changes → Python changes → Test Kafka
3. **Phase 3** (Config): Add env vars → Update compose → Rebuild
4. **Phase 4** (Validation): Unit tests → Integration → E2E manual

### Parallelization
- Phase 1 tasks can be done in parallel (models + client + tests)
- Phase 2 requires Phase 1 complete (can't publish to Kafka with broken API)
- Phase 3 can be done in parallel with Phase 2
- Phase 4 requires all previous phases

### Rollback Plan
If integration fails:
- API changes are isolated to verification module
- Frontend checkbox already has graceful degradation (no-op if backend fails)
- Can disable by setting verification_enabled=False in UI
- No database schema changes, safe to rollback

## SOLID Principles Adherence

- **Single Responsibility**: Each model/class has one clear purpose
- **Open/Closed**: Extending existing classes, not modifying core logic
- **Liskov Substitution**: HupyyClient interface unchanged for consumers
- **Interface Segregation**: Minimal interface changes
- **Dependency Inversion**: Using abstractions (Kafka topics, not direct calls)

## Type Safety Requirements

- **No `any` types**: All TypeScript interfaces fully typed
- **Pydantic validation**: All Python models validated at runtime
- **Explicit return types**: All functions have type annotations
- **Runtime validation**: Kafka messages validated with schemas
- **Error handling**: All exceptions typed and caught

## Testing Strategy

**Unit Tests (TDD):**
1. Write test for HupyyRequest transformation (informal_text)
2. Write test for HupyyResponse parsing (check_sat_result → verdict)
3. Implement model changes
4. Run tests until green

**Integration Tests:**
1. Mock Hupyy API with correct response format
2. Test full orchestrator flow
3. Verify Kafka publish/consume
4. Verify data transformations

**E2E Manual Test:**
1. Real Hupyy service call
2. Real Kafka flow
3. Real UI interaction
4. Screenshot evidence

## Git Workflow

After successful completion:
1. Run all linters (ESLint, Prettier, mypy, pylint)
2. Run all tests
3. Git commit with message:
   ```
   fix: complete Hupyy SMT verification integration

   - Fix API mismatch (/verify → /pipeline/process)
   - Update data models (nl_query/smt_query → informal_text)
   - Map check_sat_result → verdict in response
   - Complete backend integration (NodeJS + Python)
   - Add HUPYY_API_URL environment variable
   - Add integration tests for verification flow

   Verification checkbox now works end-to-end with real Hupyy service.
   ```
4. Push to develop branch
5. Create release (0.1.13-alpha) for verified integration

## Edge Cases and Error Handling

**API Errors:**
- Hupyy service down → Circuit breaker opens, fallback to no verification
- Invalid response format → Log error, mark verification as UNKNOWN
- Timeout → Kafka retry with exponential backoff

**Data Issues:**
- Empty informal_text → Skip verification, log warning
- Malformed check_sat_result → Map to UNKNOWN verdict
- Missing formalization_similarity → Default confidence to 0.5

**Infrastructure:**
- Kafka down → Queue messages in Redis until available
- Redis down → Disable caching, direct API calls only
- Orchestrator crash → Kafka retains messages for replay

## Reference Materials

**Hupyy API Documentation:**
- OpenAPI spec: https://verticalslice-smt-service-gvav8.ondigitalocean.app/openapi.json
- Health check: https://verticalslice-smt-service-gvav8.ondigitalocean.app/health

**Existing Verification Code:**
- Orchestrator: `backend/python/app/verification/orchestrator.py`
- Circuit breaker: `backend/python/app/verification/circuit_breaker.py`
- Models: `backend/python/app/verification/models.py`
- Client: `backend/python/app/verification/hupyy_client.py`

**Frontend Components:**
- Checkbox: `frontend/src/sections/qna/chatbot/chat-bot.tsx`
- Badge: `frontend/src/sections/knowledgebase/components/verification/verification-badge.tsx`
- Metadata drawer: `frontend/src/sections/knowledgebase/components/verification/verification-metadata-drawer.tsx`

## Timeline Estimate

- **Phase 1 (API Fix)**: 2-3 hours
- **Phase 2 (Backend)**: 3-4 hours
- **Phase 3 (Config)**: 30 minutes
- **Phase 4 (Testing)**: 2-3 hours
- **Total**: 8-11 hours

## Known Risks

1. **Hupyy API changes**: If API differs from OpenAPI spec
   - Mitigation: Test with real service immediately

2. **Performance**: Hupyy calls take 20-30 seconds
   - Mitigation: Already async, won't block chat

3. **Kafka lag**: Messages might pile up
   - Mitigation: Orchestrator batches, rate limits

4. **UI timing**: Results might arrive after user left
   - Mitigation: WebSocket real-time updates (Phase 3.3, future work)

---

**Created**: 2025-11-28
**Purpose**: Fix API mismatch and complete backend integration for Hupyy SMT verification
**Dependencies**: Existing research and plan in prompts/004-connect-hupyy-to-chat-ui/
**Next Prompt**: None (this completes the integration)
