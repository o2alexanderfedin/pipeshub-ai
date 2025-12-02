# E2E Test Specifications for Hupyy SMT Verification (Playwright)

**Date:** November 30, 2025
**Purpose:** Complete Playwright end-to-end test specifications

---

## Overview

**Test Count:** 15-20 tests (5% of suite)
**Framework:** Playwright with TypeScript
**Pattern:** Page Object Model
**Execution Time:** <3 minutes
**Target:** Critical user workflows

---

## Page Object Models

### ChatPage.ts
```typescript
export class ChatPage {
  constructor(private page: Page) {}
  
  async enableVerification() {
    await this.page.getByRole('checkbox', { name: /enable verification/i }).check()
  }
  
  async disableVerification() {
    await this.page.getByRole('checkbox', { name: /enable verification/i }).uncheck()
  }
  
  async isVerificationEnabled(): Promise<boolean> {
    return await this.page.getByRole('checkbox', { name: /enable verification/i }).isChecked()
  }
  
  async submitQuery(query: string) {
    await this.page.getByPlaceholder(/enter.*query/i).fill(query)
    await this.page.getByRole('button', { name: /submit|send/i }).click()
  }
  
  async waitForResults() {
    await this.page.waitForSelector('[data-testid="search-results"]')
  }
  
  async getVerificationBadge() {
    return this.page.locator('[data-testid="verification-badge"]')
  }
}
```

---

## Test Specifications

### File: `tests/e2e/verification/verification-checkbox.spec.ts`

**Test Count:** 8 tests

#### Test 1: Checkbox Visibility
```typescript
test('should display verification checkbox in active conversation', async ({ page }) => {
  const chatPage = new ChatPage(page)
  
  await page.goto('/chat')
  await page.getByRole('button', { name: /new conversation/i }).click()
  
  const checkbox = page.getByRole('checkbox', { name: /enable verification/i })
  await expect(checkbox).toBeVisible()
  
  await page.screenshot({ path: 'test-results/checkbox-visible.png' })
})
```

#### Test 2: Checkbox Toggle
```typescript
test('should toggle verification checkbox', async ({ page }) => {
  const chatPage = new ChatPage(page)
  
  await page.goto('/chat/conversation-123')
  
  // Initially unchecked
  await expect(await chatPage.isVerificationEnabled()).toBe(false)
  
  // Check
  await chatPage.enableVerification()
  await expect(await chatPage.isVerificationEnabled()).toBe(true)
  
  // Uncheck
  await chatPage.disableVerification()
  await expect(await chatPage.isVerificationEnabled()).toBe(false)
})
```

#### Test 3: Tooltip
```typescript
test('should show tooltip on hover', async ({ page }) => {
  await page.goto('/chat/conversation-123')
  
  const checkbox = page.getByRole('checkbox', { name: /enable verification/i })
  await checkbox.hover()
  
  const tooltip = page.getByText(/SMT verification uses formal logic/i)
  await expect(tooltip).toBeVisible()
})
```

#### Test 4-8: Additional Checkbox Tests
- test_checkbox_persists_across_page_refresh
- test_checkbox_disabled_during_loading
- test_checkbox_keyboard_accessible
- test_checkbox_aria_labels
- test_checkbox_resets_on_new_conversation

---

### File: `tests/e2e/verification/verification-flow.spec.ts`

**Test Count:** 7 tests

#### Test 9: Search Without Verification
```typescript
test('should send query without verification when unchecked', async ({ page }) => {
  const chatPage = new ChatPage(page)
  
  await page.goto('/chat/conversation-123')
  await chatPage.disableVerification()
  
  // Intercept API request
  const requestPromise = page.waitForRequest(request => 
    request.url().includes('/api/search') &&
    request.method() === 'POST'
  )
  
  await chatPage.submitQuery('Find all admin users')
  const request = await requestPromise
  
  const postData = request.postDataJSON()
  expect(postData.verification_enabled).toBe(false)
  
  await chatPage.waitForResults()
})
```

#### Test 10: Search With Verification
```typescript
test('should send query with verification when checked', async ({ page }) => {
  const chatPage = new ChatPage(page)
  
  await page.goto('/chat/conversation-123')
  await chatPage.enableVerification()
  
  const requestPromise = page.waitForRequest(request => 
    request.url().includes('/api/search')
  )
  
  await chatPage.submitQuery('All prime numbers > 2 are odd')
  const request = await requestPromise
  
  const postData = request.postDataJSON()
  expect(postData.verification_enabled).toBe(true)
  
  await chatPage.waitForResults()
  
  // Verify results contain verification info
  const badge = await chatPage.getVerificationBadge()
  await expect(badge).toBeVisible()
  
  await page.screenshot({ path: 'test-results/verification-results.png' })
})
```

#### Test 11-15: Additional Flow Tests
- test_verification_timeout_handling
- test_verification_error_display
- test_multiple_queries_with_verification
- test_verification_badge_shows_sat_verdict
- test_verification_badge_shows_unsat_verdict

---

### File: `tests/e2e/verification/accessibility.spec.ts`

**Test Count:** 5 tests

#### Test 16: Keyboard Navigation
```typescript
test('should navigate checkbox with keyboard', async ({ page }) => {
  await page.goto('/chat/conversation-123')
  
  // Tab to checkbox
  await page.keyboard.press('Tab')
  // ... (navigate to checkbox)
  
  const checkbox = page.getByRole('checkbox', { name: /enable verification/i })
  await expect(checkbox).toBeFocused()
  
  // Toggle with Space
  await page.keyboard.press('Space')
  await expect(checkbox).toBeChecked()
})
```

#### Test 17-20: Additional Accessibility Tests
- test_screen_reader_announcements
- test_focus_indicators_visible
- test_color_contrast_meets_wcag
- test_aria_live_region_for_results

---

## Test Configuration

### playwright.config.ts
```typescript
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [
    ['html'],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
  webServer: {
    command: 'npm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

---

## Execution

### Local
```bash
npx playwright test
npx playwright test --headed  # Visual debugging
npx playwright test --debug   # Step-through debugging
npx playwright show-report    # View HTML report
```

### CI/CD
```bash
npx playwright test --shard=1/2
npx playwright test --shard=2/2
```

---

## Summary

| Test File | Test Count | Critical? | Duration |
|-----------|-----------|-----------|----------|
| verification-checkbox.spec.ts | 8 | Yes | ~1 min |
| verification-flow.spec.ts | 7 | Yes | ~1.5 min |
| accessibility.spec.ts | 5 | Medium | ~30s |
| **Total** | **20** | **High** | **~3 min** |
