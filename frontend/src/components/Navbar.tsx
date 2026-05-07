import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, User, LogOut, Film, Loader2, Sun, Moon } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import api from '../services/api';
import styles from './Navbar.module.css';

const Navbar: React.FC = () => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const { user, logout, isAuthenticated, loading } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const fetchSuggestions = async (val: string) => {
    if (val.length < 2) {
      setSuggestions([]);
      return;
    }
    setIsSearching(true);
    try {
      const { data } = await api.get(`/movies/search?q=${encodeURIComponent(val)}`);
      setSuggestions((data.results || []).slice(0, 6)); // Show top 6
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
    setShowDropdown(true);
  };

  if (loading) return null;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query)}`);
      setShowDropdown(false);
    }
  };

  const handleSuggestionClick = (id: number) => {
    navigate(`/movie/${id}`);
    setQuery('');
    setSuggestions([]);
    setShowDropdown(false);
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

        <div className={styles.searchWrapper}>
          <form className={styles.searchBar} onSubmit={handleSearch}>
            <Search size={18} className={styles.searchIcon} />
            <input
              type="text"
              placeholder="Search movies, actors, or genres..."
              value={query}
              onChange={handleInputChange}
              onFocus={() => query.length >= 2 && setShowDropdown(true)}
            />
            {isSearching && <div className={styles.searchLoader}></div>}
          </form>

          <AnimatePresence>
            {showDropdown && suggestions.length > 0 && (
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
            <div className={styles.profileWrapper}>
              <div 
                style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
                onClick={() => setShowDropdown(!showDropdown)}
              >
                <span style={{ color: 'var(--text-primary)', fontWeight: '600', fontSize: '0.9rem' }}>
                  {user?.name}
                </span>
                <div className={styles.avatar}>
                  {(user?.name ?? "U").charAt(0).toUpperCase()}
                </div>
              </div>
              
              <AnimatePresence>
                {showDropdown && (
                  <motion.div 
                    className={styles.dropdown}
                    initial={{ opacity: 0, scale: 0.95, y: -10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: -10 }}
                    transition={{ duration: 0.2 }}
                  >
                    <Link to="/profile" onClick={() => setShowDropdown(false)}>
                      <User size={16} /> Profile
                    </Link>
                    <button onClick={() => { logout(); setShowDropdown(false); }}>
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
