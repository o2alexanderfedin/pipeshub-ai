# TO-DOS

## COMPLETED - File Streaming Issue Fixed - 2025-11-21 05:20

- ~~**Add debug logging to stream_record**~~ - **RESOLVED**: The "File not found" errors were caused by old records with incorrect paths from a previous volume mount. **Fix applied:**
  1. Added debug logging to `connector.py:280-307`
  2. Identified old records had paths like `/data/local-files/pipeshub/pipeshub-ai/...` instead of `/data/local-files/...`
  3. Cleared old records from ArangoDB
  4. Cleared orphaned embeddings from Qdrant
  5. Reset Kafka consumer offset to skip old messages
  6. Triggered fresh sync with correct paths

  The Local Filesystem connector is now fully functional with proper file streaming.

## Kafka Consumer Rebalancing - Indexing Stuck at 83% - 2025-11-28 22:45

- **Investigate Kafka consumer rebalancing causing indexing to hang** - Indexing service stuck at 83% (1,480/1,787 records), 53 files remain "Not Started". **Problem:** Kafka consumer experiences `CommitFailedError` due to exceeding `max_poll_interval_ms` timeout. Consumer processes messages too slowly (embedding generation is CPU-intensive), gets kicked out of consumer group, rejoins, and loses progress. Creates a rebalancing loop preventing completion. Connector publishes to offset ~6,366 while indexing service only reached offset ~1,015 (5,300 message backlog). **Files:** `backend/python/app/services/messaging/kafka/consumer/consumer.py` (consumer configuration), `backend/python/app/indexing/record.py:102-326` (message processing), `backend/python/app/services/messaging/kafka/consumer/consumer.py:305` (commit error). **Solution:** Need to either (1) increase `max_poll_interval_ms` timeout in consumer config, (2) reduce message processing time by optimizing embedding generation, or (3) implement batch processing to reduce per-message overhead. Root cause needs investigation to understand why processing suddenly became too slow.

## Fix Test Infrastructure Issues - 2025-11-30 23:27

- ✅ **COMPLETED - Fix missing test dependencies in requirements-test.txt** - **Solution Applied:** Added redis==5.2.1 and prometheus-client==0.19.0 to requirements-test.txt at lines 47-57. All dependencies installed successfully. **Result:** 26/29 tests now passing (20 model tests + 5 client unit tests + 1 performance test). **Files Modified:** `backend/python/requirements-test.txt:47-57`.

- ✅ **COMPLETED - Replace fake API URLs with real Hupyy service URL** - **Problem:** Tests were hardcoded with fake URL "https://api.hupyy.example.com" instead of using production URL. User explicitly requested: "All must be running for real. Our system in production cannot be running on VCR." **Solution Applied:** (1) Added HUPYY_API_URL constant loading from environment with fallback to "https://verticalslice-smt-service-gvav8.ondigitalocean.app", (2) Replaced all 8 occurrences of fake URL throughout test file. **Result:** Tests now connect to real Hupyy API. VCR successfully recording real API interactions. **Files Modified:** `backend/python/tests/verification/test_hupyy_client.py:36-39,64-69,115,118,191,226,273,295,320,360`.

- ✅ **COMPLETED - Fix cache handling bug in production code** - **Problem:** TypeError at hupyy_client.py:113 trying to access VerificationResult as dictionary. Code assumed cache returns dict, but tests mock it as VerificationResult object. **Solution Applied:** Added isinstance() check to handle both VerificationResult objects and dict formats from cache. **Result:** All 5 unit tests passing (was 4/5 before). **Files Modified:** `backend/python/app/verification/hupyy_client.py:110-131`.

- ⚠️ **PARTIAL - Fix VCR test data format** - **Problem:** 2 VCR tests failing with 422 "All 1 extraction attempts failed with exceptions" from real API. Test SMT formulas not in correct format expected by Hupyy API. **Current Status:** 7/9 tests passing. VCR successfully recording real API interactions as cassettes. **Files:** test_successful_sat_verification, test_successful_unsat_verification in `test_hupyy_client.py:269-313`. **Next Step:** Update test data to use valid SMT-LIB 2.0 format or examine production usage patterns.

- ✅ **COMPLETED - Fix Local Filesystem connector blank icon** - **Problem:** Local Filesystem connector displayed blank/blinking icon in UI. User reported: "The icon on the connector is mostly blank, blinking on mouse-hover". **Root Cause:** Backend configured iconPath as "/assets/icons/connectors/filesystem.svg" at `backend/python/app/connectors/sources/local_filesystem/connector.py:97`, but this SVG file did not exist in frontend assets. **Solution Applied:** Created `frontend/public/assets/icons/connectors/filesystem.svg` with folder icon design matching existing connector icon style. **Files Modified:** `frontend/public/assets/icons/connectors/filesystem.svg` (created). **Result:** Icon now displays correctly for Local Filesystem connector.

- **Complete missing TypeScript/React test files** - Implementation agent created infrastructure but not all test files specified in plan. **Problem:** Planning phase (prompt 027) specified 135 tests but only ~40 representative tests were created (30% complete). Missing TypeScript validators tests, controller tests, React component tests. **Files:** `backend/nodejs/apps/tests/modules/` (missing validator/controller specs), `frontend/src/components/verification/HupyyControls.spec.tsx` (not created), `.prompts/027-hupyy-verification-testing-plan/UNIT-TEST-SPECS.md:1-1500` (specifications). **Solution:** Follow patterns from existing Python tests and specifications in UNIT-TEST-SPECS.md to create remaining test files.

- **Complete missing integration test files** - Only Kafka test template exists, missing Hupyy API, NodeJS-Python, and database tests. **Problem:** Integration tests incomplete - only test_kafka_flow.py template created. Missing test_hupyy_external_api.py (VCR pattern), test_nodejs_python_integration.py (service boundary), test_database_operations.py. **Files:** `tests/integration/test_kafka_flow.py` (exists), `tests/integration/test_hupyy_external_api.py` (missing), `tests/integration/test_nodejs_python_integration.py` (missing), `tests/integration/test_database_operations.py` (missing), `.prompts/027-hupyy-verification-testing-plan/INTEGRATION-TEST-SPECS.md:1-400` (specifications). **Solution:** Follow specifications in INTEGRATION-TEST-SPECS.md and use VCR pattern for Hupyy API tests, Testcontainers for Kafka/DB.

- **Validate CI/CD workflow actually runs** - GitHub Actions workflow created but not tested. **Problem:** .github/workflows/verification-tests.yml was created but never validated. May have syntax errors or configuration issues preventing successful execution. Workflow references tests that don't exist yet. **Files:** `.github/workflows/verification-tests.yml:1-250`, `.prompts/027-hupyy-verification-testing-plan/CI-CD-PLAN.md:1-350` (specifications). **Solution:** Test workflow locally with act or create PR to trigger workflow, fix any issues found, ensure it runs all test phases successfully.

