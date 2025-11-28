# Demo Preparation - Deployment and Validation Plan

## Objective

Create a concrete, executable plan for preparing PipesHub for a successful 10AM PST demo. The plan must address all critical blockers identified in research, define exact deployment steps, establish validation checkpoints, and ensure end-to-end functionality from database clean through UI account creation, connector sync, indexing, and Assistant Q&A with verification metadata.

**Why this matters**: Demo is in ~7 hours (after research phase). Need a clear, actionable roadmap that takes us from current broken state to fully working demo where every step is verified. No time for trial-and-error - plan must be right the first time.

## Context

### Research Input

**@.prompts/011-demo-prep-research/demo-prep-research.md**
- Use root cause findings from research phase
- Reference specific code locations and blockers
- Build on system state assessment
- Address the exact failure mechanisms identified
- Prioritize based on demo criticality

### Demo Requirements (Reminder)

**Critical Path Success Criteria**:
1. ✅ Clean databases → verified empty
2. ✅ Deploy fresh Docker → all services healthy
3. ✅ UI accessible → localhost:3000 responds
4. ✅ Create account → af@o2.services / Vilisaped1!
5. ✅ Configure connector → Local Filesystem active
6. ✅ Sync files → records in database with content
7. ✅ Indexing completes → 0% → 100% progress
8. ✅ Search works → queries return results
9. ✅ Assistant answers → questions about files
10. ✅ Verification metadata → responses include provenance

**Timeline**: ~7 hours remaining after research

## Requirements

### Plan Scope

Create a **complete, actionable plan** covering:

#### 1. Blocker Resolution Strategy

Based on research findings:
- **For each critical blocker**: Exact fix procedure
- **Code changes**: File paths, line numbers, before/after
- **Configuration updates**: What settings to change
- **Database migrations**: Schema updates if needed
- **Service restarts**: What needs redeployment

**Must include**:
- Exact commands to execute
- Expected outputs at each step
- Validation queries to confirm fix worked
- Time estimates for each fix

#### 2. Database Clean Procedure

**Safe Clean Strategy**:
- PostgreSQL: Which tables to truncate/drop
- ArangoDB: Which collections to clear
- Qdrant: Which collections to delete
- Verification: How to confirm clean worked

**Considerations**:
- Preserve schema vs full wipe
- Migration replay needed?
- Connection string validation
- Backup before clean (or skip for speed)?

#### 3. Docker Deployment Process

**Build and Deploy**:
- Check build status (bash_id 43696f)
- Handle build errors if any
- Deployment command (docker compose up)
- Wait strategy for service health
- Log monitoring for startup errors

**Service Verification**:
- Health check endpoints
- Port accessibility tests
- Inter-service communication
- Database connections

#### 4. UI Account Creation Flow

**Manual Steps** (document for execution):
1. Navigate to localhost:3000
2. Registration form fields
3. Expected success response
4. Login verification
5. Dashboard accessibility

**Automation Considerations**:
- Can this be scripted with Playwright?
- Or manual execution required?
- Verification: Query PostgreSQL for user

#### 5. Connector Configuration

**Setup Steps**:
1. Navigate to Connector Settings
2. Local Filesystem connector
3. Configuration fields:
   - Root path: `/data/pipeshub/test-files`
   - Content extraction: enabled
   - Max size: 10MB
4. Save configuration
5. Trigger initial sync

**Verification**:
- Connector status: Active
- Records created in ArangoDB
- blockContainers field populated
- Kafka events produced

#### 6. Indexing Validation

**Critical**: Fix the "record not found" error first

**Monitoring**:
- Watch indexing progress in UI
- Check logs for errors
- Verify Qdrant vector count
- Confirm indexing reaches 100%

**Validation Queries**:
- ArangoDB: Records with blockContainers
- Qdrant: Vector count matches record count
- Indexing service: No error logs

#### 7. Assistant Q&A Testing

**Test Queries**:
- "What does calculator.ts do?"
- "Explain the analyzer.py file"
- "What's in config.json?"

**Success Criteria**:
- Responses reference file content
- Answers are accurate
- Verification metadata present:
  - Source file names
  - Confidence scores
  - Retrieval method

### Plan Structure

Organize as **sequential phases** with clear dependencies:

**Phase 0: Pre-Deployment Preparation**
- Check build status (bash_id 43696f)
- Review research findings
- Prepare verification commands
- Document current state
- Stop running containers

**Phase 1: Database Clean**
- Stop all services
- Clean PostgreSQL
- Clean ArangoDB
- Clean Qdrant
- Verify clean successful
- Restart databases

**Phase 2: Docker Deployment**
- Deploy fresh containers
- Wait for service health
- Verify all services up
- Check logs for errors
- Validate database connections

**Phase 3: Blocker Fixes** (If research identified code issues)
- Apply code changes
- Rebuild affected services
- Restart containers
- Verify fixes with tests

**Phase 4: UI Account Setup**
- Access localhost:3000
- Create account (af@o2.services)
- Verify login works
- Check dashboard accessible

**Phase 5: Connector Configuration**
- Navigate to settings
- Configure Local Filesystem
- Set root path
- Enable content extraction
- Save and verify status

**Phase 6: Initial Sync**
- Trigger connector sync
- Monitor logs
- Verify records created
- Check blockContainers present
- Confirm Kafka events

**Phase 7: Indexing Validation**
- Monitor indexing progress
- Watch for errors
- Verify vector creation
- Confirm 100% completion

**Phase 8: Assistant Q&A Testing**
- Test query 1
- Test query 2
- Test query 3
- Verify metadata
- Check accuracy

**Phase 9: Demo Rehearsal**
- Full end-to-end flow
- Time the demo
- Identify rough edges
- Prepare talking points

### Decision Framework

For each decision point, provide:

