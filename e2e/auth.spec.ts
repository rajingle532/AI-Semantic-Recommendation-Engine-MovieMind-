import { test, expect } from '@playwright/test';

test.describe('Authentication Pages', () => {
  test('Login page loads correctly', async ({ page }) => {
    await page.goto('/login');
    
    // Verify the page loaded
    await expect(page).toHaveURL(/\/login/);
    
    // Check form elements exist
    await expect(page.locator('input[type="email"], input[name="email"], [placeholder*="email" i]').first()).toBeVisible();
    await expect(page.locator('input[type="password"]').first()).toBeVisible();
    await expect(page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")').first()).toBeVisible();
  });

  test('Signup page loads correctly', async ({ page }) => {
    await page.goto('/signup');
    
    // Verify the page loaded
    await expect(page).toHaveURL(/\/signup/);
    
    // Check form elements exist
    await expect(page.locator('input').first()).toBeVisible();
    await expect(page.locator('button[type="submit"], button:has-text("Sign Up")').first()).toBeVisible();
  });

  test('Login page has link to signup', async ({ page }) => {
    await page.goto('/login');
    
    // Look for a link/text pointing to signup
    const signupLink = page.locator('a[href*="signup"], a:has-text("Sign Up"), a:has-text("Register"), a:has-text("Create")').first();
    await expect(signupLink).toBeVisible();
  });

  test('Signup page has link to login', async ({ page }) => {
    await page.goto('/signup');
    
    // Look for a link/text pointing to login
    const loginLink = page.locator('a[href*="login"], a:has-text("Login"), a:has-text("Sign In"), a:has-text("Log In")').first();
    await expect(loginLink).toBeVisible();
  });
});
