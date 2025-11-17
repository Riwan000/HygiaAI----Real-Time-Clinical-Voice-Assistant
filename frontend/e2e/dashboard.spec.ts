import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load dashboard page', async ({ page }) => {
    await expect(page).toHaveTitle(/HygiaAI/i);
  });

  test('should display search box', async ({ page }) => {
    const searchBox = page.getByRole('searchbox');
    await expect(searchBox).toBeVisible();
  });

  test('should search for cases', async ({ page }) => {
    const searchBox = page.getByRole('searchbox');
    await searchBox.fill('fever');
    await searchBox.press('Enter');
    
    // Wait for results (mock API will return results)
    await page.waitForTimeout(1000);
    
    // Check if results are displayed
    const results = page.locator('[data-testid="case-card"]').or(page.locator('text=case_'));
    await expect(results.first()).toBeVisible({ timeout: 5000 });
  });

  test('should navigate to SOAP Notes page', async ({ page }) => {
    const soapLink = page.getByRole('link', { name: /soap notes/i });
    await soapLink.click();
    await expect(page).toHaveURL(/.*soap-notes/i);
  });

  test('should navigate to Transcription page', async ({ page }) => {
    const transcriptionLink = page.getByRole('link', { name: /transcription/i });
    await transcriptionLink.click();
    await expect(page).toHaveURL(/.*transcription/i);
  });
});