**Decision Template**:
```xml
<decision id="decision-id">
<question>[What needs to be decided?]</question>
<context>[Why this decision matters]</context>
<options>
  <option id="A">
    <description>[Approach A]</description>
    <pros>[Benefits]</pros>
    <cons>[Drawbacks]</cons>
    <time>[Time estimate]</time>
    <risk>[Risk level: Low/Medium/High]</risk>
  </option>
  <option id="B">
    [Same structure]
  </option>
</options>
<recommendation>[Preferred option]</recommendation>
<rationale>[Why recommended]</rationale>
<time_impact>[How this affects timeline]</time_impact>
</decision>
```

**Common Decisions**:
- Full database wipe vs selective clean
- Fix code issues vs work around them
- Manual UI steps vs Playwright automation
- Rebuild all containers vs only affected ones
- Backfill existing records vs fresh data only

## Output Specification

Save your plan to: `.prompts/012-demo-prep-plan/demo-prep-plan.md`

### Required Structure

```markdown
# Demo Preparation - Deployment and Validation Plan

## Executive Summary

[One paragraph: Approach, estimated time, key decisions, confidence level]

**Total Phases**: [Number]

**Estimated Total Time**: [X hours]

**Critical Path**: [Phases that determine minimum time]

**Confidence**: [High/Medium/Low] in success

**Key Decisions Required**: [List or "None - all decided"]

## Timeline Analysis

**Time Remaining**: ~7 hours until 10AM PST demo
**Plan Execution**: [X hours estimated]
**Buffer**: [Y hours remaining]
**Risk Level**: [Low/Medium/High]

**Breakdown**:
- Phase 0-2 (Infrastructure): [X min]
- Phase 3 (Fixes): [Y min]
- Phase 4-6 (Setup): [Z min]
- Phase 7 (Indexing): [A min - may run in background]
- Phase 8 (Testing): [B min]
- Phase 9 (Rehearsal): [C min]
- **Total**: [Sum] minutes / [X.X] hours

## Prerequisites

<phase id="phase-0" name="Pre-Deployment Preparation">
<objective>Verify environment ready and prepare for clean deployment</objective>

<tasks>
1. **Check build status**: Verify docker build completed successfully
   ```bash
   # Check background build (bash_id 43696f)
   # Expected: "Successfully built" or handle errors
   ```

2. **Review research findings**: Confirm critical blockers identified
   - [ ] Read: .prompts/011-demo-prep-research/SUMMARY.md
   - [ ] Note: Critical blocker(s) to fix
   - [ ] Understand: Fix procedures needed

3. **Stop running containers**: Clean slate for deployment
   ```bash
   cd deployment/docker-compose
   docker compose -f docker-compose.dev.yml down
   # Expected: All containers stopped
   ```

4. **Document current state**: For rollback if needed
   ```bash
   # Container status
   docker ps -a > /tmp/pre-deploy-containers.txt

   # Database record counts
   # (Skip if full clean planned)
   ```
</tasks>

<success_criteria>
- Build status known (success/failure)
- All containers stopped
- Research findings reviewed
- Ready to proceed with clean
</success_criteria>

<estimated_time>10 minutes</estimated_time>

<dependencies>
- Background build (bash_id 43696f) completed
- Research phase complete
</dependencies>
</phase>

## Phase 1: Database Clean

<phase id="phase-1" name="Database Clean">
<objective>Wipe all databases for fresh start</objective>

<clean_procedures>

### PostgreSQL Clean

**Approach**: [Drop and recreate OR Truncate tables OR Full DB drop]

**Commands**:
```bash
# Connect to PostgreSQL
docker exec -it [postgres-container] psql -U oilfield -d oilfield

# Option A: Drop schema and recreate (cleanest)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO oilfield;

# Option B: Truncate all tables (preserve schema)
TRUNCATE users, connectors, data_sources, records CASCADE;

# Exit
\q
```

**Verification**:
```sql
-- Check tables empty
SELECT COUNT(*) FROM users;  -- Should be 0
SELECT COUNT(*) FROM connectors;  -- Should be 0
```

### ArangoDB Clean

**Collections to Clear**:
- records
- users
- connectors
- [any others found in research]

**Commands**:
```bash
# Via HTTP API (from host)
curl -X DELETE http://localhost:8529/_db/pipeshub-ai/_api/collection/records \
  -H "Authorization: Basic [base64(root:password)]"

# Or via arangosh in container
docker exec -it [arango-container] arangosh
db._drop("records");
db._drop("users");
# ... drop other collections
```

**Verification**:
```bash
curl http://localhost:8529/_db/pipeshub-ai/_api/collection/records/count
# Should return: {"count":0}
```

### Qdrant Clean

**Collections to Delete**:
- [collection name from research]

**Commands**:
```bash
# Via HTTP API
curl -X DELETE http://localhost:6333/collections/[collection-name]
```

**Verification**:
```bash
curl http://localhost:6333/collections
# Should return: empty collections list or 404
```

</clean_procedures>

<success_criteria>
- PostgreSQL: 0 rows in all tables
- ArangoDB: 0 documents in all collections
- Qdrant: 0 vectors or collection deleted
- All verification queries pass
</success_criteria>

<estimated_time>15 minutes</estimated_time>

<commands_summary>
```bash
# PostgreSQL
docker exec -it [container] psql -U oilfield -d oilfield -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# ArangoDB
curl -X DELETE http://localhost:8529/_db/pipeshub-ai/_api/collection/records

# Qdrant
curl -X DELETE http://localhost:6333/collections/[name]

# Verify all clean
docker exec -it [postgres] psql -U oilfield -d oilfield -c "SELECT COUNT(*) FROM users;"
curl http://localhost:8529/_db/pipeshub-ai/_api/collection/records/count
curl http://localhost:6333/collections
```
</estimated_time>

</phase>

## Phase 2: Docker Deployment

<phase id="phase-2" name="Fresh Docker Deployment">
<objective>Deploy clean PipesHub environment with all services healthy</objective>

<deployment_steps>

### Step 1: Start Services

**Command**:
```bash
cd deployment/docker-compose
docker compose -f docker-compose.dev.yml up -d
```

**Expected Output**:
```
Creating network "docker-compose_default"
Creating docker-compose-postgres-1 ... done
Creating docker-compose-arango-1 ... done
Creating docker-compose-qdrant-1 ... done
Creating docker-compose-kafka-1 ... done
Creating docker-compose-pipeshub-ai-1 ... done
Creating docker-compose-frontend-1 ... done
```

### Step 2: Wait for Service Health

**Strategy**: Poll health endpoints until ready

**Commands**:
```bash
# Wait for main service (up to 2 minutes)
for i in {1..24}; do
  curl -s http://localhost:8091/health && break
  echo "Waiting for pipeshub-ai..."
  sleep 5
