import { test, expect } from '@playwright/test';

test.describe('Movie Details Flow', () => {
  test('Watchlist button works (when logged in)', async ({ page }) => {
    // Unique user per test
    const userEmail = `user_${Date.now()}@example.com`;
    
    await page.goto('/signup');
    await page.getByLabel(/Full Name/i).fill('Test User');
    await page.getByLabel(/Email Address/i).fill(userEmail);
    await page.getByLabel(/Password/i).fill('Password123!');
    await page.getByLabel(/Mobile Number/i).fill('1234567890');
    await page.click('button:has-text("Sign Up")');
    
    await page.waitForURL('**/', { timeout: 15000 });
    await expect(page).toHaveURL('/');

    await page.goto('/movie/27205'); // Inception
    
    // Use role-based selector for better reliability
    const watchlistBtn = page.getByRole('button', { name: /Watchlist/i });
    await expect(watchlistBtn).toBeVisible();
    await watchlistBtn.click();
    
    // Wait for the button to change state (Added to Watchlist)
    // Increased timeout for CI environment latency
    await expect(page.getByRole('button', { name: /In Watchlist/i })).toBeVisible({ timeout: 15000 });
  });
});
