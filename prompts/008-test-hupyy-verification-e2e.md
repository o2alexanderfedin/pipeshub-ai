<objective>
Thoroughly test the Hupyy SMT verification integration end-to-end with comprehensive validation including visual verification using Playwright, backend logs analysis, and API response validation.

This testing validates the critical fix completed in prompt 025 where the API mismatch was resolved (/verify → /pipeline/process) and backend integration was completed. The goal is to confirm that:
1. The verification checkbox works in the UI
2. Verification requests flow from frontend → NodeJS → Python → Kafka → Hupyy
3. Verification results are correctly processed and displayed
4. No errors occur in the verification pipeline
</objective>

<context>
**What Was Just Fixed:**
- API endpoint changed from `/verify` to `/pipeline/process`
- Request model updated: `{nl_query, smt_query}` → `{informal_text, skip_formalization}`
- Response parser added: `check_sat_result` → `verdict` transformation
- Backend integration completed: NodeJS forwards `verification_enabled` to Python
- Environment configured with HUPYY_API_URL

**Test Environment:**
- Services running in Docker containers (already built with latest changes)
- Frontend: http://localhost:3000
- Backend APIs: NodeJS + Python + Kafka + Hupyy service
- Playwright already installed (package.json shows playwright@^1.56.1)

**Critical Success Criteria:**
- Verification checkbox visible and functional
- Chat queries work with and without verification enabled
- Logs show successful Hupyy API calls to `/pipeline/process`
- No 404 errors or API failures
- Verification results stored correctly

Read @CLAUDE.md for project conventions and testing requirements.
</context>

<requirements>

## Phase 1: Service Health Check

Before testing, verify all services are running:

1. **Check Docker containers status**
   ```bash
   cd deployment/docker-compose
   docker-compose ps
   ```
   All services should show "Up" status (pipeshub-ai, kafka, mongodb, arango, qdrant, redis)

2. **Check service logs for startup errors**
   ```bash
   docker logs docker-compose-pipeshub-ai-1 --tail 100
   ```
   Should see "Application started" with no critical errors

3. **Verify Hupyy service accessibility**
   ```bash
   curl -s https://verticalslice-smt-service-gvav8.ondigitalocean.app/health
   ```
   Should return: `{"status":"healthy",...}`

## Phase 2: Playwright Visual Testing

Create a comprehensive Playwright test suite that:

1. **Setup and Navigation**
   - Launch browser in headed mode (so we can see the test)
   - Navigate to http://localhost:3000
   - Login with credentials: `af@o2.services` / `Vilisaped1!`
   - Wait for chat interface to load
   - Take screenshot: `./test-results/01-chat-loaded.png`

2. **Verification Checkbox Test**
   - Locate the verification checkbox (HupyyControls component)
   - Verify checkbox is visible and not disabled
   - Take screenshot: `./test-results/02-checkbox-found.png`
   - Click checkbox to enable verification
   - Verify checkbox shows checked state
   - Take screenshot: `./test-results/03-checkbox-enabled.png`

3. **Chat Query Without Verification**
   - FIRST, ensure checkbox is UNCHECKED
   - Type test query: "What is the LLM optimization module?"
   - Submit the query
   - Wait for response to appear
   - Take screenshot: `./test-results/04-chat-response-no-verification.png`
   - Verify response contains relevant information

4. **Chat Query WITH Verification**
   - Enable verification checkbox (check it)
   - Type same test query: "What is the LLM optimization module?"
   - Submit the query
   - Wait for response to appear
   - Take screenshot: `./test-results/05-chat-response-with-verification.png`
   - Look for verification badges or indicators (if UI implemented)
   - Take screenshot of sources/citations section: `./test-results/06-verification-results.png`

5. **Error Detection**
   - Check browser console for JavaScript errors
   - Log any errors found
   - Verify no network failures in DevTools

Save Playwright test to: `./tests/e2e/hupyy-verification.spec.ts`

## Phase 3: Backend Logs Analysis

While Playwright tests run (especially the verification-enabled query), monitor backend logs:

1. **Capture verification flow logs**
   ```bash
   docker logs -f docker-compose-pipeshub-ai-1 | grep -i verification
   ```
   Expected logs:
   - "Published X chunks for verification (request_id=...)"
   - "Calling Hupyy API for request ..."
   - "Hupyy API response received"

2. **Check for API errors**
   ```bash
   docker logs docker-compose-pipeshub-ai-1 | grep -E "(404|500|error|Error|ERROR)" | tail -50
   ```
   Should NOT see:
   - "404" errors on `/verify` endpoint
   - "Failed to call Hupyy API"
   - Connection errors to Hupyy service

3. **Verify correct endpoint usage**
   ```bash
   docker logs docker-compose-pipeshub-ai-1 | grep -i "pipeline/process"
   ```
   Should see successful calls to `/pipeline/process`

4. **Check Kafka publishing**
   ```bash
   docker logs docker-compose-pipeshub-ai-1 | grep -i "kafka"
   ```
   Should see messages published to `verify_chunks` topic