done

# Wait for frontend
for i in {1..24}; do
  curl -s http://localhost:3000 && break
  echo "Waiting for frontend..."
  sleep 5
done
```

**Expected Results**:
- pipeshub-ai: `{"status":"healthy"}`
- frontend: HTTP 200 response

### Step 3: Check All Containers Running

**Command**:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

**Expected**:
```
NAMES                          STATUS
docker-compose-frontend-1      Up 2 minutes (healthy)
docker-compose-pipeshub-ai-1   Up 2 minutes (healthy)
docker-compose-kafka-1         Up 2 minutes
docker-compose-qdrant-1        Up 2 minutes
docker-compose-arango-1        Up 2 minutes
docker-compose-postgres-1      Up 2 minutes (healthy)
```

**All should be "Up" with no "(restarting)" or "(unhealthy)"**

### Step 4: Verify Database Connections

**PostgreSQL**:
```bash
docker exec docker-compose-pipeshub-ai-1 python -c "
from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('PostgreSQL connected:', result.fetchone())
"
```

**ArangoDB**:
```bash
curl -s http://localhost:8529/_api/version
# Should return: {"server":"arango",...}
```

**Qdrant**:
```bash
curl -s http://localhost:6333/collections
# Should return: {"collections":[]}
```

### Step 5: Check Logs for Errors

**Command**:
```bash
# Check main service logs (last 50 lines)
docker logs --tail 50 docker-compose-pipeshub-ai-1

