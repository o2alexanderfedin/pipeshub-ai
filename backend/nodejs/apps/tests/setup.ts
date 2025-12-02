/**
 * Jest Setup for Node.js Backend Tests
 *
 * This file runs before each test file.
 * Use it to configure global test environment, mocks, and utilities.
 */

// Extend Jest matchers
import 'jest-extended';

// Set test environment variables
process.env.NODE_ENV = 'test';
process.env.LOG_LEVEL = 'error'; // Reduce noise in tests

// Global test timeout
jest.setTimeout(10000);

// Mock console methods to reduce noise (optional)
global.console = {
  ...console,
  // Uncomment to suppress logs in tests
  // log: jest.fn(),
  // debug: jest.fn(),
  // info: jest.fn(),
  // warn: jest.fn(),
  // Keep error for debugging
  error: console.error,
};

// Global beforeAll
beforeAll(() => {
  // Setup code that runs once before all tests
  console.log('🧪 Starting Node.js backend tests...');
});

// Global afterAll
afterAll(() => {
  // Cleanup code that runs once after all tests
  console.log('✅ Node.js backend tests completed');
});

// Global beforeEach
beforeEach(() => {
  // Reset mocks before each test
  jest.clearAllMocks();
});

// Global afterEach
afterEach(() => {
  // Cleanup after each test
});

export {};
