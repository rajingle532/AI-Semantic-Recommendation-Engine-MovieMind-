import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  const uniqueEmail = `e2e_${Date.now()}@example.com`;
  const password = 'Password123!';

  test('User can signup successfully', async ({ page }) => {
    await page.goto('/signup');
    await page.getByLabel(/Full Name/i).fill('E2E User');
    await page.getByLabel(/Email Address/i).fill(uniqueEmail);
    await page.getByLabel(/Password/i).fill(password);
    await page.click('button:has-text("Sign Up")');
    
    // Should be redirected to home
    await page.waitForURL('**/', { timeout: 15000 });
    await expect(page).toHaveURL('/');
    await expect(page.locator('nav')).toContainText('E2E User');
  });

  test('User can login successfully', async ({ page }) => {
    // Signup first to ensure user exists
    const loginEmail = `login_${Date.now()}@example.com`;
    await page.goto('/signup');
    await page.getByLabel(/Full Name/i).fill('Login User');
    await page.getByLabel(/Email Address/i).fill(loginEmail);
    await page.getByLabel(/Password/i).fill(password);
    await page.click('button:has-text("Sign Up")');
    await page.waitForURL('**/', { timeout: 15000 });
    await expect(page).toHaveURL('/');
    
    // Logout
    await page.click('[data-testid="navbar-avatar"]');
    await page.click('button:has-text("Logout")');
    
    // Now try to Login
    await page.goto('/login');
    await page.getByLabel(/Email Address/i).fill(loginEmail);
    await page.getByLabel(/Password/i).fill(password);
    await page.click('button[type="submit"]');
    
    await page.waitForURL('**/');
    await expect(page).toHaveURL('/');
    await expect(page.locator('nav')).toContainText('Login User');
  });

  test('Logout works', async ({ page }) => {
    // Signup and Login
    const logoutEmail = `logout_${Date.now()}@example.com`;
    await page.goto('/signup');
    await page.getByLabel(/Full Name/i).fill('Logout User');
    await page.getByLabel(/Email Address/i).fill(logoutEmail);
    await page.getByLabel(/Password/i).fill(password);
    await page.click('button:has-text("Sign Up")');
    
    await page.waitForURL('**/', { timeout: 15000 });
    await expect(page).toHaveURL('/');
    
    // Click avatar to open profile menu
    await page.click('[data-testid="navbar-avatar"]');
    
    // Click logout in dropdown
    await page.click('button:has-text("Logout")');
    await expect(page.locator('nav')).toContainText('Login');
  });
});
