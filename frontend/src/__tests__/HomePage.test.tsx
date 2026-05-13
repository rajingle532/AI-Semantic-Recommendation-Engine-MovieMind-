import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import HomePage from '../pages/HomePage';
import { AuthContext } from '../context/AuthContext';
import { ThemeContext } from '../context/ThemeContext';
import { vi, describe, test, expect } from 'vitest';
import api from '../services/api';

vi.mock('../services/api');

const mockAuthContext = {
  user: null,
  token: null,
  login: vi.fn(),
  logout: vi.fn(),
  loading: false,
  isAuthenticated: false,
};

const mockThemeContext = {
  theme: 'dark' as const,
  toggleTheme: vi.fn(),
};

describe('HomePage Component', () => {
  test('movies load on mount', async () => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes('/movies/genres')) {
        return Promise.resolve({ data: { genres: [] } });
      }
      if (url.includes('/movies/trending')) {
        return Promise.resolve({
          data: {
            results: [{ id: 1, title: 'Trending Movie', poster_path: '/p.jpg' }],
          },
        });
      }
      if (url.includes('/movies/')) {
        return Promise.resolve({ data: { id: 1, title: 'Trending Movie', overview: 'Test Overview' } });
      }
      return Promise.resolve({ data: { results: [] } });
    });

    render(
      <AuthContext.Provider value={mockAuthContext}>
        <ThemeContext.Provider value={mockThemeContext}>
          <BrowserRouter>
            <HomePage />
          </BrowserRouter>
        </ThemeContext.Provider>
      </AuthContext.Provider>
    );

    screen.debug();
    await waitFor(async () => {
      const elements = await screen.findAllByText(/Trending Movie/i);
      expect(elements.length).toBeGreaterThan(0);
    }, { timeout: 3000 });
  });
});
