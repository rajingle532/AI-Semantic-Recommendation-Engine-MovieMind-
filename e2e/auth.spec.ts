import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('User can signup successfully', async ({ page }) => {
    await page.goto('/signup');
    await page.getByLabel(/Full Name/i).fill('E2E User');
    await page.getByLabel(/Email Address/i).fill(`e2e_${Date.now()}@example.com`);
    await page.getByLabel(/Password/i).fill('Password123!');
    await page.getByLabel(/Mobile Number/i).fill('1234567890');
    await page.click('button[type="submit"]');
    
    // Should be redirected to home or see success message
    await expect(page).toHaveURL('/');
    await expect(page.locator('nav')).toContainText('E2E User');
  });

  test('User can login successfully', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/Email Address/i).fill('test@example.com');
    await page.getByLabel(/Password/i).fill('password123');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL('/');
  });

  test('Logout works', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.getByLabel(/Email Address/i).fill('test@example.com');
    await page.getByLabel(/Password/i).fill('password123');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL('/');
    
    // Click avatar to open profile menu
    await page.click('[data-testid="navbar-avatar"]');
    
    // Click logout in dropdown
    await page.click('button:has-text("Logout")');
    await expect(page.locator('nav')).toContainText('Login');
  });
});
