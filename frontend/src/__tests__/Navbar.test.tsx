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
    renderWithRouter(<Navbar />);
    const searchInput = screen.getByPlaceholderText(/Search movies/i);
    fireEvent.change(searchInput, { target: { value: 'Inception' } });
    expect(searchInput).toHaveValue('Inception');
  });
});
