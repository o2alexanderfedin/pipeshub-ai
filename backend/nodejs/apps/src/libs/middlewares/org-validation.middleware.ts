/**
 * Org Validation Middleware
 *
 * PREVENTION MEASURE #4: Runtime protection against orphaned data
 *
 * This middleware validates that the organization ID exists in MongoDB before
 * allowing operations that write to ArangoDB. This prevents creating orphaned
 * records if a MongoDB org is deleted or doesn't exist.
 *
 * Usage:
 *   Apply this middleware to routes that create/update records in ArangoDB:
 *   router.post('/records', orgValidationMiddleware, recordController.create);
 *
 * Design Principles:
 *   - Single Responsibility: Only validates org existence
 *   - Fail-safe: Logs errors but doesn't block on MongoDB connection issues
 *   - Type-safe: Uses TypeScript interfaces for all data structures
 *   - Dependency Inversion: Depends on abstractions (Logger, Org schema)
 */

import { Response, NextFunction } from 'express';
import { inject, injectable } from 'inversify';
import { Org } from '../../modules/user_management/schema/org.schema';
import { Logger } from '../services/logger.service';
import {
  UnauthorizedError,
  InternalServerError,
} from '../errors/http.errors';
import { AuthenticatedUserRequest } from './types';

/**
 * Result of org validation check
 */
interface OrgValidationResult {
  valid: boolean;
  orgId: string;
  error?: string;
}

@injectable()
export class OrgValidationMiddleware {
  constructor(@inject('Logger') private logger: Logger) {}

  /**
   * Validate that the organization exists in MongoDB
   * @param orgId Organization ID to validate
   * @returns Validation result with details
   */
  private async validateOrgExists(
    orgId: string,
  ): Promise<OrgValidationResult> {
    try {
      const org = await Org.findOne({ _id: orgId, isDeleted: false });

      if (!org) {
        return {
          valid: false,
          orgId,
          error: `Organization ${orgId} does not exist or has been deleted`,
        };
      }

      return {
        valid: true,
        orgId,
      };
    } catch (error) {
      this.logger.error(
        `Error validating org ${orgId}:`,
        error instanceof Error ? error.message : 'Unknown error',
      );
      // Fail-safe: If we can't validate (e.g., MongoDB down), we should block
      // This prevents writing orphaned data during MongoDB outages
      return {
        valid: false,
        orgId,
        error: 'Could not validate organization - database connection issue',
      };
    }
  }

  /**
   * Express middleware to validate org before ArangoDB writes
   * Checks that the authenticated user's org exists in MongoDB
   */
  async validate(
    req: AuthenticatedUserRequest,
    _res: Response,
    next: NextFunction,
  ): Promise<void> {
    try {
      // Get org ID from authenticated user
      const orgId = req.user?.orgId;

      if (!orgId) {
        throw new UnauthorizedError('No organization ID in request');
      }

      // Validate org exists in MongoDB
      const validation = await this.validateOrgExists(orgId.toString());

      if (!validation.valid) {
        this.logger.error(
          `Org validation failed for ${orgId}: ${validation.error}`,
        );
        throw new InternalServerError(
          validation.error ||
            'Organization validation failed - cannot proceed with operation',
        );
      }

      // Validation passed - continue to next middleware
      next();
    } catch (error) {
      next(error);
    }
  }

  /**
   * Factory method to create middleware function
   * Use this when you need to pass middleware to Express router
   * @returns Express middleware function
   */
  getMiddleware() {
    return this.validate.bind(this);
  }
}