# Look for errors
docker logs docker-compose-pipeshub-ai-1 2>&1 | grep -i error | tail -20
```

**Expected**: No critical errors (warnings OK)

</deployment_steps>

<success_criteria>
- All containers status: "Up"
- Health checks passing (healthy)
- No critical errors in logs
- Database connections verified
- Frontend accessible at localhost:3000
- API accessible at localhost:8091
</success_criteria>

<estimated_time>10-15 minutes (including wait time)</estimated_time>

<failure_handling>
If deployment fails:
1. Check logs: `docker logs [container-name]`
2. Common issues:
   - Port conflicts: Check with `lsof -i :[port]`
   - Database connection: Verify credentials in .env
   - Build errors: Re-run build with `--no-cache`
3. Try restart: `docker compose restart [service-name]`
4. If persistent: Review research findings for known issues
</failure_handling>

</phase>

## Phase 3: Blocker Fixes

<phase id="phase-3" name="Apply Critical Fixes">
<objective>Fix critical blockers identified in research</objective>

**NOTE**: This phase depends on research findings. If no code fixes needed, skip to Phase 4.

<fix_procedures>

### Fix Template (Repeat for each blocker)

**Blocker**: [From research - e.g., "Indexing service can't find records"]

**Root Cause**: [Brief explanation]

**Fix Location**:
```
File: [path/to/file.py]
Lines: [X-Y]
```

**Current Code**:
```python
[Code that's broken]
```

**Fixed Code**:
```python
[Corrected code]
```

**Rationale**: [Why this fix works]

**Deployment**:
```bash
# If Python backend changed
cd deployment/docker-compose
docker compose -f docker-compose.dev.yml restart pipeshub-ai

# If Node.js frontend changed
docker compose -f docker-compose.dev.yml restart frontend
```

**Verification**:
```bash
# Test that fix worked
[Specific command or query to verify]

# Expected result:
[What should happen now]
```

**Time Estimate**: [X minutes]

---

**IMPORTANT**: Copy exact fix procedures from research phase, including:
- File paths with line numbers
- Before/after code snippets
- Verification commands
- Expected outputs

</fix_procedures>

<success_criteria>
- All code changes applied
- Services restarted/rebuilt
- Verification tests pass
- No new errors in logs
- Critical blocker resolved
</success_criteria>

<estimated_time>[Based on number and complexity of fixes from research]</estimated_time>

</phase>

## Phase 4: UI Account Setup

<phase id="phase-4" name="Create Demo Account">
<objective>Create user account for demo (af@o2.services / Vilisaped1!)</objective>

<manual_steps>

### Step 1: Access UI

1. Open browser: http://localhost:3000
2. Expected: Login/Register page

**If not accessible**:
```bash
# Check frontend container
docker logs docker-compose-frontend-1

# Check if port 3000 is bound
curl -I http://localhost:3000
```

### Step 2: Navigate to Registration

1. Click "Sign Up" or "Create Account"
2. Expected: Registration form

### Step 3: Fill Registration Form

**Fields**:
- Email: `af@o2.services`
- Password: `Vilisaped1!`
- Confirm Password: `Vilisaped1!`
- [Any other required fields]

**Click**: "Register" or "Create Account"

### Step 4: Verify Account Created

**Expected**:
- Success message or redirect to dashboard
- OR verification email message (skip email verification for local)

**Verify in Database**:
```bash
docker exec docker-compose-postgres-1 psql -U oilfield -d oilfield -c \
  "SELECT id, email, created_at FROM users WHERE email = 'af@o2.services';"
```

**Expected Result**:
```
 id | email            | created_at
----+------------------+-------------------------
  1 | af@o2.services   | 2025-11-28 08:00:00
```

### Step 5: Login

1. Navigate to login page (if not auto-logged-in)
2. Enter: af@o2.services / Vilisaped1!
3. Click "Login"
4. Expected: Dashboard page

</manual_steps>

<automation_option>

**Playwright Script** (if time permits):
```typescript
// Save to: scripts/create-demo-account.ts
import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage();

await page.goto('http://localhost:3000');
await page.click('text=Sign Up');
await page.fill('input[name="email"]', 'af@o2.services');
await page.fill('input[name="password"]', 'Vilisaped1!');
await page.fill('input[name="confirmPassword"]', 'Vilisaped1!');
await page.click('button:has-text("Register")');

await page.waitForURL('**/dashboard');
console.log('✓ Account created and logged in');

await browser.close();
```

**Run**:
```bash
npx tsx scripts/create-demo-account.ts
```

**Recommendation**: Manual execution for reliability (automation can fail on UI quirks)

</automation_option>

<success_criteria>
- Account created in database
- Login successful
- Dashboard accessible
- User ID available for next steps
</success_criteria>

<estimated_time>5 minutes (manual) or 2 minutes (automated)</estimated_time>

</phase>

## Phase 5: Connector Configuration

<phase id="phase-5" name="Configure Local Filesystem Connector">
<objective>Setup and activate Local Filesystem connector with content extraction enabled</objective>

<configuration_steps>

### Step 1: Navigate to Connector Settings

**Manual**:
1. From dashboard, click "Settings" or "Connectors"
2. Find "Local Filesystem" connector
3. Click "Configure" or "Add"

**URL**: http://localhost:3000/settings/connectors or similar

### Step 2: Fill Configuration

**Fields**:
- **Name**: `Local Filesystem Connector` (or auto-filled)
- **Root Path**: `/data/pipeshub/test-files`
- **Content Extraction**: `Enabled` (checkbox or toggle)
- **Max File Size**: `10` MB
- **File Patterns**: `*` (all files) or leave default
- **Exclude Patterns**: (leave empty or `.git/*,node_modules/*`)

**Important**: Verify `/data/pipeshub/test-files` exists in container:
```bash
docker exec docker-compose-pipeshub-ai-1 ls -la /data/pipeshub/test-files
```

**Expected**: List of test files (calculator.ts, analyzer.py, etc.)

**If missing**: Create test files or adjust path

### Step 3: Save Configuration

1. Click "Save" or "Create Connector"
2. Expected: Success message
3. Connector status: "Active" or "Ready"

### Step 4: Verify Configuration in Database

**ArangoDB**:
```bash
curl -s http://localhost:8529/_api/cursor -d '{
  "query": "FOR doc IN connectors FILTER doc.name == \"Local Filesystem Connector\" RETURN doc"
}' | jq
```

**Expected**:
```json
{
  "_key": "...",
  "name": "Local Filesystem Connector",
  "type": "LOCAL_FILESYSTEM",
  "config": {
    "rootPath": "/data/pipeshub/test-files",
    "contentExtraction": true,
    "maxSizeMb": 10
  },
  "status": "active"
}
```

</configuration_steps>

<success_criteria>
- Connector visible in UI
- Configuration saved in database
- Status: Active
- Root path accessible in container
- Content extraction enabled
</success_criteria>

<estimated_time>5 minutes</estimated_time>

</phase>

## Phase 6: Initial Sync

<phase id="phase-6" name="Trigger and Verify File Sync">
<objective>Sync test files and verify records created with content</objective>

<sync_steps>

### Step 1: Trigger Sync

**Manual**:
1. In connector settings, find "Sync" button
2. Click "Sync Now" or "Start Sync"
3. Expected: Progress indicator appears

**Automated** (if UI button not working):
```bash
# Via API
curl -X POST http://localhost:8091/api/connectors/[connector-id]/sync

# Or trigger via database update
curl -s http://localhost:8529/_api/cursor -d '{
  "query": "FOR doc IN connectors FILTER doc.type == \"LOCAL_FILESYSTEM\" UPDATE doc WITH {lastSyncTrigger: DATE_NOW()} IN connectors"
}'
```

### Step 2: Monitor Sync Progress

**Watch Logs**:
```bash
docker logs -f docker-compose-pipeshub-ai-1 | grep -i "sync\|connector\|file"
```

**Expected Log Pattern**:
```
INFO - Starting sync for LOCAL_FILESYSTEM connector
INFO - Found 12 files to process
INFO - Processing file: calculator.ts
INFO - Created record with blockContainers: Block(data='...')
INFO - Processing file: analyzer.py
...
INFO - Sync complete: 12 files processed
```

### Step 3: Verify Records Created

**Query ArangoDB**:
```bash
curl -s http://localhost:8529/_api/cursor -d '{
  "query": "FOR doc IN records FILTER doc.connectorName == \"LOCAL_FILESYSTEM\" RETURN {name: doc.recordName, hasContent: HAS(doc, \"blockContainers\"), blockCount: LENGTH(doc.blockContainers.blocks)}"
}' | jq
```

**Expected Result**:
```json
[
  {"name": "calculator.ts", "hasContent": true, "blockCount": 1},
  {"name": "analyzer.py", "hasContent": true, "blockCount": 1},
  {"name": "config.json", "hasContent": true, "blockCount": 1},
  ...
]
```

**Count**:
```bash
curl -s http://localhost:8529/_api/cursor -d '{
  "query": "RETURN COUNT(FOR doc IN records FILTER doc.connectorName == \"LOCAL_FILESYSTEM\" RETURN doc)"
}' | jq
```

**Expected**: 12 records (or number of test files)

### Step 4: Verify Content Quality

**Sample Record**:
```bash
curl -s http://localhost:8529/_api/cursor -d '{
  "query": "FOR doc IN records FILTER doc.recordName == \"calculator.ts\" RETURN doc.blockContainers"
}' | jq
```

**Expected**:
```json
{
  "blocks": [
    {
      "data": "// Calculator implementation\nfunction add(a: number, b: number) {...}",
      "type": "text",
      ...
    }
  ]
}
```

**Verification**:
- ✅ blockContainers field exists
- ✅ blocks array has entries
- ✅ data field contains actual file content
- ✅ Content matches source file

### Step 5: Verify Kafka Events Produced

**Check Logs**:
```bash
docker logs docker-compose-pipeshub-ai-1 | grep -i "kafka\|event\|publish"
```

**Expected**:
```
INFO - Published event: newRecord (id: ...)
INFO - Published event: newRecord (id: ...)
...
```

</sync_steps>

<success_criteria>
- Sync completes without errors
- 12 records created (or expected count)
- All records have blockContainers field
- Content matches source files
- Kafka events produced
- No error logs
</success_criteria>

<estimated_time>10 minutes</estimated_time>

<failure_handling>
If sync fails:
1. Check connector status: Should be "Active"
2. Verify root path accessible
3. Check logs for specific errors
4. Common issues:
   - Permission denied: Check container volume mounts
   - File not found: Verify path correct
   - Content extraction failing: Check content extraction enabled
5. Re-trigger sync after fixing
</failure_handling>

</phase>

## Phase 7: Indexing Validation

<phase id="phase-7" name="Monitor and Verify Indexing">
<objective>Ensure indexing service processes all records and creates vectors</objective>

<monitoring_steps>

### Step 1: Check Indexing Service Status

**Verify Running**:
```bash
docker exec docker-compose-pipeshub-ai-1 ps aux | grep indexing
```

**Expected**:
```
root  123  ...  python -m app.indexing_main
```

**Check Health**:
```bash
curl -s http://localhost:8091/health | jq
```

**Expected**: `{"status":"healthy",...}`

### Step 2: Monitor Indexing Progress in UI

**Manual**:
1. Navigate to Connector Management page
2. Find Local Filesystem connector
3. Check indexing progress bar

**Expected Progression**:
```
Initially: 0% (0 Indexed, 12 Not Started)
After ~1-2 min: 25% (3 Indexed, 9 In Progress)
After ~5 min: 100% (12 Indexed, 0 Not Started)
```

**If stuck at 0%**: Indexing service issue - check logs

### Step 3: Watch Indexing Service Logs

**Command**:
```bash
docker logs -f docker-compose-pipeshub-ai-1 | grep -i "indexing\|embedding\|qdrant"
```

**Expected Log Pattern**:
```
INFO - Processing record [id] with event type: newRecord
INFO - Creating embedding for: calculator.ts
INFO - Stored vector in Qdrant: [id]
INFO - Processing record [id] with event type: newRecord
INFO - Creating embedding for: analyzer.py
...
INFO - Indexing complete for 12 records
```

**Watch for Errors**:
- ❌ "Record not found in database" - **CRITICAL** (blocker not fixed)
- ❌ "Qdrant connection failed" - Vector DB issue
- ❌ "Embedding API error" - LLM/embedding service issue

### Step 4: Verify Vectors in Qdrant

**Check Collection**:
```bash
curl -s http://localhost:6333/collections | jq
```

**Expected**: Collection created (e.g., "records" or "pipeshub")

**Count Vectors**:
```bash
curl -s http://localhost:6333/collections/[collection-name] | jq '.result.vectors_count'
```

**Expected**: 12 vectors (matches record count)

**Sample Vector**:
```bash
curl -s -X POST http://localhost:6333/collections/[collection-name]/points/scroll \
  -H "Content-Type: application/json" \
  -d '{"limit": 1}' | jq
```

**Expected**:
```json
{
  "result": {
    "points": [
      {
        "id": "...",
        "payload": {
          "recordId": "...",
          "fileName": "calculator.ts",
          "content": "..."
        },
        "vector": [0.123, -0.456, ...]
      }
    ]
  }
}
```

### Step 5: Validate Indexing Completion

**UI Check**:
- Indexing progress: 100%
- All records: "Indexed" status
- No failed records

**Database Check**:
```bash
# Check indexing status in ArangoDB (if tracked there)
curl -s http://localhost:8529/_api/cursor -d '{
  "query": "FOR doc IN records FILTER doc.connectorName == \"LOCAL_FILESYSTEM\" COLLECT status = doc.indexingStatus WITH COUNT INTO count RETURN {status, count}"
}' | jq
```

**Expected**:
```json
[
  {"status": "indexed", "count": 12}
]
```

</monitoring_steps>

<success_criteria>
- Indexing service running (no restarts)
- No "record not found" errors
- UI shows 100% progress
- Qdrant has 12 vectors
- All records have "indexed" status
- Logs show successful embedding creation
</success_criteria>

<estimated_time>5-10 minutes (indexing runs in background)</estimated_time>

<failure_handling>
If indexing fails:

**Error: "Record not found"**:
- **Root Cause**: Blocker from research not fixed properly
- **Action**: Return to Phase 3, re-apply fix correctly
- **Verify**: Check indexing service query logic

**Error: "Qdrant connection failed"**:
- **Check**: `docker ps` - Is qdrant container up?
- **Check**: `curl http://localhost:6333` - Reachable?
- **Action**: Restart qdrant: `docker compose restart qdrant`

**Stuck at 0% with no errors**:
- **Possible**: Kafka consumer offset issue
- **Action**: Reset consumer group
  ```bash
  docker exec docker-compose-kafka-1 kafka-consumer-groups.sh \
    --bootstrap-server localhost:9092 \
    --group indexing-service \
    --reset-offsets --to-earliest --execute \
    --topic record-events
  ```
- **Action**: Restart indexing service

**Partial indexing (e.g., 3/12)**:
- **Check**: Logs for specific file errors
- **Possible**: Large files timing out, binary files failing
- **Action**: Skip problematic files if not critical for demo

</failure_handling>

</phase>

## Phase 8: Assistant Q&A Testing

<phase id="phase-8" name="Test Assistant Question Answering">
<objective>Verify Assistant can answer questions about indexed files with verification metadata</objective>

<testing_steps>

### Step 1: Access Assistant Interface

**Navigate to**: http://localhost:3000/assistant or /chat or /ask (depends on UI)

**Expected**: Chat interface or Q&A form

**If not found**:
- Check UI navigation menu
- Try: /search, /knowledge, /qa
- Fallback: Test via API

### Step 2: Test Query 1 - TypeScript File

**Query**: "What does calculator.ts do?"

**Expected Response**:
```
The calculator.ts file implements basic arithmetic operations. It contains functions for addition, subtraction, multiplication, and division. The file exports these functions for use in other modules.

Sources:
- calculator.ts (lines 1-25)
- Confidence: High (0.89)
- Retrieved from Local Filesystem connector
```

**Validation**:
- ✅ Response mentions calculator functionality
- ✅ Answer is accurate (matches file content)
- ✅ Source file name included
- ✅ Confidence score or verification metadata present
- ✅ No hallucination (didn't make up content)

### Step 3: Test Query 2 - Python File

**Query**: "Explain the analyzer.py file"

**Expected Response**:
```
The analyzer.py file provides text analysis functionality. It includes functions for tokenization, sentiment analysis, and keyword extraction. The main Analyzer class processes text input and returns structured analysis results.

Sources:
- analyzer.py (lines 1-50)
- Confidence: High (0.92)
```

**Validation**:
- ✅ Describes analyzer functionality
- ✅ Accurate (matches file)
- ✅ Metadata present

### Step 4: Test Query 3 - JSON File

**Query**: "What's in config.json?"

**Expected Response**:
```
The config.json file contains application configuration settings including:
- Database connection URL
- API endpoint URLs
- Feature flags (e.g., enableContentExtraction: true)
- Logging configuration

Sources:
- config.json
- Confidence: High (0.95)
```

**Validation**:
- ✅ Lists config contents
- ✅ Accurate
- ✅ Metadata present

### Step 5: Test Query 4 - Cross-File Question

**Query**: "What programming languages are used in these files?"

**Expected Response**:
```
The codebase uses multiple programming languages:
- TypeScript (calculator.ts)
- Python (analyzer.py)
- JSON for configuration
- CSS for styling
- Markdown for documentation

Sources:
- Multiple files from Local Filesystem connector
- Confidence: High
```

**Validation**:
- ✅ Aggregates across files
- ✅ Lists correct languages
- ✅ Multiple sources cited

### Step 6: Verify Metadata Format

**Check Response Structure**:

**If API available**:
```bash
curl -X POST http://localhost:8091/api/assistant/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What does calculator.ts do?"}' | jq
```

**Expected Structure**:
```json
{
  "answer": "The calculator.ts file...",
  "sources": [
    {
      "fileName": "calculator.ts",
      "recordId": "...",
      "relevanceScore": 0.89,
      "connector": "Local Filesystem"
    }
  ],
  "confidence": 0.89,
  "retrievalMethod": "vector_search"
}
```

**Validation**:
- ✅ `sources` array present
- ✅ `fileName` included
- ✅ `confidence` or `relevanceScore` present
- ✅ `retrievalMethod` or similar metadata

</testing_steps>

<success_criteria>
- All 4 test queries answered successfully
- Answers are accurate (match file content)
- No hallucinations or made-up content
- Source file names included in responses
- Verification metadata present (confidence/sources/method)
- UI displays responses clearly
- Response time acceptable (< 5 seconds per query)
</success_criteria>

<estimated_time>10 minutes</estimated_time>

<failure_handling>

**Error: "No results found"**:
- **Check**: Qdrant has vectors (Phase 7 validation)
- **Check**: Search endpoint configured correctly
- **Possible**: Collection name mismatch
- **Action**: Verify search queries Qdrant collection

**Error: Generic answers (no specific file content)**:
- **Possible**: Not using retrieved content, just LLM knowledge
- **Check**: Retrieval step in Assistant implementation
- **Action**: Verify RAG pipeline connects Qdrant → LLM

**Missing metadata**:
- **Possible**: Response format not including sources
- **Check**: Assistant response serialization
- **Action**: Add metadata fields to response
- **Workaround**: If time-critical, document as known limitation for demo

**Inaccurate answers**:
- **Check**: Retrieved chunks match query
- **Possible**: Embedding quality or chunking issues
- **Action**: Verify embeddings are created correctly
- **Workaround**: Use simpler queries that match file names exactly

</failure_handling>

</phase>

## Phase 9: Demo Rehearsal

<phase id="phase-9" name="Full Demo Run-Through">
<objective>Practice complete demo flow and identify rough edges</objective>

<rehearsal_steps>

### Step 1: Time the Demo

**Full Flow**:
1. Start timer
2. Navigate to localhost:3000
3. Login (af@o2.services / Vilisaped1!)
4. Go to Assistant/Q&A interface
5. Ask question: "What does calculator.ts do?"
6. Show response with metadata
7. Ask question: "List the files in the codebase"
8. Show response
9. Navigate to Connector Management
10. Show indexing status (100%)
11. Stop timer

**Target Time**: 3-5 minutes for full demo

**If longer**: Identify slow steps to optimize or skip

### Step 2: Prepare Talking Points

**Intro (30 seconds)**:
- "PipesHub is a knowledge management platform"
- "Connects to various data sources"
- "Extracts content and makes it searchable"

**Demo (3 minutes)**:
- "Here's the Assistant interface"
- "Let's ask about our codebase"
- [Ask first question, show response]
- "Notice the verification metadata - sources and confidence"
- [Ask second question]
- "The system indexed X files from local filesystem"
- [Show connector status]

**Wrap-up (30 seconds)**:
- "All content is automatically indexed"
- "Responses include provenance information"
- "Ready for integration with more data sources"

### Step 3: Identify Rough Edges

**Common Issues**:
- Slow response times → Pre-cache queries or add loading messages
- UI navigation unclear → Document path: Dashboard → Assistant
- Metadata not prominent → Highlight sources section
- Terminology confusing → Prepare explanations

**Polish**:
- Browser window size/zoom for visibility
- Clear browser history (no distracting autocomplete)
- Have URLs bookmarked
- Close unnecessary tabs
- Disable notifications

### Step 4: Prepare Backup Plans

**If indexing fails during demo**:
- Don't trigger sync live
- Show pre-indexed state
- Explain: "Previously synced X files"

**If Assistant is slow**:
- Have screenshot of good response ready
- Explain: "Response typically takes 2-3 seconds"

**If UI is down**:
- Have curl commands ready to show API working
- Demonstrate via terminal if needed

### Step 5: Test from Clean State

**Simulate Demo Start**:
1. Clear browser cache/cookies
2. Open new incognito window
3. Run through demo flow
4. Time it
5. Note any issues

**If issues found**:
- Fix immediately if critical
- Document as known issue if not critical
- Prepare workaround or explanation

</rehearsal_steps>

<success_criteria>
- Full demo completes in 3-5 minutes
- All steps work smoothly
- Talking points prepared
- Rough edges identified and addressed
- Backup plans ready
- Confident in flow
</success_criteria>

<estimated_time>15 minutes</estimated_time>

</phase>

## Decisions Required

<decision id="decision-1">
<question>Should we automate account creation with Playwright or do it manually?</question>
<context>Phase 4 needs user account created before connector setup</context>
<options>
  <option id="A">
    <description>Manual account creation via UI</description>
    <pros>
      - More reliable (no automation failures)
      - Can verify UI works correctly
      - Simple and quick
    </pros>
    <cons>
      - Requires manual steps
      - Harder to reproduce
    </cons>
    <time>5 minutes</time>
    <risk>Low</risk>
  </option>
  <option id="B">
    <description>Playwright automation script</description>
    <pros>
      - Repeatable and scriptable
      - Can be part of test suite
      - Faster if working
    </pros>
    <cons>
      - May fail on UI changes
      - Need to debug if broken
      - Extra development time
    </cons>
    <time>15 minutes (including script creation)</time>
    <risk>Medium</risk>
  </option>
</options>
<recommendation>Option A - Manual</recommendation>
<rationale>Time-critical demo prep. Manual is faster and more reliable. Save automation for post-demo.</rationale>
<time_impact>Saves 10 minutes vs automation approach</time_impact>
</decision>

<decision id="decision-2">
<question>Should we backfill existing records or just test with new sync?</question>
<context>After fixing blockers, existing 1,690 records won't have indexed content unless backfilled</context>
<options>
  <option id="A">
    <description>Clean databases and sync fresh (Plan approach)</description>
    <pros>
      - Guaranteed clean state
      - Tests full end-to-end flow
      - No legacy data issues
    </pros>
    <cons>
      - Loses existing data
      - Need to re-sync all files
    </cons>
    <time>Per plan timeline</time>
    <risk>Low</risk>
  </option>
  <option id="B">
    <description>Keep existing data, only sync/index new test files</description>
    <pros>
      - Faster (no clean/resync needed)
      - Preserves existing work
    </pros>
    <cons>
      - Mixed state (old + new)
      - May have inconsistencies
      - Doesn't test full flow
    </cons>
    <time>Saves ~30 minutes</time>
    <risk>Medium - May have hidden issues</risk>
  </option>
  <option id="C">
    <description>Backfill existing 1,690 records with indexing</description>
    <pros>
      - Complete dataset indexed
      - Impressive demo (1,690+ records)
    </pros>
    <cons>
      - Time-consuming (10-20 min for 1,690 records)
      - May surface issues at scale
      - Not necessary for demo
    </cons>
    <time>+15-20 minutes</time>
    <risk>Medium - Scale issues possible</risk>
  </option>
</options>
<recommendation>Option A - Clean and sync fresh</recommendation>
<rationale>Most reliable for demo. Tests complete flow. 12 test files sufficient to demonstrate capability.</rationale>
<time_impact>No change from base plan</time_impact>
</decision>

## Risk Management

### Risk 1: Indexing service blocker not fully fixed

**Probability**: Medium

**Impact**: Critical (demo-blocking)

**Mitigation**:
- Thorough verification in Phase 3 (apply fix)
- Test with single file before full sync
- Monitor logs closely in Phase 7
- Have research findings handy for debugging

**Contingency**:
- If still broken: Debug live during execution phase
- Fallback: Show content extraction working (skip Assistant Q&A if needed)
- Have screenshots of working state from previous session

### Risk 2: Services fail to start after deployment

**Probability**: Low

**Impact**: High (delays timeline)

**Mitigation**:
- Check build status before deployment
- Verify .env configuration
- Test database connections immediately
- Monitor health checks

**Contingency**:
- Restart failed services individually
- Check logs for specific errors
- Fallback: Use running environment if current state partially working

### Risk 3: Indexing takes too long (> 10 minutes)

**Probability**: Low

**Impact**: Medium (eats into buffer time)

**Mitigation**:
- Only sync 12 test files (not 1,690)
- Monitor progress closely
- Start with 1-2 files as smoke test

**Contingency**:
- Let indexing run in background during Phase 8 prep
- If stuck: Cancel and retry with single file
- Fallback: Show partial results (even 3/12 files demonstrates capability)

### Risk 4: Assistant Q&A not implemented or broken

**Probability**: Low-Medium (unknown from research)

**Impact**: High (core demo feature)

**Mitigation**:
- Verify implementation exists in Phase 8
- Test with simple queries first
- Check Qdrant connectivity early

**Contingency**:
- If not implemented: Direct Qdrant queries via curl (show search working)
- If partial: Show what works, explain what's in progress
- Fallback: Demonstrate content extraction + indexing (skip Q&A)

### Risk 5: Running out of time

**Probability**: Medium

**Impact**: Critical

**Mitigation**:
- Track time per phase
- Skip non-critical steps if running late
- Focus on core demo path

**Contingency**:
- Minimum viable demo: Show indexed content + basic search
- Skip: Demo rehearsal, polish, backfill
- Accept: Some rough edges if core functionality works

## Timeline Summary

**Total Estimated Time**: ~2-2.5 hours

| Phase | Duration | Can Parallelize | Critical Path |
|-------|----------|-----------------|---------------|
| Phase 0: Preparation | 10 min | No | Yes |
| Phase 1: Database Clean | 15 min | No | Yes |
| Phase 2: Deployment | 15 min | No | Yes |
| Phase 3: Fixes | Variable* | No | Yes |
| Phase 4: Account Setup | 5 min | No | Yes |
| Phase 5: Connector Config | 5 min | No | Yes |
| Phase 6: Sync | 10 min | No | Yes |
| Phase 7: Indexing | 10 min | Partial** | Yes |
| Phase 8: Testing | 10 min | No | Yes |
| Phase 9: Rehearsal | 15 min | No | Optional |

*Phase 3 time depends on research findings
**Phase 7 can run in background while preparing Phase 8

**Critical Path**: Phases 0-8 (Phase 9 optional if time-constrained)

**Time Remaining**: ~7 hours after research
**Buffer**: ~4.5-5 hours

**Risk Assessment**: **Low-Medium** - Comfortable buffer for issues

## Success Metrics

**Minimum for Demo Success**:
- ✅ UI accessible and account created
- ✅ Connector configured and active
- ✅ Files synced with content in database
- ✅ At least 50% of files indexed
- ✅ Assistant answers at least 1 query correctly
- ✅ Some verification metadata visible

**Complete Success** (Ideal):
- ✅ All databases clean and redeployed
- ✅ All services healthy
- ✅ Account created and logged in
- ✅ Connector configured correctly
- ✅ 12 test files synced successfully
- ✅ 100% indexing complete
- ✅ Assistant answers multiple queries accurately
- ✅ Full verification metadata in responses
- ✅ Demo rehearsed and polished
- ✅ Backup plans ready

## Metadata

<confidence>High - Plan is comprehensive and time-proven</confidence>

<dependencies>
**From Research**:
- Critical blocker identification (from 011-demo-prep-research)
- Fix procedures for identified issues
- System state assessment

**External**:
- Docker access for deployment
- Database access for clean operations
- Browser for UI testing
- ~7 hours execution time
</dependencies>

<open_questions>
- Exact fix procedures depend on research findings (Phase 3 content)
- Assistant Q&A implementation status unknown until testing
- Optimal chunking/embedding strategy for best search results
</open_questions>

<assumptions>
- Research phase will identify clear root cause for indexing blocker
- Database clean won't break schema (or migrations will replay)
- Test files exist in expected location
- Assistant feature is at least partially implemented
- 7 hours is sufficient for execution and testing
</assumptions>

<blockers>
None - ready to execute immediately after research phase completes
</blockers>

<next_steps>
1. Wait for 011-demo-prep-research to complete
2. Review research findings for critical blockers
3. Update Phase 3 with exact fix procedures from research
4. Execute plan starting at Phase 0
</next_steps>
```

## SUMMARY.md Requirement

Create `.prompts/012-demo-prep-plan/SUMMARY.md`:

```markdown
# Demo Prep Plan - Deployment and Validation

**One-liner**: 9-phase plan from database clean through deployment, fixes, sync, indexing, to Assistant Q&A testing with verification metadata - 2-2.5 hours execution, ~5 hour buffer for demo at 10AM PST

**Version**: v1

**Total Phases**: 9 (Phases 0-8 critical, Phase 9 optional)

**Estimated Time**: 2-2.5 hours execution + 4.5-5 hours buffer

**Key Decisions**:
- Clean database approach: Full wipe and fresh sync (most reliable)
- Account creation: Manual via UI (faster and more reliable than automation)
- Scope: 12 test files only (sufficient for demo, faster than 1,690 records)

**Phases Overview**:
- **Phase 0** (10 min): Pre-deployment prep - check build, stop containers, review research
- **Phase 1** (15 min): Database clean - PostgreSQL, ArangoDB, Qdrant full wipe
- **Phase 2** (15 min): Docker deployment - fresh containers, health checks, verify connections
- **Phase 3** (variable): Apply fixes - code changes from research findings to resolve blockers
- **Phase 4** (5 min): UI account setup - create af@o2.services account manually
- **Phase 5** (5 min): Connector config - Local Filesystem with content extraction enabled
- **Phase 6** (10 min): Initial sync - 12 test files with content verification
- **Phase 7** (10 min): Indexing validation - monitor 0%→100%, verify Qdrant vectors
- **Phase 8** (10 min): Assistant Q&A testing - 4 test queries with metadata validation
- **Phase 9** (15 min): Demo rehearsal - full run-through, timing, polish (optional)

**Critical Path**: Phases 0-8 (Phase 9 optional if time-constrained)

**Risks**:
- **Medium/Critical**: Indexing blocker not fully fixed → Mitigation: Thorough Phase 3 verification, live debugging if needed
- **Low/High**: Services fail to start → Mitigation: Pre-check build, monitor health
- **Low/Medium**: Indexing takes too long → Mitigation: Only 12 files, background execution
- **Medium/High**: Assistant Q&A not implemented → Contingency: Show search working via API

**Decisions Needed**:
- None - all critical decisions resolved (clean approach, manual account, 12 test files)

**Open Questions**:
- Phase 3 fix procedures depend on research findings (will be filled in after research)
- Assistant implementation status (will be discovered in Phase 8)

**Blockers**:
- None - ready to execute after research phase completes

**Next Step**:
- Wait for 011-demo-prep-research completion
- Review research SUMMARY.md for critical blockers
- Update Phase 3 with exact fix procedures
- Execute starting at Phase 0 (stop containers, check build)

**Timeline Safety**:
- Execution: 2-2.5 hours
- Buffer: 4.5-5 hours
- Risk: Low-Medium (comfortable margin for issues)
```

## Success Criteria

**Minimum Requirements**:
- ✅ All 9 phases defined with clear objectives
- ✅ Each phase has measurable success criteria
- ✅ Dependencies between phases explicitly stated
- ✅ Exact commands provided for each step
- ✅ Verification commands for each phase
- ✅ Timeline estimates realistic and justified
- ✅ Decision points identified with recommendations
- ✅ Builds on research findings (flexible Phase 3)
- ✅ SUMMARY.md created with substantive one-liner
- ✅ Plan leads to working demo

**Quality Standards**:
- Phases are sequential and logically ordered
- Commands are copy-paste ready
- Success criteria are objectively measurable
- Failure handling provided for risky phases
- Time estimates include wait times
- Verification commands return expected outputs
- No ambiguous steps (all are executable)

## Execution Notes

- **Input**: Research findings from 011-demo-prep-research
- **Time Estimate**: 30-45 minutes to create comprehensive plan
- **Approach**: Build on research root cause, create step-by-step playbook
- **Focus**: Actionable commands, clear verification, time management

Begin planning now and save output to the specified location.
