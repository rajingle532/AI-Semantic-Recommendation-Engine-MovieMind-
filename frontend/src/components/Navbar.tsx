import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, User, LogOut, Film, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import styles from './Navbar.module.css';

const Navbar: React.FC = () => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const { user, logout, isAuthenticated, loading } = useAuth();
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
    <nav className={styles.navbar}>
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

          {showDropdown && suggestions.length > 0 && (
            <div className={styles.searchSuggestions}>
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
            </div>
          )}
        </div>

        <div className={styles.actions}>
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
              
              {showDropdown && (
                <div className={styles.dropdown}>
                  <Link to="/profile" onClick={() => setShowDropdown(false)}>
                    <User size={16} /> Profile
                  </Link>
                  <button onClick={() => { logout(); setShowDropdown(false); }}>
                    <LogOut size={16} /> Logout
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className={styles.authBtns}>
              <Link to="/login" className={styles.loginBtn}>Login</Link>
              <Link to="/signup" className={styles.signupBtn}>Sign Up</Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;

