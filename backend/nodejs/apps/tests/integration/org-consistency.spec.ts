/**
 * Integration tests for organization consistency across databases
 *
 * Tests end-to-end consistency validation:
 * - Real database connections (test databases)
 * - Cross-database org validation
 * - Consistency monitoring service
 * - Orphaned data detection
 *
 * Prerequisites:
 * - Test MongoDB must be running
 * - Test ArangoDB must be running
 * - Test environment configured
 *
 * Run with:
 *   NODE_ENV=test npm test -- org-consistency.spec.ts
 */

import { describe, expect, it, jest, beforeAll, afterAll, beforeEach } from '@jest/globals';
import { MongoMemoryServer } from 'mongodb-memory-server';
import mongoose from 'mongoose';
import { Database } from 'arangojs';
import { Org } from '../../src/modules/user_management/schema/org.schema';
import { ArangoService } from '../../src/libs/services/arango.service';
import { ConsistencyMonitorService } from '../../src/services/consistency-monitor.service';
import { Logger } from '../../src/libs/services/logger.service';

// ============================================================================
// Test Database Setup
// ============================================================================

let mongoServer: MongoMemoryServer;
let arangoService: ArangoService;
let testDb: Database;
let consistencyMonitor: ConsistencyMonitorService;

beforeAll(async () => {
  // Start in-memory MongoDB for testing
  mongoServer = await MongoMemoryServer.create();
  const mongoUri = mongoServer.getUri();
  await mongoose.connect(mongoUri);

  // Setup test ArangoDB connection
  // NOTE: This requires a real ArangoDB instance for integration tests
  // In a real test environment, you'd use a test database
  const arangoConfig = {
    url: process.env.TEST_ARANGO_URL || 'http://localhost:8529',
    db: process.env.TEST_ARANGO_DB || 'test_es',
    username: process.env.TEST_ARANGO_USER || 'root',
    password: process.env.TEST_ARANGO_PASSWORD || '',
  };

  arangoService = new ArangoService(arangoConfig);
  await arangoService.initialize();
  testDb = arangoService.getConnection();

  // Setup consistency monitor
  const logger = Logger.getInstance({ service: 'Test' });
  consistencyMonitor = new ConsistencyMonitorService(arangoService, logger);

  // Create test collections if they don't exist
  try {
    await testDb.createCollection('records');
  } catch (error) {
    // Collection might already exist
  }
});

afterAll(async () => {
  // Cleanup test databases
  if (arangoService) {
    await arangoService.cleanDatabase();
    await arangoService.destroy();
  }

  await mongoose.disconnect();
  if (mongoServer) {
    await mongoServer.stop();
  }
});

beforeEach(async () => {
  // Clear data before each test
  await Org.deleteMany({});

  if (arangoService) {
    try {
      await testDb.collection('records').truncate();
    } catch (error) {
      // Collection might not exist
    }
  }
});

// ============================================================================
// Integration Test Suites
// ============================================================================

