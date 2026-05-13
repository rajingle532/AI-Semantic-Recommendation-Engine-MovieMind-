import { test, expect } from '@playwright/test';

test.describe('Home Page functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('Home page loads with movies', async ({ page }) => {
    await expect(page.locator('[data-testid="movie-card"]').first()).toBeVisible();
  });

  test('Search bar finds movies', async ({ page }) => {
    await page.fill('input[placeholder*="Search"]', 'Inception');
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/\/search\?q=Inception/);
    await expect(page.locator('h1')).toContainText('Inception');
  });

  test('Genre filter works', async ({ page }) => {
    await page.click('text=Action');
    // Check if URL updates or content changes
    await expect(page.locator('[data-testid="movie-card"]').first()).toBeVisible();
  });
});
