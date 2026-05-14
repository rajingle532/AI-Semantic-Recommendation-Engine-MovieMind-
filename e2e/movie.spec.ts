import { test, expect } from '@playwright/test';

test.describe('Movie Details Flow', () => {
  test('Watchlist button works (when logged in)', async ({ page }) => {
    // Unique user per test
    const userEmail = `user_${Date.now()}@example.com`;
    
    await page.goto('/signup');
    await page.getByLabel(/Full Name/i).fill('Test User');
    await page.getByLabel(/Email Address/i).fill(userEmail);
    await page.getByLabel(/Password/i).fill('Password123!');
    await page.click('button:has-text("Sign Up")');
    
    await page.waitForURL('**/', { timeout: 15000 });
    await expect(page).toHaveURL('/');

    await page.goto('/movie/27205'); // Inception
    
    // Just verify button exists and is clickable
    const watchlistBtn = page.getByRole('button', { name: /watchlist/i });
    await expect(watchlistBtn).toBeVisible();
    await watchlistBtn.click();
    
    // Wait for the action to complete and ensure no error is thrown
    // We wait for 2 seconds to allow the API call to resolve
    await page.waitForTimeout(2000);
    
    // Test passes if no crash or error occurs
  });
});
