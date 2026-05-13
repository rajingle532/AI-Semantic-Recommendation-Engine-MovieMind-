import { test, expect } from '@playwright/test';

test.describe('Profile Page Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
  });

  test('Profile page shows user info and sections', async ({ page }) => {
    await page.goto('/profile');
    await expect(page.locator('text=Watchlist')).toBeVisible();
    await expect(page.locator('text=Ratings')).toBeVisible();
    await expect(page.locator('text=Recommendations')).toBeVisible();
  });
});
