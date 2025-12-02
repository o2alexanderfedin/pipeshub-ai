/**
 * Unit tests for configuration manager validators.
 *
 * Tests Zod schema validation for:
 * - Storage configuration
 * - AI models configuration
 * - Database configuration
 * - Field validation and error messages
 *
 * Run with:
 *   npm test -- validators.spec.ts
 *   npm test -- validators.spec.ts --testNamePattern="storage"
 */

import { describe, expect, it, beforeEach } from '@jest/globals';
import {
  storageValidationSchema,
  s3ConfigSchema,
  azureBlobConfigSchema,
  aiModelsConfigSchema,
  modelConfigurationSchema,
  addProviderRequestSchema,
} from '../../../src/modules/configuration_manager/validator/validators';

// ============================================================================
// Storage Validation Tests
// ============================================================================

describe('Storage Configuration Validators', () => {
  describe('s3ConfigSchema', () => {
    it('should validate valid S3 configuration', () => {
      // Arrange
      const validS3Config = {
        storageType: 'S3' as const,
        s3AccessKeyId: 'AKIAIOSFODNN7EXAMPLE',
        s3SecretAccessKey: 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        s3Region: 'us-east-1',
        s3BucketName: 'my-test-bucket',
      };

      // Act
      const result = s3ConfigSchema.safeParse(validS3Config);

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.s3AccessKeyId).toBe('AKIAIOSFODNN7EXAMPLE');
        expect(result.data.s3Region).toBe('us-east-1');
      }
    });

    it('should reject S3 config with missing access key', () => {
      // Arrange
      const invalidS3Config = {
        storageType: 'S3' as const,
        // Missing s3AccessKeyId
        s3SecretAccessKey: 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        s3Region: 'us-east-1',
        s3BucketName: 'my-test-bucket',
      };

      // Act
      const result = s3ConfigSchema.safeParse(invalidS3Config);

      // Assert
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('required');
      }
    });

    it('should reject S3 config with empty region', () => {
      // Arrange
      const invalidS3Config = {
        storageType: 'S3' as const,
        s3AccessKeyId: 'AKIAIOSFODNN7EXAMPLE',
        s3SecretAccessKey: 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        s3Region: '', // Empty string
        s3BucketName: 'my-test-bucket',
      };

      // Act
      const result = s3ConfigSchema.safeParse(invalidS3Config);

      // Assert
      expect(result.success).toBe(false);
      if (!result.success) {
        const regionError = result.error.issues.find(
          (issue) => issue.path[0] === 's3Region'
        );
        expect(regionError?.message).toContain('required');
      }
    });
  });

  describe('azureBlobConfigSchema', () => {
    it('should validate valid Azure Blob configuration with connection string', () => {
      // Arrange
      const validAzureConfig = {
        storageType: 'AZURE_BLOB' as const,
        azureBlobConnectionString:
          'DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=mykey;EndpointSuffix=core.windows.net',
        containerName: 'my-container',
      };

      // Act
      const result = azureBlobConfigSchema.safeParse(validAzureConfig);

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.containerName).toBe('my-container');
      }
    });

    it('should validate valid Azure Blob configuration with individual parameters', () => {
      // Arrange
      const validAzureConfig = {
        storageType: 'AZURE_BLOB' as const,
        accountName: 'myaccount',
        accountKey: 'mykey123456',
        containerName: 'my-container',
        endpointProtocol: 'https' as const,
        endpointSuffix: 'core.windows.net',
      };

      // Act
      const result = azureBlobConfigSchema.safeParse(validAzureConfig);

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.accountName).toBe('myaccount');
        expect(result.data.endpointProtocol).toBe('https');
      }
    });

    // TODO: Add more tests:
    // - test missing container name
    // - test invalid endpoint protocol
    // - test refinement validation (either connection string OR individual params)
  });
});

// ============================================================================
// AI Models Configuration Tests
// ============================================================================

