import { test, expect } from '@playwright/test';

test.describe('Movie Details Flow', () => {
  test('Clicking movie opens detail page', async ({ page }) => {
    await page.goto('/');
    const firstMovie = page.locator('[data-testid="movie-card"]').first();
    const movieTitle = await firstMovie.locator('h3').innerText();
    await firstMovie.click();
    
    await expect(page.locator('h1')).toContainText(movieTitle);
    await expect(page.locator('text=Similar Movies')).toBeVisible();
  });

  test('Watchlist button works (when logged in)', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    await page.goto('/movie/27205'); // Inception
    await page.click('text=Add to Watchlist');
    await expect(page.locator('text=In Watchlist')).toBeVisible();
  });
});