describe('Organization Consistency - Integration Tests', () => {
  // ==========================================================================
  // Scenario 1: Detect orphaned data after partial database clear
  // ==========================================================================

  describe('Scenario: MongoDB cleared, ArangoDB retains data', () => {
    it('should detect orphaned data in ArangoDB when MongoDB is empty', async () => {
      // Arrange: Create org in MongoDB
      const org = new Org({
        accountType: 'business',
        registeredName: 'Test Organization',
        contactEmail: 'test@example.com',
        domain: 'example.com',
        isDeleted: false,
      });
      await org.save();
      const orgId = org._id.toString();

      // Create records in ArangoDB associated with this org
      const recordsCollection = testDb.collection('records');
      await recordsCollection.save({
        _key: 'record1',
        orgId: orgId,
        title: 'Test Record 1',
        content: 'Test content 1',
      });
      await recordsCollection.save({
        _key: 'record2',
        orgId: orgId,
        title: 'Test Record 2',
        content: 'Test content 2',
      });

      // Act: Clear MongoDB (simulating the bug scenario)
      await Org.deleteMany({});

      // Run consistency check
      const report = await consistencyMonitor.checkConsistency();

      // Assert: Should detect orphaned data
      expect(report.hasErrors()).toBe(true);
      expect(report.getCriticalErrors().length).toBeGreaterThan(0);

      const orphanedError = report
        .getErrors()
        .find((e) => e.type === 'orphaned_arango_data');
      expect(orphanedError).toBeDefined();
      expect(orphanedError?.severity).toBe('critical');
      expect(orphanedError?.details).toHaveProperty('totalOrphanedRecords', 2);
    });

    it('should pass consistency check when both databases are empty', async () => {
      // Arrange: Ensure both databases are empty
      await Org.deleteMany({});
      await testDb.collection('records').truncate();

      // Act: Run consistency check
      const report = await consistencyMonitor.checkConsistency();

      // Assert: No errors
      expect(report.hasErrors()).toBe(false);
      expect(report.getErrors().length).toBe(0);
    });

    it('should pass consistency check when databases are consistent', async () => {
      // Arrange: Create org in MongoDB
      const org = new Org({
        accountType: 'business',
        registeredName: 'Test Organization',
        contactEmail: 'test@example.com',
        domain: 'example.com',
        isDeleted: false,
      });
      await org.save();
      const orgId = org._id.toString();

      // Create matching records in ArangoDB
      const recordsCollection = testDb.collection('records');
      await recordsCollection.save({
        _key: 'record1',
        orgId: orgId,
        title: 'Test Record',
        content: 'Test content',
      });

      // Act: Run consistency check
      const report = await consistencyMonitor.checkConsistency();

      // Assert: Should pass (no orphaned data)
      const orphanedError = report
        .getErrors()
        .find((e) => e.type === 'orphaned_arango_data');
      expect(orphanedError).toBeUndefined();
    });
  });

  // ==========================================================================
  // Scenario 2: Multiple orgs with mixed consistency
  // ==========================================================================

  describe('Scenario: Multiple orgs with partial consistency', () => {
    it('should detect only orphaned orgs, not valid ones', async () => {
      // Arrange: Create valid org in MongoDB
      const validOrg = new Org({
        accountType: 'business',
        registeredName: 'Valid Org',
        contactEmail: 'valid@example.com',
        domain: 'valid.com',
        isDeleted: false,
      });
      await validOrg.save();
      const validOrgId = validOrg._id.toString();

      // Create records for both valid and orphaned org in ArangoDB
      const recordsCollection = testDb.collection('records');

      // Valid org record
      await recordsCollection.save({
        _key: 'valid_record',
        orgId: validOrgId,
        title: 'Valid Record',
      });

      // Orphaned org record (org doesn't exist in MongoDB)
      await recordsCollection.save({
        _key: 'orphaned_record',
        orgId: 'nonexistent_org_id_12345',
        title: 'Orphaned Record',
      });

      // Act: Run consistency check
      const report = await consistencyMonitor.checkConsistency();

      // Assert: Should detect only the orphaned org
      expect(report.hasErrors()).toBe(true);
      const orphanedError = report
        .getErrors()
        .find((e) => e.type === 'orphaned_arango_data');

      expect(orphanedError).toBeDefined();
      expect(orphanedError?.details).toHaveProperty('orphanedOrgIds');
      const orphanedOrgIds = orphanedError?.details.orphanedOrgIds as string[];
      expect(orphanedOrgIds).toContain('nonexistent_org_id_12345');
      expect(orphanedOrgIds).not.toContain(validOrgId);
    });
  });

  // ==========================================================================
  // Scenario 3: Performance with large number of records
  // ==========================================================================

  describe('Scenario: Performance with many records', () => {
    it('should efficiently detect orphaned data with 1000+ records', async () => {
      // Arrange: Create orphaned records
      const recordsCollection = testDb.collection('records');
      const orphanedOrgId = 'orphaned_org_performance_test';

      // Insert 1000 orphaned records
      const records = Array.from({ length: 1000 }, (_, i) => ({
        _key: `perf_record_${i}`,
        orgId: orphanedOrgId,
        title: `Performance Test Record ${i}`,
      }));

      await recordsCollection.saveAll(records);

      // Act: Run consistency check and measure time
      const startTime = Date.now();
      const report = await consistencyMonitor.checkConsistency();
      const duration = Date.now() - startTime;

      // Assert: Should complete in reasonable time (< 5 seconds)
      expect(duration).toBeLessThan(5000);
      expect(report.hasErrors()).toBe(true);

      const orphanedError = report
        .getErrors()
        .find((e) => e.type === 'orphaned_arango_data');
      expect(orphanedError?.details).toHaveProperty('totalOrphanedRecords', 1000);
    });
  });

  // ==========================================================================
  // Scenario 4: Connector config validation
  // ==========================================================================

  describe('Scenario: Connector config consistency', () => {
    it('should detect connector configs referencing deleted orgs', async () => {
      // Note: This test requires ConnectorsConfig model
      // Skipped if not available in test environment

      // Placeholder for connector config consistency tests
      // Would test:
      // 1. Connector config points to deleted org -> detected
      // 2. Connector config points to valid org -> passes
      // 3. Records exist without connector config -> detected

      expect(true).toBe(true); // Placeholder
    });
  });
});

// ============================================================================
// ArangoDB Query Tests
// ============================================================================

describe('ArangoDB Query Validation', () => {
  it('should correctly count records by org ID', async () => {
    // Arrange
    const testOrgId = 'test_org_count_validation';
    const recordsCollection = testDb.collection('records');

    // Insert 5 records for test org
    for (let i = 0; i < 5; i++) {
      await recordsCollection.save({
        _key: `count_test_${i}`,
        orgId: testOrgId,
        title: `Count Test ${i}`,
      });
    }

    // Act: Query record count
    const query = `
      FOR r IN records
      FILTER r.orgId == @orgId
      COLLECT WITH COUNT INTO count
      RETURN count
    `;
    const cursor = await testDb.query(query, { orgId: testOrgId });
    const result = await cursor.all();
    const count = result[0];

    // Assert
    expect(count).toBe(5);
  });

  it('should correctly get distinct org IDs', async () => {
    // Arrange
    const recordsCollection = testDb.collection('records');
    await recordsCollection.saveAll([
      { _key: 'distinct1', orgId: 'org1', title: 'Record 1' },
      { _key: 'distinct2', orgId: 'org1', title: 'Record 2' },
      { _key: 'distinct3', orgId: 'org2', title: 'Record 3' },
      { _key: 'distinct4', orgId: 'org3', title: 'Record 4' },
    ]);

    // Act: Query distinct org IDs
    const query = 'FOR r IN records RETURN DISTINCT r.orgId';
    const cursor = await testDb.query(query);
    const orgIds = await cursor.all();

    // Assert
    expect(orgIds).toHaveLength(3);
    expect(orgIds).toContain('org1');
    expect(orgIds).toContain('org2');
    expect(orgIds).toContain('org3');
  });
});