describe('AI Models Configuration Validators', () => {
  describe('modelConfigurationSchema', () => {
    it('should validate valid model configuration', () => {
      // Arrange
      const validConfig = {
        provider: 'openAI' as const,
        configuration: {
          model: 'gpt-4o',
          apiKey: 'sk-test-key-123',
          endpoint: 'https://api.openai.com/v1',
        },
        isMultimodal: false,
        isReasoning: false,
        isDefault: true,
      };

      // Act
      const result = modelConfigurationSchema.safeParse(validConfig);

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.provider).toBe('openAI');
        expect(result.data.configuration.model).toBe('gpt-4o');
        expect(result.data.isDefault).toBe(true);
      }
    });

    it('should accept Anthropic model configuration', () => {
      // Arrange
      const anthropicConfig = {
        provider: 'anthropic' as const,
        configuration: {
          model: 'claude-sonnet-4-5-20250929',
          apiKey: 'sk-ant-test-123',
        },
        isMultimodal: true,
        isReasoning: true,
        isDefault: false,
      };

      // Act
      const result = modelConfigurationSchema.safeParse(anthropicConfig);

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.provider).toBe('anthropic');
        expect(result.data.isReasoning).toBe(true);
      }
    });

    it('should set default values for optional fields', () => {
      // Arrange
      const minimalConfig = {
        provider: 'ollama' as const,
        configuration: {
          model: 'llama2',
        },
      };

      // Act
      const result = modelConfigurationSchema.safeParse(minimalConfig);

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.isMultimodal).toBe(false);
        expect(result.data.isReasoning).toBe(false);
        expect(result.data.isDefault).toBe(false);
      }
    });

    // TODO: Add more tests:
    // - test invalid provider name
    // - test configuration with model_kwargs
    // - test embedding provider configuration
  });

  describe('addProviderRequestSchema', () => {
    it('should validate valid add provider request', () => {
      // Arrange
      const validRequest = {
        body: {
          modelType: 'llm' as const,
          provider: 'anthropic' as const,
          configuration: {
            model: 'claude-sonnet-4-5-20250929',
            apiKey: 'sk-ant-key',
          },
          isMultimodal: true,
          isReasoning: true,
          isDefault: true,
        },
      };

      // Act
      const result = addProviderRequestSchema.safeParse(validRequest);

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.body.modelType).toBe('llm');
        expect(result.data.body.provider).toBe('anthropic');
      }
    });

    it('should reject request with invalid model type', () => {
      // Arrange
      const invalidRequest = {
        body: {
          modelType: 'invalid_type', // Not a valid enum value
          provider: 'openAI' as const,
          configuration: {
            model: 'gpt-4',
          },
        },
      };

      // Act
      const result = addProviderRequestSchema.safeParse(invalidRequest);

      // Assert
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues.length).toBeGreaterThan(0);
      }
    });

    // TODO: Add more tests:
    // - test all model types (embedding, ocr, slm, reasoning, multiModal)
    // - test all provider types
    // - test configuration validation
  });
});

// ============================================================================
// INSTRUCTIONS FOR EXTENDING TESTS
// ============================================================================
/**
 * TO ADD MORE TESTS, FOLLOW THESE PATTERNS:
 *
 * 1. Group related tests in describe blocks:
 *    describe('SchemaName', () => {
 *      it('should test specific behavior', () => { ... });
 *    });
 *
 * 2. Use descriptive test names:
 *    it('should validate valid configuration', () => { ... });
 *    it('should reject configuration with missing field', () => { ... });
 *
 * 3. Follow Arrange-Act-Assert pattern:
 *    // Arrange - Set up test data
 *    const data = { ... };
 *
 *    // Act - Execute the validation
 *    const result = schema.safeParse(data);
 *
 *    // Assert - Verify the results
 *    expect(result.success).toBe(true);
 *
 * 4. Test both success and failure cases:
 *    - Valid data should pass
 *    - Invalid data should fail with appropriate error messages
 *    - Edge cases (empty strings, null, undefined, boundaries)
 *
 * 5. Use safeParse() for better error handling:
 *    const result = schema.safeParse(data);
 *    if (result.success) {
 *      // Access validated data
 *      expect(result.data.field).toBe(expected);
 *    } else {
 *      // Access error messages
 *      expect(result.error.issues[0].message).toContain('expected text');
 *    }
 *
 * For complete test specifications, see:
 *     docs/UNIT-TEST-SPECS.md
 *
 * To run these tests:
 *     # All tests
 *     npm test -- validators.spec.ts
 *
 *     # Specific test suite
 *     npm test -- validators.spec.ts --testNamePattern="Storage"
 *
 *     # With coverage
 *     npm test -- validators.spec.ts --coverage
 */
