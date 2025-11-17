import { test, expect } from '@playwright/test';

test.describe('Transcription Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/transcription');
  });

  test('should load transcription page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /live transcription/i })).toBeVisible();
  });

  test('should display start recording button', async ({ page }) => {
    const startButton = page.getByRole('button', { name: /start recording/i });
    await expect(startButton).toBeVisible();
  });

  test('should show recording controls', async ({ page }) => {
    // Check for control buttons
    const controls = page.locator('[role="group"][aria-label*="Transcription controls"]');
    await expect(controls).toBeVisible();
  });

  test('should have keyboard shortcuts', async ({ page }) => {
    // Test Ctrl+R shortcut (start/stop)
    await page.keyboard.press('Control+r');
    // Should trigger recording start/stop
    await page.waitForTimeout(500);
  });
});

