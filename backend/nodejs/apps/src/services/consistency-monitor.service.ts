/**
 * Database Consistency Monitoring Service
 *
 * PREVENTION MEASURE #3: Consistency monitoring every 6 hours
 *
 * This service monitors cross-database consistency to detect and alert on:
 * 1. Org IDs in ArangoDB that don't exist in MongoDB (orphaned data)
 * 2. Connector configs in MongoDB referencing non-existent orgs
 * 3. Records in ArangoDB without corresponding connector configs
 *
 * Design Principles:
 * - Single Responsibility: Only monitors consistency, doesn't fix issues
 * - Open/Closed: Easy to add new consistency checks
 * - Dependency Inversion: Injected dependencies for database services
 * - Type Safety: Strong typing for all check results
 *
 * Usage:
 *   const monitor = new ConsistencyMonitorService(arangoService, logger);
 *   const report = await monitor.checkConsistency();
 *   if (report.hasErrors()) {
 *     logger.error('Consistency issues found:', report.toJSON());
 *   }
 *
 * Scheduling:
 *   Schedule this service to run every 6 hours via cron:
 *   cron.schedule('0 *\\/6 * * *', async () => {
 *     const report = await monitor.checkConsistency();
 *     if (report.hasErrors()) {
 *       await alertAdmins(report);
 *     }
 *   });
 */

import { inject, injectable } from 'inversify';
import { ArangoService } from '../libs/services/arango.service';
import { Logger } from '../libs/services/logger.service';
import { Org } from '../modules/user_management/schema/org.schema';
import { ConnectorsConfig } from '../modules/configuration_manager/schema/connectors.schema';

/**
 * Types of consistency errors that can be detected
 */
enum ConsistencyErrorType {
  ORPHANED_ARANGO_DATA = 'orphaned_arango_data',
  INVALID_CONNECTOR_ORG = 'invalid_connector_org',
  ORPHANED_CONNECTOR_CONFIG = 'orphaned_connector_config',
  MISSING_ORG_IN_MONGO = 'missing_org_in_mongo',
}

/**
 * Individual consistency error
 */
interface ConsistencyError {
  type: ConsistencyErrorType;
  severity: 'critical' | 'high' | 'medium' | 'low';
  message: string;
  details: Record<string, unknown>;
  detectedAt: Date;
}

/**
 * Consistency check report
 */
class ConsistencyReport {
  private errors: ConsistencyError[] = [];
  private checkedAt: Date;

  constructor() {
    this.checkedAt = new Date();
  }

  addError(
    type: ConsistencyErrorType,
    message: string,
    details: Record<string, unknown>,
    severity: 'critical' | 'high' | 'medium' | 'low' = 'high',
  ): void {
    this.errors.push({
      type,
      severity,
      message,
      details,
      detectedAt: new Date(),
    });
  }

  hasErrors(): boolean {
    return this.errors.length > 0;
  }

  getErrors(): ConsistencyError[] {
    return this.errors;
  }

  getCriticalErrors(): ConsistencyError[] {
    return this.errors.filter((e) => e.severity === 'critical');
  }

  toJSON(): Record<string, unknown> {
    return {
      checkedAt: this.checkedAt,
      errorCount: this.errors.length,
      criticalCount: this.getCriticalErrors().length,
      errors: this.errors,
    };
  }

  toString(): string {
    return JSON.stringify(this.toJSON(), null, 2);
  }
}

@injectable()
export class ConsistencyMonitorService {
  constructor(
    @inject(ArangoService) private arangoService: ArangoService,
    @inject('Logger') private logger: Logger,
  ) {}

  /**
   * Get all unique org IDs from ArangoDB records
   */
  private async getArangoDBOrgIds(): Promise<string[]> {
    try {
      const db = this.arangoService.getConnection();
      const query = 'FOR r IN records RETURN DISTINCT r.orgId';
      const cursor = await db.query(query);
      const result = await cursor.all();
      return result.filter((id): id is string => id != null);
    } catch (error) {
      this.logger.error(
        'Error fetching ArangoDB org IDs:',
        error instanceof Error ? error.message : 'Unknown error',
      );
      return [];
    }
  }

  /**
   * Get record count for a specific org in ArangoDB
   */
  private async getArangoDBRecordCount(orgId: string): Promise<number> {
    try {
      const db = this.arangoService.getConnection();
      const query = `
        FOR r IN records
        FILTER r.orgId == @orgId
        COLLECT WITH COUNT INTO count
        RETURN count
      `;
      const cursor = await db.query(query, { orgId });
      const result = await cursor.all();
      return result[0] || 0;
    } catch (error) {
      this.logger.error(
        `Error fetching record count for org ${orgId}:`,
        error instanceof Error ? error.message : 'Unknown error',
      );
      return 0;
    }
  }

