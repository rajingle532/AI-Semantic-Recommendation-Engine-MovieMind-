# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: movie.spec.ts >> Movie Details Flow >> Watchlist button works (when logged in)
- Location: e2e\movie.spec.ts:14:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=In Watchlist')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('text=In Watchlist')

```

```yaml
- status: Please login to manage watchlist
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
- img "Inception"
- heading "Inception" [level=1]
- img
- text: "8.4"
- img
- text: 124 min
- img
- text: 2010-07-15 Action Science Fiction Adventure
- heading "Overview" [level=3]
- paragraph: "Cobb, a skilled thief who commits corporate espionage by infiltrating the subconscious of his targets is offered a chance to regain his old life as payment for a task considered to be impossible: \"inception\", the implantation of another person's idea into a target's subconscious."
- paragraph: "Rate this movie:"
- text: ★ ★ ★ ★ ★
- button "Add to Watchlist":
  - img
  - text: Add to Watchlist
- button "Watch Trailer":
  - img
  - text: Watch Trailer
- button "Share":
  - img
  - text: Share
- paragraph: "Watch On:"
- link "Amazon Prime Video":
  - /url: https://www.themoviedb.org/movie/27205-inception/watch?locale=IN?tag=your-affiliate-id
  - img "Amazon Prime Video"
- link "JioHotstar":
  - /url: https://www.themoviedb.org/movie/27205-inception/watch?locale=IN?tag=your-affiliate-id
  - img "JioHotstar"
- link "Amazon Prime Video with Ads":
  - /url: https://www.themoviedb.org/movie/27205-inception/watch?locale=IN?tag=your-affiliate-id
  - img "Amazon Prime Video with Ads"
- heading "Top Cast" [level=2]
- link "Leonardo DiCaprio Leonardo DiCaprio Dom Cobb":
  - /url: /person/6193
  - img "Leonardo DiCaprio"
  - paragraph: Leonardo DiCaprio
  - paragraph: Dom Cobb
- link "Joseph Gordon-Levitt Joseph Gordon-Levitt Arthur":
  - /url: /person/24045
  - img "Joseph Gordon-Levitt"
  - paragraph: Joseph Gordon-Levitt
  - paragraph: Arthur
- link "Ken Watanabe Ken Watanabe Saito":
  - /url: /person/3899
  - img "Ken Watanabe"
  - paragraph: Ken Watanabe
  - paragraph: Saito
- link "Tom Hardy Tom Hardy Eames":
  - /url: /person/2524
  - img "Tom Hardy"
  - paragraph: Tom Hardy
  - paragraph: Eames
- link "Elliot Page Elliot Page Ariadne":
  - /url: /person/27578
  - img "Elliot Page"
  - paragraph: Elliot Page
  - paragraph: Ariadne
- link "Dileep Rao Dileep Rao Yusuf":
  - /url: /person/95697
  - img "Dileep Rao"
  - paragraph: Dileep Rao
  - paragraph: Yusuf
- link "Cillian Murphy Cillian Murphy Robert Fischer, Jr.":
  - /url: /person/2037
  - img "Cillian Murphy"
  - paragraph: Cillian Murphy
  - paragraph: Robert Fischer, Jr.
- link "Tom Berenger Tom Berenger Peter Browning":
  - /url: /person/13022
  - img "Tom Berenger"
  - paragraph: Tom Berenger
  - paragraph: Peter Browning
- link "Marion Cotillard Marion Cotillard Mal Cobb":
  - /url: /person/8293
  - img "Marion Cotillard"
  - paragraph: Marion Cotillard
  - paragraph: Mal Cobb
- link "Pete Postlethwaite Pete Postlethwaite Maurice Fischer":
  - /url: /person/4935
  - img "Pete Postlethwaite"
  - paragraph: Pete Postlethwaite
  - paragraph: Maurice Fischer
- heading "Similar Movies You Might Like" [level=2]
- link "Memento View Details Memento N/A":
  - /url: /movie/77
  - img "Memento"
  - button "View Details"
  - heading "Memento" [level=3]
  - text: N/A
- link "Hesher View Details Hesher N/A":
  - /url: /movie/44835
  - img "Hesher"
  - button "View Details"
  - heading "Hesher" [level=3]
  - text: N/A
- link "Copying Beethoven View Details Copying Beethoven N/A":
  - /url: /movie/1590
  - img "Copying Beethoven"
  - button "View Details"
  - heading "Copying Beethoven" [level=3]
  - text: N/A
- link "Abduction View Details Abduction N/A":
  - /url: /movie/59965
  - img "Abduction"
  - button "View Details"
  - heading "Abduction" [level=3]
  - text: N/A
- link "12 Rounds View Details 12 Rounds N/A":
  - /url: /movie/17134
  - img "12 Rounds"
  - button "View Details"
  - heading "12 Rounds" [level=3]
  - text: N/A
- link "Krrish View Details Krrish N/A":
  - /url: /movie/32740
  - img "Krrish"
  - button "View Details"
  - heading "Krrish" [level=3]
  - text: N/A
- link "Rockaway View Details Rockaway N/A":
  - /url: /movie/20406
  - img "Rockaway"
  - button "View Details"
  - heading "Rockaway" [level=3]
  - text: N/A
- link "RED View Details RED N/A":
  - /url: /movie/39514
  - img "RED"
  - button "View Details"
  - heading "RED" [level=3]
  - text: N/A
- link "Robot & Frank View Details Robot & Frank N/A":
  - /url: /movie/84329
  - img "Robot & Frank"
  - button "View Details"
  - heading "Robot & Frank" [level=3]
  - text: N/A
- link "After Earth View Details After Earth N/A":
  - /url: /movie/82700
  - img "After Earth"
  - button "View Details"
  - heading "After Earth" [level=3]
  - text: N/A
- button:
  - img
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Movie Details Flow', () => {
  4  |   test('Clicking movie opens detail page', async ({ page }) => {
  5  |     await page.goto('/');
  6  |     const firstMovie = page.locator('[data-testid="movie-card"]').first();
  7  |     const movieTitle = await firstMovie.locator('h3').innerText();
  8  |     await firstMovie.click();
  9  |     
  10 |     await expect(page.locator('h1')).toContainText(movieTitle);
  11 |     await expect(page.locator('text=Similar Movies')).toBeVisible();
  12 |   });
  13 | 
  14 |   test('Watchlist button works (when logged in)', async ({ page }) => {
  15 |     // Login
  16 |     await page.goto('/login');
  17 |     await page.fill('input[name="email"]', 'test@example.com');
  18 |     await page.fill('input[name="password"]', 'password123');
  19 |     await page.click('button[type="submit"]');
  20 | 
  21 |     await page.goto('/movie/27205'); // Inception
  22 |     await page.click('text=Add to Watchlist');
> 23 |     await expect(page.locator('text=In Watchlist')).toBeVisible();
     |                                                     ^ Error: expect(locator).toBeVisible() failed
  24 |   });
  25 | });
  26 | 
```