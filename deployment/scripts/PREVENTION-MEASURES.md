# Org Mismatch Prevention Measures Documentation

## Overview

This document describes the prevention measures implemented to ensure the org mismatch issue never happens again. These measures protect against the scenario where MongoDB is cleared while ArangoDB retains data, causing orphaned records that users cannot access.

**Root Cause**: The org creation logic only checked MongoDB (`Org.countDocuments()`) before allowing new org creation. When MongoDB was cleared but ArangoDB wasn't, a new org was created while 1,884 records remained orphaned in ArangoDB.

**Solution**: Four-layer defense strategy with cross-database validation, safe reset procedures, runtime protection, and continuous monitoring.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   Prevention Measures                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Layer 1: Org Creation Validation (IMMEDIATE PREVENTION)    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  OrgController.createOrg()                          │   │
│  │  ✓ Check MongoDB org count                          │   │
│  │  ✓ Check ArangoDB record count                      │   │
│  │  ✓ Check ArangoDB org IDs                           │   │
│  │  ✗ Block if inconsistency detected                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Layer 2: Safe Database Reset (OPERATIONAL SAFETY)          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  safe-database-reset.sh                             │   │
│  │  ✓ Detect orphaned data before reset                │   │
│  │  ✓ Warn user about data loss                        │   │
│  │  ✓ Create backups automatically                     │   │
│  │  ✓ Provide options: clear all / cancel              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Layer 3: Runtime Protection (ONGOING VALIDATION)           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  OrgValidationMiddleware                            │   │
│  │  ✓ Validate org exists before ArangoDB writes       │   │
│  │  ✓ Prevent orphaned records during operations       │   │
│  │  ✗ Block if org doesn't exist in MongoDB            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Layer 4: Consistency Monitoring (EARLY DETECTION)          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ConsistencyMonitorService (runs every 6 hours)     │   │
│  │  ✓ Check orphaned ArangoDB data                     │   │
│  │  ✓ Validate connector configs                       │   │
│  │  ✓ Verify cross-database consistency                │   │
│  │  ⚠ Alert admins if issues found                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. Cross-Database Org Validation (HIGH PRIORITY)

**File**: `backend/nodejs/apps/src/modules/user_management/controller/org.controller.ts`

**Purpose**: Prevent org creation when ArangoDB has orphaned data.

**Implementation**:
```typescript
// New method added to OrgController
private async performCrossDatabaseOrgCheck(): Promise<OrgExistenceCheck> {
  // Check MongoDB for existing organizations
  const mongoCount = await Org.countDocuments();

  // Check ArangoDB for existing data
  const arangoRecordCount = await this.checkArangoDBRecordCount();
  const arangoOrgCount = await this.checkArangoDBOrgCount();

  // CRITICAL: Detect database inconsistency
  if (mongoCount === 0 && arangoRecordCount > 0) {
    throw new InternalServerError(
      'Database inconsistency detected: ArangoDB contains records but MongoDB has no organization.'
    );
  }

  return { mongoCount, arangoCount: arangoOrgCount, exists: mongoCount > 0 || arangoOrgCount > 0 };
}
```

**When It Runs**: Every time `POST /api/org` endpoint is called to create a new organization.

