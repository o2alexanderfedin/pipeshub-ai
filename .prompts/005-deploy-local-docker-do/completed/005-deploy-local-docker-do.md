# Meta-Prompt: Deploy PipesHub to Local Docker

## Objective

Deploy the complete PipesHub application stack to local Docker containers using docker-compose, including:
- Full verification of service health
- Database migrations execution
- API endpoint testing
- Comprehensive integration testing

This enables local development and testing of the Hupyy-PipesHub integration in a production-like environment.

## Context

**Project**: PipesHub-AI with Hupyy SMT verification integration
**Deployment target**: Local Docker containers
**Scope**: Full stack (frontend, backend, databases, Kafka, Redis, all services)
**Environment**: `.env` file exists, needs validation for completeness

**Related implementations**:
- Hupyy integration (Phases 0-4) recently completed
- Local filesystem connector implemented
- Verification services (orchestrator, updaters, ranker) ready for deployment

## Requirements

### Pre-Deployment

1. **Environment Validation**
   - Read `.env` file in project root
   - Verify all required environment variables are present:
     - `VITE_MAPBOX_TOKEN` (frontend)
     - `ANTHROPIC_API_KEY` (backend AI features)
     - Database credentials (POSTGRES_*, MONGODB_*, etc.)
     - Kafka/Redis connection strings
     - Hupyy API URL and credentials (if configured)
   - Report missing variables with clear error messages
   - DO NOT create or modify `.env` - only validate

2. **Docker Environment Check**
   - Verify Docker is running (`docker info`)
   - Check docker-compose is available (`docker-compose --version`)
   - Check available disk space (need at least 10GB free)
   - List currently running containers (`docker ps`)
   - Warn if ports 3001, 5434, 8090, 9092 (Kafka), 6379 (Redis) are in use

### Deployment Steps

Execute in order, stopping on any failure:

1. **Stop Existing Containers** (if any)
   ```bash
   docker-compose down
   ```
   - Report what was stopped

2. **Build All Images**
   ```bash
   docker-compose build --no-cache
   ```
   - Use `--no-cache` to ensure latest code changes are included
   - Report build progress for each service
   - Capture and log any build errors

3. **Start All Services**
   ```bash
   docker-compose up -d
   ```
   - Start in detached mode
   - Wait for healthchecks to pass (use `docker-compose ps` to monitor)
   - Services to start:
     - postgres (database)
     - mongodb (config/feature flags)
     - redis (caching)
     - kafka + zookeeper (event streaming)
     - arangodb (knowledge graph)
     - qdrant (vector DB)
     - backend (Python/Node.js services)
     - frontend (React app)

4. **Wait for Service Readiness**
   - Poll `docker-compose ps` until all services show "healthy" status
   - Timeout: 5 minutes
   - If any service fails to start, capture logs and report

### Database Migrations

Execute database migrations for each database:

1. **PostgreSQL Migrations** (if applicable)
   ```bash
   docker-compose exec backend npm run migrate:latest
   ```

2. **MongoDB Initialization**
   - Verify feature_flags collection exists
   - Verify verification flags are initialized (from Phase 0)

3. **ArangoDB Initialization**
   - Verify knowledge graph collections exist
   - Verify citation network edges created

### Health Checks

Perform comprehensive health checks:

1. **Service Health Endpoints**
   ```bash
   # Backend health
   curl http://localhost:3001/health

   # Expected: {"status": "ok", "services": {"postgres": "up", "mongodb": "up", ...}}
   ```

2. **Database Connectivity**
   ```bash
   # PostgreSQL
   docker-compose exec postgres psql -U oilfield -d oilfield -c "SELECT 1;"

   # MongoDB
   docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

   # ArangoDB
   curl http://localhost:8529/_api/version

   # Qdrant
   curl http://localhost:6333/health
   ```

3. **Kafka Topics**
   ```bash
   docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
   ```
   - Verify verification topics exist:
     - `verify_chunks`
     - `verification_complete`
     - `verification_failed`
     - `pagerank_recalc`

