/**
 * Unit tests for OrgController cross-database validation
 *
 * Tests the prevention measures for org mismatch issue:
 * - Cross-database org validation
 * - ArangoDB orphaned data detection
 * - Fail-safe behavior when databases unavailable
 *
 * Run with:
 *   npm test -- org.controller.spec.ts
 */

import { describe, expect, it, jest, beforeEach, afterEach } from '@jest/globals';
import type { Response } from 'express';
import { OrgController } from '../../../src/modules/user_management/controller/org.controller';
import { Org } from '../../../src/modules/user_management/schema/org.schema';
import { ArangoService } from '../../../src/libs/services/arango.service';
import { Logger } from '../../../src/libs/services/logger.service';
import { MailService } from '../../../src/modules/user_management/services/mail.service';
import { EntitiesEventProducer } from '../../../src/modules/user_management/services/entity_events.service';
import {
  BadRequestError,
  InternalServerError,
} from '../../../src/libs/errors/http.errors';
import type { ContainerRequest } from '../../../src/modules/auth/middlewares/types';

// ============================================================================
// Mock Setup
// ============================================================================

// Mock all dependencies
jest.mock('../../../src/modules/user_management/schema/org.schema');
jest.mock('../../../src/libs/services/arango.service');
jest.mock('../../../src/libs/services/logger.service');
jest.mock('../../../src/modules/user_management/services/mail.service');
jest.mock('../../../src/modules/user_management/services/entity_events.service');

const mockRequest = (data: any = {}): Partial<ContainerRequest> => ({
  body: data.body || {},
  params: data.params || {},
  query: data.query || {},
  headers: data.headers || {},
  user: data.user,
  container: data.container,
  ip: data.ip || '127.0.0.1',
});

const mockResponse = (): Partial<Response> => {
  const res: any = {};
  res.status = jest.fn().mockReturnValue(res);
  res.json = jest.fn().mockReturnValue(res);
  res.send = jest.fn().mockReturnValue(res);
  return res;
};

const mockArangoQuery = (results: any[]) => {
  return {
    all: jest.fn().mockResolvedValue(results),
  };
};

// ============================================================================
// Test Suite
// ============================================================================

