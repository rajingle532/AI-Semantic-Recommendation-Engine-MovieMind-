import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import LoginPage from '../pages/LoginPage';
import { AuthContext } from '../context/AuthContext';
import { ThemeContext } from '../context/ThemeContext';
import { vi, describe, test, expect } from 'vitest';

vi.mock('@react-oauth/google', () => ({
  GoogleLogin: ({ onSuccess }: any) => (
    <button onClick={() => onSuccess({ credential: 'mock-token' })}>
      Continue with Google
    </button>
  ),
  GoogleOAuthProvider: ({ children }: any) => children,
}));

vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}));

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

describe('LoginPage Component', () => {
  test('form renders correctly', () => {
    render(
      <AuthContext.Provider value={mockAuthContext}>
        <ThemeContext.Provider value={mockThemeContext}>
          <BrowserRouter>
            <LoginPage />
          </BrowserRouter>
        </ThemeContext.Provider>
      </AuthContext.Provider>
    );
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Password$/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
  });

  test('Google login button present', () => {
    render(
      <AuthContext.Provider value={mockAuthContext}>
        <ThemeContext.Provider value={mockThemeContext}>
          <BrowserRouter>
            <LoginPage />
          </BrowserRouter>
        </ThemeContext.Provider>
      </AuthContext.Provider>
    );
    expect(screen.getByText(/Continue with Google/i)).toBeInTheDocument();
  });
});
