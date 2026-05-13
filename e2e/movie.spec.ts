import { test, expect } from '@playwright/test';

test.describe('Movie Details Flow', () => {
  test('Clicking movie opens detail page', async ({ page }) => {
    await page.goto('/');
    const firstMovie = page.locator('[data-testid="movie-card"]').first();
    const movieTitle = await firstMovie.locator('h3').getAttribute('title');
    
    await firstMovie.click();
    await expect(page.locator('h1')).toContainText(movieTitle || "");
    await expect(page.locator('text=Similar Movies')).toBeVisible();
  });

  test('Watchlist button works (when logged in)', async ({ page }) => {
    // Signup to create a valid session
    const watchlistEmail = `watchlist_${Date.now()}@example.com`;
    await page.goto('/signup');
    await page.getByLabel(/Full Name/i).fill('Watchlist User');
    await page.getByLabel(/Email Address/i).fill(watchlistEmail);
    await page.getByLabel(/Password/i).fill('Password123!');
    await page.getByLabel(/Mobile Number/i).fill('1234567890');
    await page.click('button:has-text("Sign Up")');
    await page.waitForURL('**/', { timeout: 15000 });
    await expect(page).toHaveURL('/');

    await page.goto('/movie/27205'); // Inception
    // Use specific button text to avoid strict mode violation
    await page.click('button:has-text("Add to Watchlist")');
    await expect(page.locator('button:has-text("In Watchlist")')).toBeVisible();
  });
});