  /**
   * Check 1: MongoDB org count vs ArangoDB org IDs
   * Detects orphaned data in ArangoDB
   */
  private async checkOrphanedArangoData(
    report: ConsistencyReport,
  ): Promise<void> {
    try {
      // Get all orgs from MongoDB
      const mongoOrgs = await Org.find({ isDeleted: false }).select('_id');
      const mongoOrgIds = new Set(
        mongoOrgs.map((org) => org._id.toString()),
      );

      // Get all org IDs from ArangoDB
      const arangoOrgIds = await this.getArangoDBOrgIds();

      // Find orphaned org IDs (in ArangoDB but not MongoDB)
      const orphanedOrgIds = arangoOrgIds.filter(
        (id) => !mongoOrgIds.has(id),
      );

      if (orphanedOrgIds.length > 0) {
        // Get record counts for each orphaned org
        const orphanedDetails = await Promise.all(
          orphanedOrgIds.map(async (orgId) => {
            const recordCount = await this.getArangoDBRecordCount(orgId);
            return { orgId, recordCount };
          }),
        );

        const totalOrphanedRecords = orphanedDetails.reduce(
          (sum, item) => sum + item.recordCount,
          0,
        );

        report.addError(
          ConsistencyErrorType.ORPHANED_ARANGO_DATA,
          `Found ${orphanedOrgIds.length} org ID(s) in ArangoDB not in MongoDB, affecting ${totalOrphanedRecords} records`,
          {
            orphanedOrgIds,
            orphanedDetails,
            totalOrphanedRecords,
          },
          'critical',
        );

        this.logger.error(
          `CRITICAL: Orphaned data detected in ArangoDB: ${orphanedOrgIds.length} org(s), ${totalOrphanedRecords} records`,
        );
      }
    } catch (error) {
      this.logger.error(
        'Error checking orphaned ArangoDB data:',
        error instanceof Error ? error.message : 'Unknown error',
      );
    }
  }

  /**
   * Check 2: Connector configs reference valid orgs
   * Detects connector configs pointing to deleted or non-existent orgs
   */
  private async checkInvalidConnectorOrgs(
    report: ConsistencyReport,
  ): Promise<void> {
    try {
      const connectorConfigs = await ConnectorsConfig.find();

      for (const config of connectorConfigs) {
        const orgExists = await Org.exists({
          _id: config.orgId,
          isDeleted: false,
        });

        if (!orgExists) {
          report.addError(
            ConsistencyErrorType.INVALID_CONNECTOR_ORG,
            `Connector ${config.name} references non-existent org ${config.orgId}`,
            {
              connectorId: config._id.toString(),
              connectorName: config.name,
              orgId: config.orgId.toString(),
            },
            'high',
          );

          this.logger.warn(
            `Connector config ${config._id} references invalid org ${config.orgId}`,
          );
        }
      }
    } catch (error) {
      this.logger.error(
        'Error checking connector org validity:',
        error instanceof Error ? error.message : 'Unknown error',
      );
    }
  }

  /**
   * Check 3: ArangoDB records have corresponding connector configs
   * Detects records that exist without proper connector configuration
   */
  private async checkOrphanedRecords(
    report: ConsistencyReport,
  ): Promise<void> {
    try {
      // Get all org IDs from ArangoDB
      const arangoOrgIds = await this.getArangoDBOrgIds();

      // Get all org IDs that have connector configs
      const connectorConfigs = await ConnectorsConfig.find({ isEnabled: true });
      const configuredOrgIds = new Set(
        connectorConfigs.map((c) => c.orgId.toString()),
      );

      // Find org IDs in ArangoDB that don't have connector configs
      const orgsWithoutConfigs = arangoOrgIds.filter(
        (orgId) => !configuredOrgIds.has(orgId),
      );

      if (orgsWithoutConfigs.length > 0) {
        const details = await Promise.all(
          orgsWithoutConfigs.map(async (orgId) => {
            const recordCount = await this.getArangoDBRecordCount(orgId);
            return { orgId, recordCount };
          }),
        );

        report.addError(
          ConsistencyErrorType.ORPHANED_CONNECTOR_CONFIG,
          `Found ${orgsWithoutConfigs.length} org(s) with records but no active connector config`,
          {
            orgsWithoutConfigs: details,
          },
          'medium',
        );
      }
    } catch (error) {
      this.logger.error(
        'Error checking orphaned records:',
        error instanceof Error ? error.message : 'Unknown error',
      );
    }
  }

  /**
   * Check 4: Ensure all MongoDB orgs have expected data consistency
   * Verifies that orgs in MongoDB have proper setup
   */
  private async checkMongoDBOrgIntegrity(
    report: ConsistencyReport,
  ): Promise<void> {
    try {
      const orgs = await Org.find({ isDeleted: false });

      for (const org of orgs) {
        const orgId = org._id.toString();

        // Check if org has records in ArangoDB
        const recordCount = await this.getArangoDBRecordCount(orgId);

        // Check if org has connector config
        const connectorConfig = await ConnectorsConfig.findOne({ orgId: org._id });

        // If org has records but no connector, that's unusual
        if (recordCount > 0 && !connectorConfig) {
          report.addError(
            ConsistencyErrorType.MISSING_ORG_IN_MONGO,
            `Org ${orgId} has ${recordCount} records but no connector config`,
            {
              orgId,
              recordCount,
              orgName: org.registeredName,
            },
            'low',
          );
        }
      }
    } catch (error) {
      this.logger.error(
        'Error checking MongoDB org integrity:',
        error instanceof Error ? error.message : 'Unknown error',
      );
    }
  }

  /**
   * Run all consistency checks and return comprehensive report
   * This is the main entry point for the monitoring service
   */
  async checkConsistency(): Promise<ConsistencyReport> {
    this.logger.info('Starting database consistency check...');
    const report = new ConsistencyReport();

    try {
      // Run all checks in parallel for efficiency
      await Promise.all([
        this.checkOrphanedArangoData(report),
        this.checkInvalidConnectorOrgs(report),
        this.checkOrphanedRecords(report),
        this.checkMongoDBOrgIntegrity(report),
      ]);

      if (report.hasErrors()) {
        this.logger.error(
          `Consistency check completed with ${report.getErrors().length} error(s)`,
        );
      } else {
        this.logger.info('Consistency check completed - no issues found');
      }
    } catch (error) {
      this.logger.error(
        'Error during consistency check:',
        error instanceof Error ? error.message : 'Unknown error',
      );
    }

    return report;
  }
}
