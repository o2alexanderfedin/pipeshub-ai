import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright Test Configuration for PipesHub AI
 *
 * This configuration supports:
 * - E2E testing of the full application
 * - Cross-browser testing (Chromium, Firefox, WebKit)
 * - Visual regression testing
 * - API testing
 * - Verification feature testing
 *
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  // Directory containing test files
  testDir: './tests/e2e',

  // Test file patterns
  testMatch: '**/*.spec.ts',

  // Maximum time one test can run for
  timeout: 120 * 1000, // 2 minutes for verification tests

  // Run tests in files in parallel
  fullyParallel: process.env.CI ? false : true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Opt out of parallel tests on CI for more stable runs
  workers: process.env.CI ? 1 : 1,

  // Reporter to use
  reporter: [
    ['html', { outputFolder: 'test-results/e2e-report', open: 'never' }],
    ['json', { outputFile: 'test-results/e2e-results.json' }],
    ['junit', { outputFile: 'test-results/e2e-junit.xml' }],
    ['list'],
    // GitHub Actions reporter
    ...(process.env.CI ? [['github']] : []),
  ],

  // Shared settings for all the projects below
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL: process.env.BASE_URL || 'http://localhost:3000',

    // Collect trace when retrying the failed test
    trace: 'retain-on-failure',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video on failure
    video: 'retain-on-failure',

    // Browser context options
    viewport: { width: 1920, height: 1080 },

    // Accept downloads
    acceptDownloads: true,

    // Ignore HTTPS errors
    ignoreHTTPSErrors: true,

    // Default timeout for assertions
    expect: {
      timeout: 5000,
    },

    // Action timeout
    actionTimeout: 10000,

    // Navigation timeout
    navigationTimeout: 30000,
  },

  // Output folder for test artifacts
  outputDir: 'test-results/e2e-artifacts',

  // Folder for snapshots
  snapshotDir: 'tests/e2e/snapshots',

  // Configure projects for major browsers
  projects: [
    // =========================================================================
    // Desktop Browsers
    // =========================================================================
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
        launchOptions: {
          // Run in headed mode for local development
          headless: !!process.env.CI,
          // Slow down for visibility (only in local dev)
          slowMo: process.env.CI ? 0 : 500,
        },
      },
    },

    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        viewport: { width: 1920, height: 1080 },
      },
    },

    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
        viewport: { width: 1920, height: 1080 },
      },
    },

    // =========================================================================
    // Mobile Browsers (uncomment as needed)
    // =========================================================================
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
    // {
    //   name: 'Mobile Safari',
    //   use: { ...devices['iPhone 12'] },
    // },
  ],

  // =========================================================================
  // Global Setup & Teardown
  // =========================================================================

  // Run your global setup before all tests
  // globalSetup: require.resolve('./tests/e2e/support/global-setup'),

  // Run your global teardown after all tests
  // globalTeardown: require.resolve('./tests/e2e/support/global-teardown'),

  // =========================================================================
  // Web Server Configuration
  // =========================================================================

  // Run local dev server before starting the tests
  webServer: {
    command: 'cd frontend && npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000, // 2 minutes
    stdout: 'ignore',
    stderr: 'pipe',
  },

  // =========================================================================
  // Global Test Configuration
  // =========================================================================

  // Maximum number of test failures before stopping
  maxFailures: process.env.CI ? 10 : undefined,

  // Whether to preserve output between runs
  preserveOutput: 'always',

  // Update snapshots with `npx playwright test --update-snapshots`
  // updateSnapshots: 'missing',

  // =========================================================================
  // Metadata
  // =========================================================================

  metadata: {
    project: 'PipesHub AI',
    description: 'End-to-end tests for PipesHub AI verification feature',
    testType: 'e2e',
  },
});
