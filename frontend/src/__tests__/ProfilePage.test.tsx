import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProfilePage from '../pages/ProfilePage';
import { AuthContext } from '../context/AuthContext';
import { ThemeContext } from '../context/ThemeContext';
import { vi, describe, test, expect } from 'vitest';
import api from '../services/api';

vi.mock('../services/api');

const mockUser = {
  id: '1',
  name: 'John Doe',
  email: 'john@example.com',
};

const mockAuthContext = {
  user: mockUser,
  token: 'mock-token',
  login: vi.fn(),
  logout: vi.fn(),
  loading: false,
  isAuthenticated: true,
};

const mockThemeContext = {
  theme: 'dark' as const,
  toggleTheme: vi.fn(),
};

describe('ProfilePage Component', () => {
  test('shows user name and email', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { watchlist: [], ratings: [], recommendations: [] } });

    render(
      <AuthContext.Provider value={mockAuthContext}>
        <ThemeContext.Provider value={mockThemeContext}>
          <BrowserRouter>
            <ProfilePage />
          </BrowserRouter>
        </ThemeContext.Provider>
      </AuthContext.Provider>
    );

    screen.debug();
    await waitFor(async () => {
      const nameElements = await screen.findAllByText(/John Doe/i);
      const emailElements = await screen.findAllByText(/john@example.com/i);
      expect(nameElements.length).toBeGreaterThan(0);
      expect(emailElements.length).toBeGreaterThan(0);
    });
  });
});
