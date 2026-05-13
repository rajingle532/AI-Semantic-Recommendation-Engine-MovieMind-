# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth.spec.ts >> Authentication Flow >> User can login successfully
- Location: e2e\auth.spec.ts:17:7

# Error details

```
Error: expect(page).toHaveURL(expected) failed

Expected: "http://localhost:5173/"
Received: "http://localhost:5173/login"
Timeout:  5000ms

Call log:
  - Expect "toHaveURL" with timeout 5000ms
    12 × unexpected value "http://localhost:5173/login"

```

```yaml
- navigation:
  - link "MovieMind":
    - /url: /
    - img
    - text: MovieMind
  - img
  - textbox "Search movies, actors, or genres..."
  - button "Switch to Light Mode":
    - img
  - link "Login":
    - /url: /login
  - link "Sign Up":
    - /url: /signup
- heading "Sign In" [level=1]
- text: Email Address
- textbox "Email Address":
  - /placeholder: name@example.com
  - text: test@example.com
- text: Password
- link "Forgot Password?":
  - /url: /forgot-password
- textbox "Password":
  - /placeholder: ••••••••
  - text: password123
- button "Signing in..." [disabled]
- text: OR
- button "Sign in with Google. Opens in new tab":
  - img
  - text: Sign in with Google
- iframe
- paragraph:
  - text: New to MovieMind?
  - link "Sign up now":
    - /url: /signup
- button:
  - img
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Authentication Flow', () => {
  4  |   test('User can signup successfully', async ({ page }) => {
  5  |     await page.goto('/signup');
  6  |     await page.getByLabel(/Full Name/i).fill('E2E User');
  7  |     await page.getByLabel(/Email Address/i).fill(`e2e_${Date.now()}@example.com`);
  8  |     await page.getByLabel(/Password/i).fill('Password123!');
  9  |     await page.getByLabel(/Mobile Number/i).fill('1234567890');
  10 |     await page.click('button[type="submit"]');
  11 |     
  12 |     // Should be redirected to home or see success message
  13 |     await expect(page).toHaveURL('/');
  14 |     await expect(page.locator('nav')).toContainText('E2E User');
  15 |   });
  16 | 
  17 |   test('User can login successfully', async ({ page }) => {
  18 |     await page.goto('/login');
  19 |     await page.getByLabel(/Email Address/i).fill('test@example.com');
  20 |     await page.getByLabel(/Password/i).fill('password123');
  21 |     await page.click('button[type="submit"]');
  22 |     
> 23 |     await expect(page).toHaveURL('/');
     |                        ^ Error: expect(page).toHaveURL(expected) failed
  24 |   });
  25 | 
  26 |   test('Logout works', async ({ page }) => {
  27 |     // Login first
  28 |     await page.goto('/login');
  29 |     await page.getByLabel(/Email Address/i).fill('test@example.com');
  30 |     await page.getByLabel(/Password/i).fill('password123');
  31 |     await page.click('button[type="submit"]');
  32 |     
  33 |     await expect(page).toHaveURL('/');
  34 |     
  35 |     // Click avatar to open profile menu
  36 |     await page.click('[data-testid="navbar-avatar"]');
  37 |     
  38 |     // Click logout in dropdown
  39 |     await page.click('button:has-text("Logout")');
  40 |     await expect(page.locator('nav')).toContainText('Login');
  41 |   });
  42 | });
  43 | 
```