4. **Redis Connection**
   ```bash
   docker-compose exec redis redis-cli ping
   ```
   - Expected: "PONG"

### API Endpoint Testing

Test critical API endpoints:

1. **Search API** (core functionality)
   ```bash
   curl -X POST http://localhost:3001/api/search \
     -H "Content-Type: application/json" \
     -d '{"query": "test search", "limit": 5}'
   ```
   - Verify returns valid JSON with results array

2. **Connector API** (local filesystem)
   ```bash
   curl http://localhost:3001/api/connectors
   ```
   - Verify local_filesystem connector is listed

3. **Verification Status** (Hupyy integration)
   ```bash
   curl http://localhost:3001/api/verification/status
   ```
   - Verify returns feature flag status
   - Check verification_enabled, verification_top_k, etc.

4. **Frontend Loading**
   ```bash
   curl http://localhost:8090
   ```
   - Verify HTML returned (React app served by nginx)

### Integration Testing

Run end-to-end integration tests:

1. **Connector Sync Test**
   - Trigger local filesystem connector sync
   - Verify documents indexed to Qdrant
   - Check ArangoDB knowledge graph updated

2. **Search Pipeline Test**
   - Execute search query
   - Verify semantic retrieval works (Qdrant)
   - Verify knowledge graph enhancement (ArangoDB)
   - Check ranking formula applied

3. **Verification Pipeline Test** (if enabled)
   - Enable verification via feature flag
   - Trigger search that produces verification
   - Verify Kafka messages published to `verify_chunks`
   - Check orchestrator processes verification
   - Verify Qdrant payloads updated
   - Check ArangoDB metrics updated

4. **Cache Test**
   - Execute same query twice
   - Verify second query uses Redis cache (faster response)

### Post-Deployment Report

Create comprehensive report in SUMMARY.md:

1. **Service Status**
   - List all services with status (up/down/degraded)
   - Include container IDs and port mappings

2. **Health Check Results**
   - Database connectivity: ✓/✗
   - API endpoints: ✓/✗
   - Kafka topics: ✓/✗
   - Redis: ✓/✗

3. **Integration Test Results**
   - Connector sync: ✓/✗
   - Search pipeline: ✓/✗
   - Verification pipeline: ✓/✗ (or skipped if disabled)
   - Cache: ✓/✗

4. **Access Information**
   - Frontend URL: http://localhost:8090
   - Backend API: http://localhost:3001
   - Grafana (if started): http://localhost:3000
   - Database ports: PostgreSQL (5434), MongoDB (27017), etc.

5. **Logs Location**
   - How to view logs: `docker-compose logs -f [service]`
   - How to restart service: `docker-compose restart [service]`

6. **Known Issues**
   - Report any warnings or non-critical failures
   - Suggest fixes for common issues

7. **Next Steps**
   - Instructions for accessing the application
   - How to enable Hupyy verification (if not already enabled)
   - How to trigger connector syncs
   - How to monitor with Grafana

## Output Specification

Create `SUMMARY.md` at: `.prompts/005-deploy-local-docker-do/SUMMARY.md`

**Required sections** (see structure below):

```markdown
# PipesHub Local Docker Deployment

**[One-liner describing deployment status]**

## Deployment Info
- Started: [timestamp]
- Completed: [timestamp]
- Duration: [time taken]
- Status: ✓ Success / ✗ Failed / ⚠️ Partial

## Services Status

| Service | Status | Container ID | Port |
|---------|--------|--------------|------|
| postgres | ✓ Healthy | abc123... | 5434 |
| mongodb | ✓ Healthy | def456... | 27017 |
| ...

## Health Checks

- [x] Database connectivity
- [x] API endpoints responding
- [x] Kafka topics created
- [x] Redis operational
- [x] Frontend accessible

## Integration Tests

- [x] Connector sync: 15 documents indexed
- [x] Search pipeline: Query returned 5 results in 245ms
- [x] Verification pipeline: Skipped (verification_enabled=false)
- [x] Cache: Hit rate 0% (fresh deployment)

## Access URLs

- Frontend: http://localhost:8090
- Backend API: http://localhost:3001
- Grafana: http://localhost:3000 (admin/admin)
- Databases: See service table above

## Issues & Warnings

[List any non-critical issues, warnings, or degraded services]

## Logs & Troubleshooting

View logs:
\`\`\`bash
docker-compose logs -f [service-name]
\`\`\`

Restart service:
\`\`\`bash
docker-compose restart [service-name]
\`\`\`

Full restart:
\`\`\`bash
docker-compose down && docker-compose up -d
\`\`\`

## Next Steps

1. Access frontend at http://localhost:8090
2. [Additional recommended next steps based on deployment state]

## Decisions Needed

[Any user decisions required, or "None" if deployment is fully operational]

## Blockers

[Any blocking issues preventing full functionality, or "None"]
```

