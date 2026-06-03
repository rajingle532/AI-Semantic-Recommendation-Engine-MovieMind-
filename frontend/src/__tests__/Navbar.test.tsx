import { describe, test, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { AuthContext } from '../context/AuthContext';
import { ThemeContext } from '../context/ThemeContext';

vi.mock('../services/api', () => ({
  __esModule: true,
  default: {
    get: vi.fn(),
    post: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}));

// Mock lucide-react using importOriginal so ALL icons (including Clapperboard,
// Sparkles, TrendingUp, Bookmark, etc. used in NotificationPanel) are available.
vi.mock('lucide-react', async (importOriginal) => {
  const actual = await importOriginal<typeof import('lucide-react')>();
  return { ...actual };
});

// Mock NotificationContext so NotificationPanel never tries to fetch from the backend.
vi.mock('../context/NotificationContext', () => ({
  NotificationProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useNotifications: () => ({
    notifications: [],
    unreadCount: 0,
    markAsRead: vi.fn(),
    markAllAsRead: vi.fn(),
    clearNotification: vi.fn(),
    clearAll: vi.fn(),
    addNotification: vi.fn(),
    isLoading: false,
    isBellShaking: false,
    pushPermission: 'default' as NotificationPermission,
    requestPushPermission: vi.fn(),
    nextScheduledTime: null,
  }),
}));

// Mock NotificationPanel itself — keeps Navbar tests focused and avoids
// pulling in the entire notification dependency tree.
vi.mock('../components/NotificationPanel', () => ({
  default: () => <div data-testid="notification-panel-mock" />,
}));

const mockAuthContext: any = {
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

const renderWithRouter = (ui: React.ReactElement, { authProps = mockAuthContext, themeProps = mockThemeContext } = {}) => {
  return render(
    <AuthContext.Provider value={authProps}>
      <ThemeContext.Provider value={themeProps}>
        <BrowserRouter>{ui}</BrowserRouter>
      </ThemeContext.Provider>
    </AuthContext.Provider>
  );
};

describe('Navbar Component', () => {
  test('shows Login/Signup when not authenticated', () => {
    renderWithRouter(<Navbar />);
    expect(screen.getByText(/Login/i)).toBeInTheDocument();
    expect(screen.getByText(/Sign Up/i)).toBeInTheDocument();
  });

  test('shows username when authenticated', () => {
    const authenticatedUser = { ...mockAuthContext, user: { id: '1', name: 'John Doe', email: 'john@example.com' }, isAuthenticated: true };
    renderWithRouter(<Navbar />, { authProps: authenticatedUser });
    expect(screen.getByText(/John Doe/i)).toBeInTheDocument();
  });

  test('search bar works', () => {
    const authenticatedUser = { ...mockAuthContext, isAuthenticated: true };
    renderWithRouter(<Navbar />, { authProps: authenticatedUser });
    const searchInput = screen.getByPlaceholderText(/Search movies/i);
    fireEvent.change(searchInput, { target: { value: 'Inception' } });
    expect(searchInput).toHaveValue('Inception');
  });
});