describe('OrgController - Cross-Database Validation', () => {
  let orgController: OrgController;
  let mockArangoService: jest.Mocked<ArangoService>;
  let mockLogger: jest.Mocked<Logger>;
  let mockMailService: jest.Mocked<MailService>;
  let mockEventService: jest.Mocked<EntitiesEventProducer>;
  let mockArangoDb: any;

  beforeEach(() => {
    jest.clearAllMocks();

    // Setup mocks
    mockLogger = {
      info: jest.fn(),
      warn: jest.fn(),
      error: jest.fn(),
      debug: jest.fn(),
    } as any;

    mockMailService = {
      sendMail: jest.fn(),
    } as any;

    mockEventService = {
      start: jest.fn(),
      publishEvent: jest.fn(),
      stop: jest.fn(),
    } as any;

    mockArangoDb = {
      query: jest.fn(),
    };

    mockArangoService = {
      getConnection: jest.fn().mockReturnValue(mockArangoDb),
    } as any;

    // Create controller instance
    const mockConfig = {
      rsAvailable: 'false',
      frontendUrl: 'http://localhost:3000',
      scopedJwtSecret: 'test-secret',
    } as any;

    orgController = new OrgController(
      mockConfig,
      mockMailService,
      mockLogger,
      mockEventService,
      mockArangoService,
    );
  });

  // ==========================================================================
  // Test 1: Reject org creation when ArangoDB has orphaned records
  // ==========================================================================

  describe('Prevention Measure #1: Cross-Database Validation', () => {
    it('should reject org creation when MongoDB empty but ArangoDB has orphaned records', async () => {
      // Arrange
      const req = mockRequest({
        body: {
          contactEmail: 'admin@example.com',
          adminFullName: 'Admin User',
          password: 'SecurePass123!',
          accountType: 'business',
          registeredName: 'Test Org',
        },
      }) as ContainerRequest;

      const res = mockResponse() as Response;

      // Mock MongoDB: No orgs exist (count = 0)
      (Org.countDocuments as jest.Mock) = jest.fn().mockResolvedValue(0);

      // Mock ArangoDB: Has 1884 orphaned records
      mockArangoDb.query
        .mockResolvedValueOnce(mockArangoQuery([1884])) // Record count query
        .mockResolvedValueOnce(mockArangoQuery(['6929b83ca78b2651fdf1b04a'])); // Org IDs query

      // Act & Assert
      await expect(orgController.createOrg(req, res)).rejects.toThrow(
        InternalServerError,
      );

      await expect(orgController.createOrg(req, res)).rejects.toThrow(
        /Database inconsistency detected/,
      );

      // Verify error was logged
      expect(mockLogger.error).toHaveBeenCalledWith(
        expect.stringContaining('DATABASE INCONSISTENCY DETECTED'),
      );
    });

    it('should allow org creation when both databases are empty', async () => {
      // Arrange
      const req = mockRequest({
        body: {
          contactEmail: 'admin@example.com',
          adminFullName: 'Admin User',
          password: 'SecurePass123!',
          accountType: 'business',
          registeredName: 'Test Org',
        },
        container: {
          get: jest.fn().mockReturnValue({
            recordActivity: jest.fn(),
          }),
        },
      }) as ContainerRequest;

      const res = mockResponse() as Response;

      // Mock MongoDB: No orgs exist
      (Org.countDocuments as jest.Mock) = jest.fn().mockResolvedValue(0);

      // Mock ArangoDB: No records exist
      mockArangoDb.query
        .mockResolvedValueOnce(mockArangoQuery([0])) // Record count query
        .mockResolvedValueOnce(mockArangoQuery([])); // Org IDs query

      // Mock Mongoose models
      const mockOrgSave = jest.fn().mockResolvedValue({});
      const mockUserSave = jest.fn().mockResolvedValue({});

      jest.spyOn(Org.prototype, 'save').mockImplementation(mockOrgSave);

      // Note: Full org creation test would require mocking all models
      // This test focuses on the cross-database check passing

      // Act
      try {
        await orgController.createOrg(req, res);
      } catch (error) {
        // Expected to fail on other validations/saves, but should pass cross-db check
        // The important thing is it doesn't throw "Database inconsistency" error
        if (error instanceof InternalServerError) {
          expect((error as Error).message).not.toContain(
            'Database inconsistency',
          );
        }
      }

      // Verify no inconsistency error was logged
      expect(mockLogger.error).not.toHaveBeenCalledWith(
        expect.stringContaining('DATABASE INCONSISTENCY DETECTED'),
      );
    });

    it('should reject org creation when MongoDB already has an org', async () => {
      // Arrange
      const req = mockRequest({
        body: {
          contactEmail: 'admin@example.com',
          adminFullName: 'Admin User',
          password: 'SecurePass123!',
          accountType: 'business',
          registeredName: 'Test Org',
        },
      }) as ContainerRequest;

      const res = mockResponse() as Response;

      // Mock MongoDB: Already has org
      (Org.countDocuments as jest.Mock) = jest.fn().mockResolvedValue(1);

      // Mock ArangoDB: Has matching records
      mockArangoDb.query
        .mockResolvedValueOnce(mockArangoQuery([100]))
        .mockResolvedValueOnce(mockArangoQuery(['existing-org-id']));

      // Act & Assert
      await expect(orgController.createOrg(req, res)).rejects.toThrow(
        BadRequestError,
      );

      await expect(orgController.createOrg(req, res)).rejects.toThrow(
        /already an organization/,
      );
    });
  });

  // ==========================================================================
  // Test 2: Fail-safe behavior when ArangoDB unavailable
  // ==========================================================================

  describe('Fail-safe Behavior', () => {
    it('should not block org creation if ArangoDB is unavailable', async () => {
      // Arrange
      const req = mockRequest({
        body: {
          contactEmail: 'admin@example.com',
          adminFullName: 'Admin User',
          password: 'SecurePass123!',
          accountType: 'business',
          registeredName: 'Test Org',
        },
        container: {
          get: jest.fn().mockReturnValue({
            recordActivity: jest.fn(),
          }),
        },
      }) as ContainerRequest;

      const res = mockResponse() as Response;

      // Mock MongoDB: No orgs exist
      (Org.countDocuments as jest.Mock) = jest.fn().mockResolvedValue(0);

      // Mock ArangoDB: Connection fails
      mockArangoDb.query.mockRejectedValue(
        new Error('ArangoDB connection failed'),
      );

      // Act
      try {
        await orgController.createOrg(req, res);
      } catch (error) {
        // Should fail on other reasons, not cross-database check
        if (error instanceof InternalServerError) {
          expect((error as Error).message).not.toContain(
            'Database inconsistency',
          );
        }
      }

      // Verify warning was logged but operation wasn't blocked
      expect(mockLogger.warn).toHaveBeenCalledWith(
        expect.stringContaining('Could not check ArangoDB'),
        expect.anything(),
      );
    });

    it('should log error details when ArangoDB check fails', async () => {
      // Arrange
      const req = mockRequest({
        body: {
          contactEmail: 'admin@example.com',
          adminFullName: 'Admin User',
          password: 'SecurePass123!',
          accountType: 'business',
          registeredName: 'Test Org',
        },
        container: {
          get: jest.fn(),
        },
      }) as ContainerRequest;

      const res = mockResponse() as Response;

      // Mock MongoDB: No orgs
      (Org.countDocuments as jest.Mock) = jest.fn().mockResolvedValue(0);

      // Mock ArangoDB: Throws specific error
      const arangoError = new Error('Connection timeout');
      mockArangoDb.query.mockRejectedValue(arangoError);

      // Act
      try {
        await orgController.createOrg(req, res);
      } catch (error) {
        // Expected
      }

      // Verify error details were logged
      expect(mockLogger.warn).toHaveBeenCalledWith(
        expect.stringContaining('Could not check ArangoDB'),
        arangoError,
      );
    });
  });

  // ==========================================================================
  // Test 3: Edge cases
  // ==========================================================================

  describe('Edge Cases', () => {
    it('should handle ArangoDB returning null or undefined gracefully', async () => {
      // Arrange
      const req = mockRequest({
        body: {
          contactEmail: 'admin@example.com',
          adminFullName: 'Admin User',
          password: 'SecurePass123!',
          accountType: 'business',
          registeredName: 'Test Org',
        },
        container: {
          get: jest.fn(),
        },
      }) as ContainerRequest;

      const res = mockResponse() as Response;

      // Mock MongoDB: No orgs
      (Org.countDocuments as jest.Mock) = jest.fn().mockResolvedValue(0);

      // Mock ArangoDB: Returns null/undefined
      mockArangoDb.query
        .mockResolvedValueOnce(mockArangoQuery([null])) // Null count
        .mockResolvedValueOnce(mockArangoQuery([])); // Empty org IDs

      // Act
      try {
        await orgController.createOrg(req, res);
      } catch (error) {
        // Should not throw inconsistency error
        if (error instanceof InternalServerError) {
          expect((error as Error).message).not.toContain(
            'Database inconsistency',
          );
        }
      }

      // Should treat null as 0
      expect(mockLogger.error).not.toHaveBeenCalledWith(
        expect.stringContaining('DATABASE INCONSISTENCY'),
      );
    });

    it('should detect inconsistency even with small number of orphaned records', async () => {
      // Arrange
      const req = mockRequest({
        body: {
          contactEmail: 'admin@example.com',
          adminFullName: 'Admin User',
          password: 'SecurePass123!',
          accountType: 'business',
          registeredName: 'Test Org',
        },
      }) as ContainerRequest;

      const res = mockResponse() as Response;

      // Mock MongoDB: Empty
      (Org.countDocuments as jest.Mock) = jest.fn().mockResolvedValue(0);

      // Mock ArangoDB: Just 1 orphaned record should trigger error
      mockArangoDb.query
        .mockResolvedValueOnce(mockArangoQuery([1])) // 1 record
        .mockResolvedValueOnce(mockArangoQuery(['orphan-org-id']));

      // Act & Assert
      await expect(orgController.createOrg(req, res)).rejects.toThrow(
        /Database inconsistency detected/,
      );
    });
  });
});
