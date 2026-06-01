import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Search, LogOut, Film, Sun, Moon, Shield, HelpCircle, Headphones, Tv, Zap, Users, Ticket } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import api from '../services/api';
import NotificationPanel from './NotificationPanel';
import styles from './Navbar.module.css';

// Pages where full navbar (search, nav links, profile) should be hidden
const AUTH_ONLY_PATHS = ['/login', '/signup', '/forgot-password', '/reset-password'];

const Navbar: React.FC = () => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchSuggestions, setShowSearchSuggestions] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  const searchRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);

  const { user, logout, isAuthenticated, loading } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  // Is this a pure auth page? If so, hide nav/search/profile
  const isAuthPage = AUTH_ONLY_PATHS.includes(location.pathname);


  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSearchSuggestions(false);
      }
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setShowProfileMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchSuggestions = async (val: string) => {
    if (val.length < 2) {
      setSuggestions([]);
      return;
    }
    setIsSearching(true);
    try {
      const { data } = await api.get(`/movies/search?q=${encodeURIComponent(val)}`);
      setSuggestions((data.results || []).slice(0, 6));
    } catch (err) {
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    fetchSuggestions(val);
    setShowSearchSuggestions(true);
  };

  // Only hide navbar entirely during loading if we're NOT on an auth page
  if (loading && !isAuthPage) return null;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query)}`);
      setShowSearchSuggestions(false);
    }
  };

  const handleSuggestionClick = (id: number) => {
    navigate(`/movie/${id}`);
    setQuery('');
    setSuggestions([]);
    setShowSearchSuggestions(false);
  };

  return (
    <motion.nav
      className={styles.navbar}
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: 'spring', stiffness: 120, damping: 20 }}
    >
      <div className={`${styles.container} container`}>
        <Link to="/" className={styles.logo}>
          <img src="/logo.png" alt="MovieMind Logo" style={{ width: '28px', height: '28px', borderRadius: '4px' }} />
          <span>MovieMind</span>
        </Link>

        {isAuthenticated && !isAuthPage && (
          <>
            <div className={styles.mediaToggle}>
              <Link
                to="/"
                className={`${styles.toggleBtn} ${location.pathname === '/' ? styles.active : ''}`}
              >
                <Film size={15} /> Movies
              </Link>
              <Link
                to="/tv"
                className={`${styles.toggleBtn} ${location.pathname.startsWith('/tv') ? styles.active : ''}`}
              >
                <Tv size={15} /> Web Series
              </Link>
              <Link
                to="/cinematch"
                className={`${styles.toggleBtn} ${styles.chipCineMatch} ${location.pathname.startsWith('/cinematch') ? styles.active : ''}`}
              >
                <Zap size={14} style={{ strokeWidth: 2.5 }} /> CineMatch
              </Link>
              <Link
                to="/cineshare"
                className={`${styles.toggleBtn} ${styles.chipCineShare} ${location.pathname.startsWith('/cineshare') ? styles.active : ''}`}
              >
                <Users size={14} style={{ strokeWidth: 2.5 }} /> CineShare
              </Link>
              <Link
                to="/tickets"
                className={`${styles.toggleBtn} ${styles.chipTickets} ${location.pathname.startsWith('/tickets') ? styles.active : ''}`}
              >
                <Ticket size={14} style={{ strokeWidth: 2.5 }} /> Tickets
              </Link>
            </div>

            <div className={styles.searchWrapper} ref={searchRef}>
              <form className={styles.searchBar} onSubmit={handleSearch}>
                <button type="submit" style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer', position: 'absolute', left: '1.1rem', top: '50%', transform: 'translateY(-50%)', zIndex: 10 }}>
                  <Search size={18} className={styles.searchIcon} style={{ position: 'static', transform: 'none' }} />
                </button>
                <input
                  type="text"
                  placeholder="Search movies, actors, or genres..."
                  value={query}
                  onChange={handleInputChange}
                  onFocus={() => query.length >= 2 && setShowSearchSuggestions(true)}
                />
                {isSearching && <div className={styles.searchLoader}></div>}
              </form>

              <AnimatePresence>
                {showSearchSuggestions && suggestions.length > 0 && (
                  <motion.div
                    className={styles.searchSuggestions}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    transition={{ duration: 0.2 }}
                  >
                    {suggestions.map((movie) => (
                      <div
                        key={movie.id}
                        className={styles.suggestionItem}
                        onClick={() => handleSuggestionClick(movie.id)}
                      >
                        <img
                          src={movie.poster_path || 'https://via.placeholder.com/40x60?text=?'}
                          alt={movie.title}
                        />
                        <div className={styles.suggestionInfo}>
                          <p className={styles.suggestionTitle}>{movie.title}</p>
                          <p className={styles.suggestionYear}>
                            {movie.release_date ? movie.release_date.split('-')[0] : 'N/A'}
                          </p>
                        </div>
                      </div>
                    ))}
                    <div
                      className={styles.seeAll}
                      onClick={handleSearch}
                    >
                      See all results for "{query}"
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </>
        )}

        <div className={styles.actions}>
          {/* Smart Notification Bell — only for authenticated users */}
          {isAuthenticated && !isAuthPage && (
            <NotificationPanel
              isOpen={showNotifications}
              onClose={() => setShowNotifications(prev => !prev)}
            />
          )}

          <div
            className={styles.themeTogglePill}
            onClick={toggleTheme}
            title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
          >
            <div className={styles.themeToggleBg} data-theme={theme}></div>
            <div className={`${styles.themeIcon} ${theme === 'light' ? styles.activeIcon : ''}`}>
              <Sun size={14} />
            </div>
            <div className={`${styles.themeIcon} ${theme === 'dark' ? styles.activeIcon : ''}`}>
              <Moon size={14} />
            </div>
          </div>

          {isAuthenticated ? (
            <div className={styles.profileWrapper} ref={profileRef}>
              <div
                style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
                onClick={() => setShowProfileMenu(!showProfileMenu)}
              >
                <span style={{ color: 'var(--text-primary)', fontWeight: '600', fontSize: '0.9rem', whiteSpace: 'nowrap' }}>
                  {user?.name}
                </span>
                <div className={styles.avatar} data-testid="navbar-avatar">
                  {(user?.name ?? "U").charAt(0).toUpperCase()}
                </div>
              </div>

              <AnimatePresence>
                {showProfileMenu && (
                  <motion.div
                    className={styles.dropdown}
                    initial={{ opacity: 0, scale: 0.95, y: -10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: -10 }}
                    transition={{ duration: 0.2 }}
                  >
                    <Link to="/music" onClick={() => setShowProfileMenu(false)}>
                      <Headphones size={16} /> MediaMind Hub
                    </Link>
                    <Link to="/cinematch" onClick={() => setShowProfileMenu(false)} style={{ color: 'var(--accent-primary)', fontWeight: '600' }}>
                      <span style={{ marginRight: '8px' }}>🔥</span> CineMatch Deck
                    </Link>
                    <Link to="/cineshare" onClick={() => setShowProfileMenu(false)} style={{ color: '#6366f1', fontWeight: '600' }}>
                      <span style={{ marginRight: '8px' }}>👥</span> CineShare Party
                    </Link>
                    <Link to="/profile" onClick={() => setShowProfileMenu(false)}>
                      <Film size={16} /> My Library
                    </Link>
                    <Link to="/profile#watchlist" onClick={() => setShowProfileMenu(false)}>
                      <Film size={16} /> My Watchlist
                    </Link>
                    <Link to="/account" onClick={() => setShowProfileMenu(false)}>
                      <Shield size={16} /> Account Details
                    </Link>
                    <Link to="/help" onClick={() => setShowProfileMenu(false)}>
                      <HelpCircle size={16} /> Help
                    </Link>
                    <div className={styles.divider}></div>
                    <button onClick={() => {
                      logout();
                      setShowProfileMenu(false);
                      navigate('/login');
                    }}>
                      <LogOut size={16} /> Logout
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : (
            <div className={styles.authBtns}>
              <Link to="/login" className={styles.loginBtn}>Login</Link>
              <Link to="/signup" className={styles.signupBtn}>Sign Up</Link>
            </div>
          )}
        </div>
      </div>
    </motion.nav>
  );
};

export default Navbar;
