import { test, expect } from '@playwright/test';

test.describe('Accessibility', () => {
  test('should have no accessibility violations on dashboard', async ({ page }) => {
    await page.goto('/');
    
    // Check for basic accessibility features
    const mainContent = page.getByRole('main');
    await expect(mainContent).toBeVisible();
    
    // Check for skip links
    const skipLink = page.getByRole('link', { name: /skip to main content/i });
    await expect(skipLink).toBeVisible();
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/');
    
    // Tab through interactive elements
    await page.keyboard.press('Tab');
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('/');
    
    // Check for search box with proper label
    const searchBox = page.getByRole('searchbox');
    await expect(searchBox).toHaveAttribute('aria-label');
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/');
    
    // Check for h1 heading
    const h1 = page.locator('h1').first();
    await expect(h1).toBeVisible();
  });
});

