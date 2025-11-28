# Complete Hupyy Verification - Infrastructure + Citations + Testing

<objective>
Finish the **final 20%** of Hupyy SMT verification feature to achieve true production-ready status. The core infrastructure (80%) is complete and committed to git. This prompt completes:

1. **Fix infrastructure** - Debug and resolve Docker service crashes (MongoDB, Zookeeper, Kafka)
2. **Citations integration** - Add VerificationBadge to citation display
3. **E2E testing** - Verify full flow works end-to-end
4. **Integration tests** - Test complete pipeline
5. **Final commit** - Commit remaining work

**This is done-done-done work** - everything production-ready, tested, and verified working.
</objective>

<context>
## Current State (80% Complete)

**✅ What's Working:**
- Backend: Verification publisher integrated with Kafka (`backend/python/app/verification/publisher.py`)
- Backend: Chat API accepts `verification_enabled` parameter
- Frontend: VerificationBadge component created (SAT/UNSAT/UNKNOWN colors)
- Frontend: VerificationMetadataDrawer component created (proof/model display)
- Frontend: Checkbox wired to send `verification_enabled: true` to API
- Code quality: Linted, type-checked, unit tests created
- Git: Initial work committed (commit 5cc6ad30)

**❌ What's Blocking:**
- Infrastructure: MongoDB restarting continuously (exit code 133)
- Infrastructure: Zookeeper restarting (exit code 3), causing Kafka instability
- Infrastructure: ArangoDB running but unhealthy
- Missing: VerificationBadge not integrated into citations display
- Missing: E2E test not performed (blocked by infrastructure)
- Missing: Integration tests not written

## Technical Context
- Working directory: `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/deployment/docker-compose`
- Docker Compose file: `docker-compose.dev.yml`
- Frontend: React + TypeScript + Material-UI
- Backend: Python (FastAPI) + Node.js (Express)
- Infrastructure: MongoDB, ArangoDB, Redis, Kafka, Zookeeper, Qdrant

## Files to Modify
- `frontend/src/sections/qna/chatbot/components/sources-citations.tsx` (or wherever citations render)
</context>

<requirements>

## Phase 1: Fix Infrastructure (CRITICAL)

### 1.1 Diagnose Service Failures
Check logs and identify root causes:

```bash
# MongoDB logs
docker compose -f docker-compose.dev.yml logs mongodb --tail=50

# Zookeeper logs
docker compose -f docker-compose.dev.yml logs zookeeper --tail=50

# Check resource usage
docker stats --no-stream
```

**Common causes to investigate:**
- MongoDB exit 133 = SIGTERM/resource limits
- Zookeeper exit 3 = configuration or port conflicts
- Check Docker resource limits in `docker-compose.dev.yml`
- Check if ports 27017, 2181 are available

### 1.2 Apply Fixes

**Likely fixes:**
1. **Increase memory limits** in docker-compose.dev.yml for MongoDB/Zookeeper
2. **Check port conflicts** - verify nothing else using these ports
3. **Volume permissions** - ensure data directories are writable
4. **Restart order** - some services may need specific startup order

Example memory increase:
```yaml
mongodb:
  deploy:
    resources:
      limits:
        memory: 2G  # Increase if needed
```

### 1.3 Verify Services Healthy
```bash
docker compose -f docker-compose.dev.yml ps
# All services should show "Up" status (not "Restarting")

docker compose -f docker-compose.dev.yml logs --tail=20
# No error logs, services running stable
```

**Success Criteria:**
- ✅ MongoDB: Up and healthy
- ✅ Zookeeper: Up and stable
- ✅ Kafka: Up and connected to Zookeeper
- ✅ ArangoDB: Up and healthy
- ✅ PipesHub services: Up and connected to Kafka
- ✅ No services in "Restarting" state for 2+ minutes

## Phase 2: Citations Integration

### 2.1 Find Citations Component
Locate where citations are rendered. Check these locations:
```bash
find frontend/src -name "*citation*" -o -name "*source*" | grep -i tsx
```

Likely files:
- `frontend/src/sections/qna/chatbot/components/sources-citations.tsx`
- `frontend/src/sections/qna/chatbot/chat-messages.tsx`
- Search for where `sources` array is mapped and rendered

### 2.2 Integrate VerificationBadge
In the citations rendering code:

**Import the badge:**
```typescript
import { VerificationBadge } from './verification-badge';
import { VerificationMetadataDrawer } from './verification-metadata-drawer';
```

**Add state for drawer:**
```typescript
const [selectedVerification, setSelectedVerification] = useState<VerificationResult | null>(null);
const [drawerOpen, setDrawerOpen] = useState(false);
```

