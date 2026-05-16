import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, User, LogOut, Film, Sun, Moon, Shield, HelpCircle, Headphones } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import api from '../services/api';
import styles from './Navbar.module.css';

const Navbar: React.FC = () => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchSuggestions, setShowSearchSuggestions] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  const searchRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);

  const { user, logout, isAuthenticated, loading } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = window.location;

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

  if (loading) return null;

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
          <Film size={28} className={styles.logoIcon} />
          <span>MovieMind</span>
        </Link>

        <div className={styles.mediaToggle}>
          <Link to="/" className={`${styles.toggleBtn} ${location.pathname === '/' ? styles.active : ''}`}>🎬 Movies</Link>
          <Link to="/tv" className={`${styles.toggleBtn} ${location.pathname.startsWith('/tv') ? styles.active : ''}`}>📺 Web Series</Link>
        </div>

        <div className={styles.searchWrapper} ref={searchRef}>
          <form className={styles.searchBar} onSubmit={handleSearch}>
            <Search size={18} className={styles.searchIcon} />
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

        <div className={styles.actions}>
          <button
            className={styles.themeToggle}
            onClick={toggleTheme}
            title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
          >
            {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
          </button>

          {isAuthenticated ? (
            <div className={styles.profileWrapper} ref={profileRef}>
              <div
                style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
                onClick={() => setShowProfileMenu(!showProfileMenu)}
              >
                <span style={{ color: 'var(--text-primary)', fontWeight: '600', fontSize: '0.9rem' }}>
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
