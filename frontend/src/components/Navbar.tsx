import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, User, LogOut, Film } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import styles from './Navbar.module.css';

const Navbar: React.FC = () => {
  const [query, setQuery] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const { user, logout, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();

  if (loading) return null;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query)}`);
      setQuery('');
    }
  };

  return (
    <nav className={styles.navbar}>
      <div className={`${styles.container} container`}>
        <Link to="/" className={styles.logo}>
          <Film size={28} className={styles.logoIcon} />
          <span>MovieMind</span>
        </Link>

        <form className={styles.searchBar} onSubmit={handleSearch}>
          <Search size={18} className={styles.searchIcon} />
          <input
            type="text"
            placeholder="Search movies, actors, or genres..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </form>

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

