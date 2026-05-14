import { test, expect } from '@playwright/test';

test.describe('Profile Page', () => {
  test('Profile page redirects to login when not authenticated', async ({ page }) => {
    // Go to profile without being logged in
    await page.goto('/profile');
    
    // Should redirect to login page since user is not authenticated
    await page.waitForURL(/\/(login|signup)/, { timeout: 10000 });
    
    // Verify we ended up on login or signup page
    const url = page.url();
    expect(url).toMatch(/\/(login|signup)/);
  });

  test('Account page redirects to login when not authenticated', async ({ page }) => {
    // Go to account settings without being logged in
    await page.goto('/account');
    
    // Should redirect to login page since user is not authenticated
    await page.waitForURL(/\/(login|signup)/, { timeout: 10000 });
    
    // Verify we ended up on login or signup page
    const url = page.url();
    expect(url).toMatch(/\/(login|signup)/);
  });
});