**Render badge on each citation:**
```typescript
{sources.map((source) => (
  <Box key={source.id}>
    {/* Existing citation content */}

    {/* Add verification badge if data exists */}
    {source.verification_metadata && (
      <VerificationBadge
        result={source.verification_metadata}
        onClick={() => {
          setSelectedVerification(source.verification_metadata);
          setDrawerOpen(true);
        }}
      />
    )}
  </Box>
))}

{/* Add drawer outside the map */}
<VerificationMetadataDrawer
  open={drawerOpen}
  onClose={() => setDrawerOpen(false)}
  result={selectedVerification}
/>
```

### 2.3 Update TypeScript Types
Ensure `Source` interface includes verification metadata:

```typescript
// In frontend/src/types/chat-bot.ts
interface Source {
  id: string;
  content: string;
  // ... other fields
  verification_metadata?: VerificationResult;
}
```

**Success Criteria:**
- ✅ VerificationBadge imported and used
- ✅ Badge displays next to citations that have verification data
- ✅ Clicking badge opens VerificationMetadataDrawer
- ✅ TypeScript types updated
- ✅ No TypeScript errors (`npm run type-check`)
- ✅ No ESLint errors (`npm run lint`)

## Phase 3: E2E Testing

### 3.1 Rebuild Frontend with Citations Integration
```bash
cd ../../
docker compose -f deployment/docker-compose/docker-compose.dev.yml build pipeshub-ai
docker compose -f deployment/docker-compose/docker-compose.dev.yml up -d
```

### 3.2 Perform Manual E2E Test
Use Playwright to test the complete flow:

1. Navigate to http://localhost:3000
2. Enable "SMT Verification" checkbox
3. Submit query: "What is the connector integration playbook?"
4. Wait for response (should be quick)
5. Verify checkbox state is enabled
6. Check Kafka logs for `verify_chunks` events:
   ```bash
   docker compose -f docker-compose.dev.yml logs pipeshub-ai | grep "verify_chunks"
   ```
7. Wait for verification to complete (1-2 min)
8. Verify badge appears on citations (check DOM for VerificationBadge)
9. Click badge and verify drawer opens
10. Verify metadata displays: specification, proof/model, solve time
11. Disable checkbox
12. Submit another query
13. Verify NO `verify_chunks` events published

**Evidence Required:**
- Screenshot showing checkbox enabled
- Log output showing `verify_chunks` Kafka messages
- Screenshot showing verification badge on citation
- Screenshot showing metadata drawer open

**Success Criteria:**
- ✅ Checkbox visible and functional
- ✅ Enabling triggers Kafka publishing (log evidence)
- ✅ Badge appears on citations
- ✅ Clicking badge opens drawer with metadata
- ✅ Disabling prevents verification
- ✅ No console errors

## Phase 4: Integration Tests

### 4.1 Write API Integration Test
Create `frontend/src/sections/qna/chatbot/__tests__/verification-integration.test.tsx`:

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { ChatBot } from '../chat-bot';
import { enableVerification } from '@/hooks/use-verification';

describe('Verification Integration', () => {
  it('sends verification_enabled when checkbox enabled', async () => {
    const mockFetch = jest.spyOn(global, 'fetch');

    render(<ChatBot />);

    // Enable verification
    const checkbox = screen.getByLabelText(/SMT Verification/i);
    fireEvent.click(checkbox);

    // Submit query
    const input = screen.getByPlaceholderText(/Ask anything/i);
    fireEvent.change(input, { target: { value: 'test query' } });
    fireEvent.submit(input);

    // Verify API call includes verification_enabled: true
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: expect.stringContaining('"verification_enabled":true')
        })
      );
    });
  });

  it('displays badge when verification metadata present', async () => {
    // Mock API response with verification data
    const mockResponse = {
      answer: 'test answer',
      sources: [{
        id: '1',
        content: 'test content',
        verification_metadata: {
          verdict: 'SAT',
          confidence: 0.95
        }
      }]
    };

    // Render and verify badge appears
    // ... test implementation
  });
});
```

### 4.2 Run Tests
```bash
cd frontend
npm test -- --testPathPattern=verification
```

**Success Criteria:**
- ✅ Integration tests pass
- ✅ Tests cover: checkbox → API call, badge display, drawer interaction
- ✅ No test failures

## Phase 5: Final Commit

### 5.1 Review All Changes
```bash
git status
git diff
```

### 5.2 Commit Remaining Work
```bash
cd /Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig

git add frontend/src/sections/qna/chatbot/components/sources-citations.tsx
git add frontend/src/sections/qna/chatbot/__tests__/verification-integration.test.tsx
git add deployment/docker-compose/docker-compose.dev.yml  # if modified

git commit -m "feat: complete Hupyy verification integration (final 20%)

- Integrate VerificationBadge into citations display
- Add integration tests for verification flow
- Fix Docker infrastructure issues (MongoDB, Zookeeper)
- Perform E2E verification test
- Verify complete flow: checkbox → Kafka → badges → metadata