**Fail-Safe Behavior**: If ArangoDB is unavailable, returns 0 (doesn't block org creation). Logs warning for investigation.

**Testing**:
```bash
npm test -- org.controller.spec.ts
```

### 2. Safe Database Reset Script (HIGH PRIORITY)

**File**: `deployment/scripts/safe-database-reset.sh`

**Purpose**: Safely reset all databases with orphan detection and backup.

**Features**:
- Detects orphaned data before any destructive operation
- Creates automatic backups of MongoDB and ArangoDB
- Provides user with clear options:
  - Option 1: Clear ALL databases (with backup)
  - Option 2: Cancel and investigate
  - Option 3: Exit without changes
- Logs all operations with timestamps
- Requires explicit "YES" confirmation

**Usage**:
```bash
cd deployment/scripts
./safe-database-reset.sh
```

**Example Output**:
```
==========================================
  Safe Database Reset Tool
  Hupyy KB - Version 1.0
==========================================

[INFO] Checking MongoDB for existing data...
[INFO] MongoDB organizations: 0
[INFO] ArangoDB records: 1884
[WARNING] ORPHANED DATA DETECTED!
[WARNING] MongoDB has no organizations but ArangoDB has 1884 records

Please choose an option:
  1) Clear ALL databases (MongoDB, ArangoDB, etcd)
  2) Cancel and investigate
  3) Exit without changes

Enter choice (1-3):
```

**Backup Location**: `/tmp/hupyy-kb-backups/reset-YYYYMMDD-HHMMSS/`

### 3. Org Validation Middleware (MEDIUM PRIORITY)

**File**: `backend/nodejs/apps/src/libs/middlewares/org-validation.middleware.ts`

**Purpose**: Runtime protection - validate org exists before writing to ArangoDB.

**Implementation**:
```typescript
@injectable()
export class OrgValidationMiddleware {
  async validate(req: AuthenticatedUserRequest, res: Response, next: NextFunction): Promise<void> {
    const orgId = req.user?.orgId;
    const org = await Org.findOne({ _id: orgId, isDeleted: false });

    if (!org) {
      throw new InternalServerError('Organization validation failed');
    }

    next();
  }
}
```

**Usage** (apply to routes that write to ArangoDB):
```typescript
import { OrgValidationMiddleware } from '../middlewares/org-validation.middleware';

router.post(
  '/records',
  authMiddleware.authenticate,
  orgValidationMiddleware.validate,  // Add this middleware
  recordController.createRecord
);
```

**When to Use**:
- Apply to any route that creates/updates records in ArangoDB
- Apply to connector sync operations
- Apply to bulk data import operations

**Performance**: Single MongoDB query per request. Cached results recommended for high-traffic routes.

### 4. Consistency Monitoring Service (MEDIUM PRIORITY)

**File**: `backend/nodejs/apps/src/services/consistency-monitor.service.ts`

**Purpose**: Continuous monitoring to detect inconsistencies early.

**Checks Performed**:

1. **Orphaned ArangoDB Data** (Critical)
   - Finds org IDs in ArangoDB not present in MongoDB
   - Reports total orphaned records
   - Severity: Critical

2. **Invalid Connector Configs** (High)
   - Finds connector configs pointing to non-existent orgs
   - Reports affected connectors
   - Severity: High

3. **Orphaned Connector Configs** (Medium)
   - Finds orgs with records but no connector config
   - May indicate misconfiguration
   - Severity: Medium

4. **MongoDB Org Integrity** (Low)
   - Validates org setup is complete
   - Checks for missing data
   - Severity: Low

**Usage**:
```typescript
const monitor = new ConsistencyMonitorService(arangoService, logger);
const report = await monitor.checkConsistency();

if (report.hasErrors()) {
  logger.error('Consistency issues found:', report.toJSON());
  await alertAdmins(report);
}
```

**Scheduling** (recommended):
```typescript
import cron from 'node-cron';

// Run every 6 hours
cron.schedule('0 */6 * * *', async () => {
  const report = await consistencyMonitor.checkConsistency();
  if (report.hasErrors()) {
    await notificationService.alertAdmins({
      subject: 'Database Consistency Issues Detected',
      body: report.toString(),
      severity: report.getCriticalErrors().length > 0 ? 'critical' : 'warning'
    });
  }
});
```

**Manual Check**:
```bash
npm run check:db-consistency
```

**Report Format**:
```json
{
  "checkedAt": "2025-12-04T10:30:00Z",
  "errorCount": 2,
  "criticalCount": 1,
  "errors": [
    {
      "type": "orphaned_arango_data",
      "severity": "critical",
      "message": "Found 1 org ID(s) in ArangoDB not in MongoDB, affecting 1884 records",
      "details": {
        "orphanedOrgIds": ["6929b83ca78b2651fdf1b04a"],
        "orphanedDetails": [
          { "orgId": "6929b83ca78b2651fdf1b04a", "recordCount": 1884 }
        ],
        "totalOrphanedRecords": 1884
      },
      "detectedAt": "2025-12-04T10:30:05Z"
    }
  ]
}
```

## Testing

### Unit Tests

**File**: `backend/nodejs/apps/tests/modules/user_management/org.controller.spec.ts`

**Coverage**:
- Cross-database validation logic
- Fail-safe behavior when ArangoDB unavailable
- Edge cases (null values, empty results)
- Error message validation

**Run**:
```bash
npm test -- org.controller.spec.ts
```

**Expected Results**: All tests pass, 100% coverage of new validation methods.

### Integration Tests

**File**: `backend/nodejs/apps/tests/integration/org-consistency.spec.ts`

**Scenarios Tested**:
1. MongoDB cleared, ArangoDB has data → Detected
2. Both databases empty → Pass
3. Both databases consistent → Pass
4. Multiple orgs with mixed consistency → Detect only orphaned
5. Performance with 1000+ records → Complete in < 5 seconds

**Prerequisites**:
- Test MongoDB instance
- Test ArangoDB instance
- Test environment configured

**Run**:
```bash
NODE_ENV=test npm test -- org-consistency.spec.ts
```

## Deployment

### Fresh Deployment

1. Deploy code with all prevention measures
2. Start all services via docker-compose
3. Run consistency check:
   ```bash
   npm run check:db-consistency
   ```
4. If clean, proceed with org creation via UI
5. If issues found, investigate before proceeding

### Existing Deployment

1. **Before deploying prevention measures**:
   ```bash
   # Check current state
   npm run check:db-consistency

   # If inconsistencies found, fix them first
   # See: .prompts/005-org-mismatch-investigation-plan/org-mismatch-investigation-plan.md
   ```

2. **Deploy prevention measures**:
   ```bash
   git pull origin develop
   npm install
   npm run build
   docker-compose restart
   ```

3. **Verify prevention measures active**:
   ```bash
   # Check logs for consistency monitoring
   docker-compose logs -f apps | grep "consistency check"

   # Test cross-database validation (should fail if ArangoDB has orphaned data)
   curl -X POST http://localhost:8000/api/org \
     -H "Content-Type: application/json" \
     -d '{"contactEmail":"test@example.com","password":"Test123!","accountType":"business"}'
   ```

### Database Reset Procedure

**NEVER manually clear databases in production.**

**Development/Testing**:
```bash
# Use safe reset script
cd deployment/scripts
./safe-database-reset.sh
```

**Production** (if absolutely necessary):
1. Schedule maintenance window
2. Create full backups
3. Stop all services
4. Run safe-database-reset.sh
5. Verify databases empty
6. Restart services
7. Create new org through UI
8. Verify org creation and data access

## Monitoring

### Metrics to Track

1. **Org Count Consistency** (Critical)
   - MongoDB org count vs ArangoDB distinct org IDs
   - Alert: If ArangoDB has more org IDs than MongoDB
   - Frequency: Every 6 hours

2. **Orphaned Records** (Critical)
   - Records in ArangoDB with org IDs not in MongoDB
   - Alert: If count > 0
   - Frequency: Every 6 hours

3. **Failed Org Creation Attempts** (High)
   - Attempts to create org when inconsistency detected
   - Alert: If rate > 0 per hour
   - Indicates someone trying to create org with orphaned data present

4. **Connector Config Validity** (Medium)
   - Connector configs pointing to deleted/non-existent orgs
   - Alert: If any found
   - Frequency: Daily

### Alert Configuration

**Critical Alerts** (immediate notification):
- Orphaned data detected
- Org creation blocked due to inconsistency
- Cross-database validation failures

**Warning Alerts** (notification within 1 hour):
- Invalid connector configs
- ArangoDB connection failures during validation
- Consistency check errors

**Info Alerts** (daily digest):
- Consistency check completed successfully
- Database reset operations performed
- Org validation middleware activations

## Troubleshooting

### Issue: Org creation fails with "Database inconsistency detected"

**Cause**: ArangoDB has records but MongoDB has no org (orphaned data).

**Resolution**:
1. Run consistency check:
   ```bash
   npm run check:db-consistency
   ```

2. Choose resolution strategy:
   - **Option A**: Migrate orphaned data to new org (recommended)
     - See: `.prompts/005-org-mismatch-investigation-plan/org-mismatch-investigation-plan.md`
   - **Option B**: Clear all databases and start fresh
     - Run: `./deployment/scripts/safe-database-reset.sh`

### Issue: Consistency monitoring reports orphaned data

**Cause**: Data exists in ArangoDB for orgs that don't exist in MongoDB.

**Resolution**:
1. Investigate which org IDs are orphaned:
   ```bash
   # Check report details
   npm run check:db-consistency | jq '.errors[] | select(.type=="orphaned_arango_data")'
   ```

2. Determine if data is valuable:
   - If yes: Migrate to current org (see investigation plan)
   - If no: Clear ArangoDB and recreate indexes

### Issue: ArangoDB validation fails during org creation

**Cause**: ArangoDB is unavailable or connection error.

**Resolution**:
1. Check ArangoDB service:
   ```bash
   docker-compose ps arangodb
   docker-compose logs arangodb
   ```

2. Verify network connectivity:
   ```bash
   curl http://localhost:8529/_api/version
   ```

3. If ArangoDB is down, org creation will proceed (fail-safe) but log warning
4. Check logs after service restored to verify validation resumed

### Issue: Connector creates records but middleware blocks them

**Cause**: Org validation middleware rejecting writes for non-existent org.

**Resolution**:
1. Verify org exists:
   ```bash
   docker exec -it hupyy-kb-mongodb-1 mongosh es --eval 'db.org.find()'
   ```

2. If org missing, this is the correct behavior (prevention measure working)
3. Create org first, then retry connector sync

## Best Practices

### Development

1. **Always use safe-database-reset.sh** instead of manual database clearing
2. **Run consistency checks** before and after major database operations
3. **Test with orphaned data scenarios** to verify prevention measures
4. **Monitor logs** for validation warnings during development

### Production

1. **Never clear databases manually** - always use documented procedures
2. **Schedule consistency checks** to run every 6 hours
3. **Set up alerts** for critical consistency errors
4. **Keep backups** for minimum 30 days
5. **Document any database operations** in change logs
6. **Verify org existence** before bulk data imports

### Operations

1. **Regular Consistency Audits**: Run manual checks weekly
2. **Review Monitoring Reports**: Check consistency reports daily
3. **Backup Verification**: Test restore procedures monthly
4. **Incident Response**: Document any consistency issues for root cause analysis

## Success Criteria

All prevention measures are considered successful when:

- ✅ Cross-database org validation blocks creation when ArangoDB has orphaned data
- ✅ Safe database reset script warns before destructive operations
- ✅ Org validation middleware prevents writing to non-existent orgs
- ✅ Consistency monitoring detects issues within 6 hours
- ✅ All unit tests pass with 100% coverage
- ✅ All integration tests pass
- ✅ Zero occurrences of org mismatch issue in production

## Related Documents

- **Root Cause Analysis**: `.prompts/005-org-mismatch-investigation-plan/org-mismatch-investigation-plan.md`
- **Migration Plan**: Same document, Section 2
- **Backup Procedures**: `deployment/scripts/README.md`
- **Restore Procedures**: `deployment/scripts/restore-all-databases.sh`

## Version History

- **v1.0.0** (2025-12-04): Initial implementation
  - Cross-database org validation
  - Safe database reset script
  - Org validation middleware
  - Consistency monitoring service
  - Comprehensive test suite

---

**Document Status**: Complete
**Last Updated**: 2025-12-04
**Author**: Claude (Sonnet 4.5)
**Reviewer**: Pending
**Approved**: Pending