Save log analysis to: `./test-results/backend-logs-analysis.md`

## Phase 4: API Response Validation

If possible, capture and validate actual Hupyy API responses:

1. **Check orchestrator logs for API responses**
   ```bash
   docker logs docker-compose-pipeshub-ai-1 | grep -A 10 "Hupyy API response"
   ```

2. **Verify response format**
   - Should contain `check_sat_result` (SAT/UNSAT/UNKNOWN)
   - Should contain `formalization_similarity`
   - Should contain `proof` object
   - Should NOT contain old fields like `verdict` directly

3. **Verify transformation**
   - Check logs show `check_sat_result` → `verdict` mapping occurred
   - Verify metadata contains `model`, `smt_lib_code`, `formal_text`

Save API validation to: `./test-results/api-response-validation.md`

## Phase 5: Integration Testing

Run the Python unit tests to verify models work correctly:

```bash
cd backend/python
pytest tests/verification/test_hupyy_api_integration.py -v
```

Expected: 18/18 tests passing

Save test output to: `./test-results/unit-test-results.txt`

</requirements>

<implementation>

## Playwright Test Structure

Use this structure for the Playwright test:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Hupyy SMT Verification E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate and login
    await page.goto('http://localhost:3000');
    // Add login steps
  });

  test('verification checkbox is visible and functional', async ({ page }) => {
    // Test checkbox visibility and click behavior
    await page.screenshot({ path: './test-results/02-checkbox-found.png' });
  });

  test('chat works without verification enabled', async ({ page }) => {
    // Ensure checkbox unchecked, send query, verify response
  });

  test('chat works with verification enabled', async ({ page }) => {
    // Check checkbox, send query, verify response
    await page.screenshot({ path: './test-results/05-chat-response-with-verification.png' });
  });

  test('no errors in console', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text());
    });

    // Perform actions

    expect(errors).toHaveLength(0);
  });
});
```

## Running Tests in Headed Mode

To see the browser during testing:
```bash
npx playwright test --headed --project=chromium
```

## Why These Specific Steps Matter

**Service health check first**: Prevents wasting time on tests if services aren't running
**Visual screenshots**: Provides evidence for manual review and debugging
**Logs analysis**: Catches issues that don't surface in UI but exist in backend
**Both with/without verification**: Ensures graceful degradation works
**Console error checking**: Catches JavaScript issues that might not be visible

</implementation>

<output>

Create the following files:

1. **Playwright Test Suite**
   - `./tests/e2e/hupyy-verification.spec.ts` - Comprehensive E2E test
   - `./playwright.config.ts` - Playwright configuration (if not exists)

2. **Test Results Directory**
   - `./test-results/` - Create directory for screenshots and reports
   - `./test-results/01-chat-loaded.png` - Initial state
   - `./test-results/02-checkbox-found.png` - Checkbox visible
   - `./test-results/03-checkbox-enabled.png` - Checkbox checked
   - `./test-results/04-chat-response-no-verification.png` - Response without verification
   - `./test-results/05-chat-response-with-verification.png` - Response with verification
   - `./test-results/06-verification-results.png` - Verification badges/results
   - `./test-results/backend-logs-analysis.md` - Log analysis report
   - `./test-results/api-response-validation.md` - API validation report
   - `./test-results/unit-test-results.txt` - Python test output

3. **Test Summary Report**
   - `./test-results/TEST-SUMMARY.md` - Comprehensive test report with:
     - Test execution date/time
     - All test results (pass/fail)
     - Screenshots embedded or referenced
     - Log excerpts showing verification flow
     - API response samples
     - Issues found (if any)
     - Overall verdict (PASS/FAIL)
     - Next steps or recommendations

</output>

<verification>

Before declaring testing complete, verify:

1. **All Playwright tests pass**
   - ✅ Checkbox test: PASS
   - ✅ Chat without verification: PASS
   - ✅ Chat with verification: PASS
   - ✅ No console errors: PASS

2. **Screenshots captured and reviewed**
   - ✅ All 6 screenshots exist
   - ✅ Screenshots show expected UI state
   - ✅ Checkbox clearly visible
   - ✅ Chat responses appear normal

3. **Backend logs confirm verification flow**
   - ✅ "Published X chunks for verification" appears
   - ✅ "Calling Hupyy API" with `/pipeline/process` appears
   - ✅ No 404 or 500 errors
   - ✅ Successful API responses logged

4. **API validation confirms correct format**
   - ✅ Responses contain `check_sat_result`
   - ✅ Responses contain `formalization_similarity`
   - ✅ Old fields (`nl_query`, `smt_query`) NOT in requests
   - ✅ Transformation logic executed correctly

5. **Unit tests pass**
   - ✅ 18/18 Python tests passing

6. **Test summary report created**
   - ✅ Contains all required sections
   - ✅ Includes evidence (screenshots, logs)
   - ✅ Has clear PASS/FAIL verdict
   - ✅ Lists any issues found

If ANY verification fails, document the failure in TEST-SUMMARY.md and mark overall verdict as FAIL.

</verification>

<success_criteria>

## Test Suite SUCCESS Criteria

- [ ] Playwright test suite created with all 4 test cases
- [ ] Tests run successfully in headed mode
- [ ] All 6 screenshots captured clearly showing UI state
- [ ] Backend logs show complete verification flow
- [ ] No API errors (404, 500) in logs
- [ ] Correct endpoint (`/pipeline/process`) used
- [ ] Python unit tests: 18/18 passing
- [ ] TEST-SUMMARY.md created with comprehensive results

## Verification Flow SUCCESS Criteria

- [ ] Checkbox visible and clickable in UI
- [ ] Checkbox state persists when toggled
- [ ] Chat works normally WITHOUT verification enabled
- [ ] Chat works normally WITH verification enabled
- [ ] Logs show "Published X chunks for verification"
- [ ] Logs show Hupyy API calls to `/pipeline/process`
- [ ] No errors in browser console
- [ ] No errors in backend logs

## Integration SUCCESS Criteria

- [ ] Request format correct: `{informal_text, skip_formalization, enrich}`
- [ ] Response format correct: `{check_sat_result, formalization_similarity, ...}`
- [ ] Transformation executes: `check_sat_result` → `verdict`
- [ ] Metadata stored: `model`, `smt_lib_code`, `formal_text`
- [ ] Graceful degradation: Chat still works if verification fails

## Overall PASS Criteria

ALL of the following must be true:
- ✅ All Playwright tests PASS
- ✅ No critical errors in logs
- ✅ Verification flow completes successfully
- ✅ Screenshots show expected behavior
- ✅ Unit tests all passing
- ✅ TEST-SUMMARY.md verdict is PASS

If even ONE criterion fails, overall verdict is FAIL and requires investigation.

</success_criteria>

<execution_strategy>

## Recommended Test Execution Order

1. **Pre-flight checks** (5 minutes)
   - Verify Docker containers running
   - Check Hupyy service health
   - Ensure ports accessible

2. **Unit tests first** (2 minutes)
   - Run Python tests to verify models work
   - If these fail, don't proceed to E2E

3. **Playwright tests in headed mode** (10 minutes)
   - Watch browser automation execute
   - Observe UI behavior visually
   - Screenshots captured automatically

4. **Logs analysis during tests** (5 minutes)
   - Monitor logs in separate terminal
   - Capture relevant log sections
   - Verify expected log messages appear

5. **Post-test validation** (5 minutes)
   - Review all screenshots
   - Analyze captured logs
   - Validate API responses

6. **Summary report creation** (10 minutes)
   - Compile all evidence
   - Write clear verdict
   - Document any issues

**Total estimated time: 35-40 minutes**

## Parallel Execution Strategy

For maximum efficiency, run these in parallel:
- Terminal 1: Playwright tests (headed mode)
- Terminal 2: Log monitoring (`docker logs -f ...`)
- Terminal 3: Ready for ad-hoc log queries

## If Tests Fail

1. **Capture failure evidence**
   - Screenshot at failure point
   - Full stack trace
   - Relevant log sections

2. **Document in TEST-SUMMARY.md**
   - What failed
   - Error messages
   - Suspected root cause
   - Steps to reproduce

3. **Don't proceed** to next test phase until failure investigated

</execution_strategy>

<troubleshooting>

## Common Issues and Solutions

**Issue**: Checkbox not visible
- **Check**: Frontend loaded correctly? Look for React errors in console
- **Solution**: Check `chat-bot.tsx` has HupyyControls component rendered

**Issue**: Chat works but no verification logs
- **Check**: Is `verification_enabled` being sent to backend?
- **Solution**: Check browser DevTools → Network tab → Request payload

**Issue**: 404 errors on Hupyy API
- **Check**: Still using old `/verify` endpoint?
- **Solution**: Verify `hupyy_client.py` line 232 uses `/pipeline/process`

**Issue**: Kafka messages not published
- **Check**: Is Kafka container running?
- **Solution**: `docker-compose ps` and restart if needed

**Issue**: Playwright can't find elements
- **Check**: Are selectors correct? UI might have changed
- **Solution**: Use Playwright Inspector: `npx playwright test --debug`

**Issue**: Unit tests fail
- **Check**: Models updated correctly?
- **Solution**: Review test failures, verify model fields match Hupyy API

</troubleshooting>

<notes>

## Why Visual Testing Matters

Playwright provides visual confirmation that:
- UI renders correctly
- User interactions work
- No visual regressions
- Screenshots serve as documentation

## Why Log Analysis Matters

Logs reveal backend behavior that UI might hide:
- Actual API calls made
- Error conditions
- Performance issues
- Integration points

## Why Both Together Matter

Visual + Logs = Complete picture:
- UI shows user experience
- Logs show system behavior
- Together they prove end-to-end functionality

## Test Evidence Hierarchy

1. **Automated test pass/fail** - Objective truth
2. **Screenshots** - Visual evidence
3. **Logs** - Backend behavior proof
4. **API responses** - Data flow validation

All four types of evidence needed for confident PASS verdict.

</notes>