All verification features now production-ready and tested.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push
```

**Success Criteria:**
- ✅ All changes committed
- ✅ Commit message clear and complete
- ✅ Code pushed to remote
- ✅ `git status` shows clean working tree

</requirements>

<output>

Save comprehensive summary to: `.prompts/002-hupyy-verification-complete-do/SUMMARY.md`

Must include:
- **One-liner**: Substantive description (not generic)
- **Version**: v1 (or iteration number)
- **Key Findings**: What infrastructure issues were fixed, citations integration details
- **Files Created**: Integration test file
- **Files Modified**: Citations component, docker-compose (if modified)
- **Decisions Needed**: None (everything should be done)
- **Blockers**: List any remaining blockers (should be none)
- **Next Step**: "Feature complete and production-ready" or next action if blocked

**Evidence appendix:**
- Screenshot: Checkbox enabled
- Screenshot: Verification badge on citation
- Screenshot: Metadata drawer open
- Logs: Kafka `verify_chunks` events
- Tests: Integration test pass output

</output>

<verification>

## Before Declaring Complete

Run comprehensive checklist:

### Infrastructure Verification
- [ ] MongoDB: Up and stable (no restarts)
- [ ] Zookeeper: Up and stable (no restarts)
- [ ] Kafka: Up and connected
- [ ] ArangoDB: Healthy
- [ ] All services: No "Restarting" status

### Citations Integration Verification
- [ ] VerificationBadge imported in citations component
- [ ] Badge renders on citations with verification data
- [ ] Clicking badge opens VerificationMetadataDrawer
- [ ] Drawer displays full metadata correctly
- [ ] TypeScript: `npm run type-check` passes (0 errors)
- [ ] ESLint: `npm run lint` passes (0 errors, 0 warnings)

### E2E Test Verification
- [ ] Checkbox visible and functional (screenshot evidence)
- [ ] Enabling checkbox triggers Kafka publishing (log evidence)
- [ ] Kafka logs show `verify_chunks` messages
- [ ] Badge appears on citations after verification
- [ ] Drawer opens with metadata
- [ ] Disabling checkbox prevents verification
- [ ] No console errors in browser

### Testing Verification
- [ ] Integration tests written
- [ ] All tests pass (`npm test`)
- [ ] Test coverage for: API call, badge display, drawer interaction

### Git Verification
- [ ] All changes committed
- [ ] Commit message follows convention
- [ ] Code pushed to remote
- [ ] `git status` shows clean working tree

**If ANY item is not checked, the task is NOT complete.**

</verification>

<success_criteria>

This task is **done-done-done** when ALL of the following are true:

✅ **Infrastructure Fixed**
- All Docker services up and stable (no restarts for 5+ minutes)
- MongoDB, Zookeeper, Kafka all healthy
- PipesHub services connected and running

✅ **Citations Integration Complete**
- VerificationBadge integrated into citation display
- Badges visible on citations with verification data
- Clicking badge opens drawer with metadata
- All linters passing (TypeScript + ESLint)

✅ **E2E Testing Complete**
- Full verification flow tested manually
- Evidence collected: screenshots + logs
- Kafka events confirmed in logs
- No console errors

✅ **Integration Tests Complete**
- Integration tests written and passing
- Tests cover critical flow points
- `npm test` exits with 0 errors

✅ **Git Complete**
- All changes committed with proper message
- Code pushed to remote
- Clean working tree

✅ **Production Ready**
- Feature functional end-to-end
- No known bugs or issues
- All code quality checks pass
- Complete user flow verified working

**The feature is production-ready when EVERY criterion is met.**

</success_criteria>

<execution_notes>

## Approach

Work **sequentially** through phases:
1. Infrastructure fixes (MUST work before anything else)
2. Citations integration (can't test without stable services)
3. E2E testing (validates everything works)
4. Integration tests (programmatic validation)
5. Final commit (preserves all work)

## If Infrastructure Won't Fix

If Docker issues persist after reasonable debugging (30+ min):

**Alternative approaches:**
1. Use system resources (kill other Docker containers, free memory)
2. Restart Docker Desktop completely
3. Try production deployment instead of dev environment
4. Document infrastructure issues as blocking, mark code as "ready when environment stable"

**The code is production-ready** - infrastructure issues are environmental, not code defects.

## Time Estimates

- Phase 1 (Infrastructure): 15-30 min (debugging + fixing)
- Phase 2 (Citations): 15-20 min (integration + linting)
- Phase 3 (E2E): 10-15 min (testing + evidence)
- Phase 4 (Tests): 20-30 min (write + run)
- Phase 5 (Git): 5 min (commit + push)

**Total: 1-2 hours to true production-ready status**

</execution_notes>
