# Verify Configuration and Redeploy to Local Docker

<objective>
Verify all configuration parameters for PipesHub AI are correctly set, then perform a clean redeployment to local Docker with all services running and healthy.

This ensures the system is properly configured with:
- Correct volume mounts for Local Filesystem connector
- Proper database credentials
- AI model configuration (Claude LLM + local embeddings)
- All services communicating correctly
- Verification checkbox functional in UI
</objective>

<context>
The PipesHub AI system has been configured with Hupyy SMT verification integration. All configuration details are documented in `CLAUDE.md` and `deployment/docker-compose/docker-compose.dev.yml`.

Recent changes:
- Hupyy SMT verification checkbox integrated into chat UI (release 0.1.8-alpha)
- Local Filesystem connector default path updated to `/data/local-files`
- Volume mount added: `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig:/data/local-files:ro`
- CLAUDE.md updated with all configuration parameters

Review these files for current configuration:
- `CLAUDE.md` - All credentials, database connections, AI models
- `deployment/docker-compose/docker-compose.dev.yml` - Docker services configuration
- `.env` files if they exist
</context>

<requirements>

## Phase 1: Configuration Verification

Verify the following parameters are correctly configured:

### 1. Docker Volume Mounts
- Check `docker-compose.dev.yml` has volume mount:
  - Host: `/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig`
  - Container: `/data/local-files`
  - Mode: Read-only (`:ro`)

### 2. Database Credentials
Verify these match CLAUDE.md configuration:
- **ArangoDB**: root/your_password on localhost:8529, database `es`
- **MongoDB**: admin/password on localhost:27017, database `es`
- **Qdrant**: API key `your_qdrant_secret_api_key` on localhost:6333/6334

### 3. AI Model Configuration
- **LLM**: ANTHROPIC_API_KEY environment variable set in docker-compose
- **Embedding**: USE_LOCAL_EMBEDDINGS=true, EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

### 4. Local Filesystem Connector
- Default path in `backend/python/app/connectors/sources/local_filesystem/connector.py` should be `/data/local-files`
- This was changed from `/data/pipeshub/test-files` in commit 7e3fbd78

### 5. Application Credentials
- Email: af@o2.services
- Password: Vilisaped1!
- (These are used for login after deployment)

## Phase 2: Clean Redeployment

Execute a clean Docker deployment:

1. **Stop and clean existing containers**:
   ```bash
   cd deployment/docker-compose
   docker compose -f docker-compose.dev.yml down
   ```

2. **Rebuild images** (to pick up latest code changes):
   ```bash
   docker compose -f docker-compose.dev.yml build pipeshub-ai
   ```

3. **Start all services**:
   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```

4. **Verify all services are healthy**:
   ```bash
   docker compose -f docker-compose.dev.yml ps
   ```

   Expected: All services should show "Up" status, no "Restarting"

5. **Check volume mount is accessible**:
   ```bash
   docker compose -f docker-compose.dev.yml exec pipeshub-ai ls -la /data/local-files | head -20
   ```

   Expected: Should show project directories (backend, frontend, etc.)

## Phase 3: Service Verification

Verify each service is functioning:

1. **Frontend accessible**: http://localhost:3000
2. **ArangoDB**: http://localhost:8529
3. **Qdrant**: http://localhost:6333/dashboard
4. **MongoDB**: Port 27017 accessible

Check service logs for errors:
```bash
docker compose -f docker-compose.dev.yml logs pipeshub-ai --tail=50
```

## Phase 4: Feature Verification

Verify the Hupyy verification checkbox is functional:

1. Open http://localhost:3000 in browser
2. Log in with credentials (af@o2.services / Vilisaped1!)
3. Navigate to chat interface
4. Verify "Enable SMT Verification" checkbox is visible below message input
5. Checkbox should be clickable and persist state

</requirements>

<output>

Create a verification report: `./deployment/VERIFICATION-REPORT.md`

Include:
- ✅/❌ for each configuration parameter verified
- Service health status (all services Up/Restarting/Down)
- Volume mount verification (accessible/not accessible)
- Frontend accessibility (working/not working)
- Verification checkbox status (visible/not visible)
- Any errors or issues encountered
- Timestamp of deployment

Format:
```markdown
# PipesHub Local Docker Deployment Verification

**Deployment Date**: [timestamp]
**Version**: 0.1.8-alpha

## Configuration Verification
- [ ] Docker volume mount: /Users/.../pipeshub-ai-orig -> /data/local-files
- [ ] ArangoDB credentials
- [ ] MongoDB credentials
- [ ] Qdrant credentials
- [ ] Anthropic API key
- [ ] Local embeddings enabled
- [ ] Connector default path: /data/local-files

## Service Health
- [ ] pipeshub-ai: Up
- [ ] mongodb: Up
- [ ] arango: Up
- [ ] qdrant: Up
- [ ] kafka-1: Up
- [ ] zookeeper: Up
- [ ] redis: Up
- [ ] etcd: Up

## Feature Verification
- [ ] Frontend accessible (http://localhost:3000)
- [ ] Login successful
- [ ] Verification checkbox visible
- [ ] Volume mount accessible inside container

## Issues
[List any problems encountered]

## Next Steps
[What needs to be done, if anything]
```
</output>

<verification>

Before declaring success, verify:

1. **All services healthy**: No services in "Restarting" state for 2+ minutes
2. **Volume mount working**: Can list files from `/data/local-files` inside container
3. **Frontend accessible**: Can load http://localhost:3000 without errors
4. **Verification checkbox visible**: Can see checkbox in chat UI
5. **No critical errors in logs**: Check last 50 lines of pipeshub-ai logs

If any verification fails:
- Document the failure in VERIFICATION-REPORT.md
- Investigate logs for root cause
- Provide troubleshooting steps
</verification>

<success_criteria>

Deployment is successful when ALL of the following are true:

- ✅ All configuration parameters verified against CLAUDE.md
- ✅ All Docker services Up and healthy (no Restarting status)
- ✅ Volume mount `/data/local-files` accessible inside container
- ✅ Frontend loads at http://localhost:3000
- ✅ Verification checkbox visible in chat UI
- ✅ No critical errors in service logs
- ✅ VERIFICATION-REPORT.md created with complete status
- ✅ If any issues exist, they are documented with troubleshooting steps

The system is ready for use when you can log in and see the verification checkbox in the chat interface.
</success_criteria>

<troubleshooting>

## Common Issues

**Services keep restarting**:
- Check logs: `docker compose logs [service-name] --tail=100`
- Common causes: Port conflicts, memory limits, missing environment variables

**Volume mount not accessible**:
- Verify Docker has access to host directory
- Check docker-compose.dev.yml syntax for volume mount
- Restart Docker Desktop if on macOS

**Frontend not loading**:
- Check frontend build logs in pipeshub-ai service
- Verify port 3000 not in use by another process
- Check CORS/ALLOWED_ORIGINS configuration

**Verification checkbox not visible**:
- Verify you're on the develop branch with latest code
- Check browser console for JavaScript errors
- Confirm deployment used latest built image
</troubleshooting>