## Error Handling

### Build Failures
- Capture full build logs
- Identify which service failed
- Report common causes (missing dependencies, syntax errors, etc.)
- DO NOT continue to deployment if build fails

### Service Start Failures
- Wait up to 5 minutes for services to become healthy
- If service fails to start:
  - Capture last 50 lines of logs: `docker-compose logs --tail=50 [service]`
  - Check common issues:
    - Port conflicts
    - Missing environment variables
    - Database connection failures
    - Insufficient memory/disk
  - Report issue with suggested fix
  - Ask user: Continue with degraded deployment? / Stop and fix? / Retry?

### Migration Failures
- Capture migration error output
- Check if migrations already applied (`docker-compose exec postgres psql -U oilfield -d oilfield -c "\dt"`)
- Report schema state
- Suggest: Skip migrations? / Rollback and retry? / Stop?

### Health Check Failures
- Report which checks failed
- Provide diagnostic commands to run manually
- DO NOT mark deployment as successful if critical checks fail
- Partial success allowed for non-critical services

### Integration Test Failures
- Integration test failures are warnings, not blockers
- Report failures but mark deployment as successful with warnings
- User can investigate and fix post-deployment

## Success Criteria

**Deployment considered successful if**:
- ✓ All critical services started and healthy (postgres, mongodb, kafka, redis, backend, frontend)
- ✓ Database migrations completed successfully
- ✓ All health check endpoints responding
- ✓ At least one integration test passed (search pipeline minimum)

**Deployment considered partial if**:
- ⚠️ Non-critical services failed (Grafana, optional monitoring)
- ⚠️ Integration tests failed (can debug post-deployment)
- ⚠️ Warnings present but core functionality works

**Deployment considered failed if**:
- ✗ Critical services won't start (backend, frontend, databases)
- ✗ Database migrations failed
- ✗ Health checks timeout
- ✗ Environment validation failed (missing critical variables)

## Implementation Notes

1. **Use TodoWrite** to track deployment steps
2. **Stream output** for long-running operations (docker-compose build)
3. **Parallel health checks** where possible (test multiple endpoints concurrently)
4. **Timeout all operations** to prevent hanging (use `timeout` command or async timeout)
5. **Preserve logs** if failures occur (copy to `.prompts/005-deploy-local-docker-do/logs/`)
6. **Test against actual Hupyy integration** from Phases 0-4
7. **Verify feature flags** are accessible and can be toggled

## Special Considerations

### Hupyy Integration
- Hupyy API URL may not be configured (development mode)
- Verification should be disabled by default (feature flag)
- If enabled, verify circuit breaker is operational
- Check Grafana dashboard for verification metrics

### Data Persistence
- Do NOT run `docker-compose down -v` (would delete database data)
- If reset needed, confirm with user first
- Preserve Qdrant vectors and ArangoDB graph data

### Resource Limits
- Full stack requires ~8GB RAM
- Check `docker stats` to monitor resource usage
- Warn if system resources constrained
- Suggest stopping non-essential services if needed

## References

- Docker Compose file: `deployment/docker-compose/docker-compose.prod.yml`
- Environment template: `.env.example`
- Hupyy operations runbook: `docs/runbooks/hupyy-verification-ops.md`
- Implementation summary: `IMPLEMENTATION_SUMMARY.md`
