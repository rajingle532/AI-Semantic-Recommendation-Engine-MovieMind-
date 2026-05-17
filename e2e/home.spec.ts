import { test, expect } from '@playwright/test';

// Inject a fake auth token so ProtectedRoute allows access
async function loginAs(page: any) {
  await page.goto('/login'); // land somewhere first so origin is set
  await page.evaluate(() => {
    localStorage.setItem('token', 'e2e-test-token');
    localStorage.setItem('user', JSON.stringify({
      id: 'test-user-id',
      name: 'E2E Tester',
      email: 'e2e@test.com',
    }));
  });
}

test.describe('Home Page', () => {
  test('Home page loads with navbar', async ({ page }) => {
    await loginAs(page);
    await page.goto('/');

    // Verify navigation bar is visible
    await expect(page.locator('nav').first()).toBeVisible();

    // Verify the MovieMind branding is present
    await expect(page.locator('text=MovieMind').first()).toBeVisible();
  });

  test('Search bar exists and is functional', async ({ page }) => {
    await loginAs(page);
    await page.goto('/');

    // Verify search input exists (visible to authenticated users)
    const searchInput = page.locator('input[type="text"], input[placeholder*="Search" i]').first();
    await expect(searchInput).toBeVisible({ timeout: 8000 });

    // Verify we can type in it
    await searchInput.fill('Test');
    await expect(searchInput).toHaveValue('Test');
  });

  test('Login and Signup links are visible when not authenticated', async ({ page }) => {
    await page.goto('/');

    // When not logged in, we land on /login - check for Login button
    const loginLink = page.locator('a[href*="login"], a:has-text("Login"), button:has-text("Login")').first();
    await expect(loginLink).toBeVisible();
  });

  test('Page title is set correctly', async ({ page }) => {
    await page.goto('/');

    // Page should have a title (not empty)
    const title = await page.title();
    expect(title.length).toBeGreaterThan(0);
  });
});
