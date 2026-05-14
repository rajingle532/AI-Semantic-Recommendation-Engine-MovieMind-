import { test, expect } from '@playwright/test';

test.describe('Profile Page Flow', () => {
  test('Profile page shows user info and sections', async ({ page }) => {
    // Signup first to create a valid session and user
    const profileEmail = `profile_${Date.now()}@example.com`;
    await page.goto('/signup');
    await page.getByLabel(/Full Name/i).fill('Profile User');
    await page.getByLabel(/Email Address/i).fill(profileEmail);
    await page.getByLabel(/Password/i).fill('Password123!');
    await page.click('button:has-text("Sign Up")');
    await page.waitForURL('**/', { timeout: 15000 });
    await expect(page).toHaveURL('/');

    await page.goto('/profile');
    await expect(page.locator('h1')).toContainText('Profile User');
    // Correct syntax: .first() inside the expect()
    await expect(page.locator('span:has-text("Watchlist")').first()).toBeVisible();
    await expect(page.locator('span:has-text("Ratings")').first()).toBeVisible();
    await expect(page.locator('text=Recommendations')).toBeVisible();
  });
});
