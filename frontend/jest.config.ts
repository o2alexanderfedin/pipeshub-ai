/**
 * Jest Configuration for Hupyy KB React Frontend
 *
 * This configuration supports:
 * - React component testing with Testing Library
 * - TypeScript support
 * - CSS/SCSS module mocking
 * - SVG and asset mocking
 * - Coverage reporting
 *
 * @see https://jestjs.io/docs/configuration
 */

import type { Config } from 'jest';

const config: Config = {
  // Use jsdom for React testing
  testEnvironment: 'jsdom',

  // Roots for test discovery
  roots: ['<rootDir>/src'],

  // Test file patterns
  testMatch: [
    '**/__tests__/**/*.{ts,tsx}',
    '**/?(*.)+(spec|test).{ts,tsx}',
  ],

  // Transform files
  transform: {
    '^.+\\.tsx?$': ['ts-jest', {
      tsconfig: '<rootDir>/tsconfig.json',
      diagnostics: {
        warnOnly: true,
      },
    }],
    '^.+\\.(js|jsx)$': 'babel-jest',
  },

  // Module file extensions
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],

  // Module name mapper for path aliases and assets
  moduleNameMapper: {
    // Path aliases (match your tsconfig paths)
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@pages/(.*)$': '<rootDir>/src/pages/$1',
    '^@hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@store/(.*)$': '<rootDir>/src/store/$1',
    '^@assets/(.*)$': '<rootDir>/src/assets/$1',

    // CSS/SCSS modules
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',

    // Static assets
    '\\.(jpg|jpeg|png|gif|svg|webp|ico)$': '<rootDir>/tests/__mocks__/fileMock.ts',
    '\\.(ttf|eot|woff|woff2)$': '<rootDir>/tests/__mocks__/fileMock.ts',
  },

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/tests/setup.tsx'],

  // Coverage configuration
  collectCoverage: false, // Enable with --coverage flag
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{ts,tsx}',
    '!src/**/*.spec.{ts,tsx}',
    '!src/**/*.test.{ts,tsx}',
    '!src/index.tsx',
    '!src/vite-env.d.ts',
    '!src/**/__tests__/**',
    '!src/**/__mocks__/**',
  ],

  coverageDirectory: '<rootDir>/coverage',

  coverageReporters: [
    'text',
    'text-summary',
    'html',
    'lcov',
    'json',
  ],

  // Coverage thresholds
  coverageThresholds: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },

  // Ignore patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '/dist/',
    '/build/',
    '/.git/',
  ],

  // Watch ignore patterns
  watchPathIgnorePatterns: [
    '/node_modules/',
    '/dist/',
    '/coverage/',
  ],

  // Clear mocks between tests
  clearMocks: true,

  // Restore mocks between tests
  restoreMocks: true,

  // Reset mocks between tests
  resetMocks: true,

  // Verbose output
  verbose: true,

  // Test timeout (milliseconds)
  testTimeout: 10000,

  // Reporters
  reporters: [
    'default',
    ['jest-junit', {
      outputDirectory: '<rootDir>/test-results',
      outputName: 'junit.xml',
      classNameTemplate: '{classname}',
      titleTemplate: '{title}',
      ancestorSeparator: ' › ',
      usePathForSuiteName: true,
    }],
  ],

  // Error on deprecated APIs
  errorOnDeprecated: true,

  // Maximum number of concurrent workers
  maxWorkers: '50%',

  // Transform ignore patterns
  transformIgnorePatterns: [
    'node_modules/(?!(@mui|@emotion|@iconify)/)',
  ],

  // Globals for React Testing Library
  globals: {
    'ts-jest': {
      isolatedModules: true,
    },
  },
};

export default config;
