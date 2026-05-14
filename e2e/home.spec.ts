import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('Home page loads with navbar', async ({ page }) => {
    await page.goto('/');
    
    // Verify navigation bar is visible
    await expect(page.locator('nav').first()).toBeVisible();
    
    // Verify the MovieMind branding is present
    await expect(page.locator('text=MovieMind').first()).toBeVisible();
  });

  test('Search bar exists and is functional', async ({ page }) => {
    await page.goto('/');
    
    // Verify search input exists
    const searchInput = page.locator('input[type="text"], input[placeholder*="Search" i]').first();
    await expect(searchInput).toBeVisible();
    
    // Verify we can type in it
    await searchInput.fill('Test');
    await expect(searchInput).toHaveValue('Test');
  });

  test('Login and Signup links are visible when not authenticated', async ({ page }) => {
    await page.goto('/');
    
    // Check auth links exist in navbar
    const loginLink = page.locator('a[href*="login"], a:has-text("Login")').first();
    await expect(loginLink).toBeVisible();
  });

  test('Page title is set correctly', async ({ page }) => {
    await page.goto('/');
    
    // Page should have a title (not empty)
    const title = await page.title();
    expect(title.length).toBeGreaterThan(0);
  });
});
