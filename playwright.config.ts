import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for PipesHub AI E2E tests
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/e2e',

  // Maximum time one test can run
  timeout: 120000, // 2 minutes for verification tests

  // Test artifacts
  outputDir: './test-results/artifacts',

  // Fail fast on CI
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 1,

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: './test-results/html-report' }],
    ['list'],
  ],

  // Shared settings for all projects
  use: {
    // Base URL for the application
    baseURL: 'http://localhost:3000',

    // Collect trace when retrying the failed test
    trace: 'retain-on-failure',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video on failure
    video: 'retain-on-failure',

    // Browser context options
    viewport: { width: 1920, height: 1080 },

    // Ignore HTTPS errors
    ignoreHTTPSErrors: true,
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: {
          // Run in headed mode to see the test
          headless: false,
          slowMo: 500, // Slow down by 500ms for visibility
        },
      },
    },
  ],

  // Run local dev server before starting tests
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:3000',
  //   reuseExistingServer: !process.env.CI,
  // },
});
