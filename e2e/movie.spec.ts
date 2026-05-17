import { test, expect } from '@playwright/test';

// Inject a fake auth token so ProtectedRoute allows access
async function loginAs(page: any) {
  await page.goto('/login');
  await page.evaluate(() => {
    localStorage.setItem('token', 'e2e-test-token');
    localStorage.setItem('user', JSON.stringify({
      id: 'test-user-id',
      name: 'E2E Tester',
      email: 'e2e@test.com',
    }));
  });
}

test.describe('Movie Detail Page', () => {
  test('Movie detail page loads with correct URL', async ({ page }) => {
    await loginAs(page);
    // Navigate to a known movie page (Inception - ID 27205)
    await page.goto('/movie/27205');

    // Verify URL is correct (app should stay on the movie page, not redirect to /login)
    await expect(page).toHaveURL(/\/movie\/27205/);

    // Verify the page rendered (navbar should be visible)
    await expect(page.locator('nav').first()).toBeVisible();
  });

  test('Movie page shows loading or content', async ({ page }) => {
    await loginAs(page);
    await page.goto('/movie/27205');

    // The page should show either a loader or movie content
    // We just verify it doesn't crash and the DOM has content
    const body = page.locator('body');
    await expect(body).not.toBeEmpty();
  });
});
