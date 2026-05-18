import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Sparkles, AlertCircle, Star, Film } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import PageTransition from '../components/PageTransition';
import styles from './CineSharePage.module.css';

interface SharedGenre {
  name: string;
  percentage: number;
}

interface CommonPick {
  id: number;
  title: string;
  poster_path: string;
  vote_average: number;
  release_date: string;
  genres: string[];
  overlap_score: number;
}

interface CineShareResult {
  compatibility: number;
  friend_name: string;
  friend_email: string;
  shared_genres: SharedGenre[];
  common_picks: CommonPick[];
  my_genre_count: number;
  friend_genre_count: number;
}

const getCompatDesc = (score: number): string => {
  if (score >= 85) return '🔥 Incredible match! You two have an almost identical taste in movies!';
  if (score >= 70) return '✨ Great compatibility! You\'ll find lots of movies you both love.';
  if (score >= 55) return '👍 Good match! You share a solid common ground with some variety.';
  if (score >= 40) return '🎭 Interesting combo! Different tastes, but that makes movie nights exciting!';
  return '🌍 Opposites attract! Your differences could lead to some amazing movie discoveries.';
};

const CineSharePage: React.FC = () => {
  const { user } = useAuth();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<CineShareResult | null>(null);

  const myInitial = (user?.name ?? 'U').charAt(0).toUpperCase();

  const handleMatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const res = await api.post('/recommend/cineshare', { friend_email: email.trim().toLowerCase() });
      setResult(res.data);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Something went wrong. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError('');
    setEmail('');
  };

  return (
    <PageTransition>
      <div className={styles.page}>
        {/* Hero */}
        <div className={styles.heroBanner}>
          <div className={styles.heroBg} />
          <div className={styles.heroIcon}>👥</div>
          <h1 className={styles.heroTitle}>CineShare</h1>
          <p className={styles.heroSubtitle}>
            Enter a friend's email to discover how compatible your movie tastes are — and get AI-picked films you'll both love!
          </p>
        </div>

        {/* Input Card */}
        <div className={styles.inputSection}>
          <div className={styles.inputCard}>
            <label className={styles.inputLabel}>Friend's MovieMind Email</label>
            <form className={styles.inputRow} onSubmit={handleMatch}>
              <input
                id="cineshare-email-input"
                type="email"
                className={styles.emailInput}
                placeholder="friend@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                disabled={loading}
                autoComplete="email"
              />
              <button
                id="cineshare-match-btn"
                type="submit"
                className={styles.matchBtn}
                disabled={loading || !email.trim()}
              >
                <Sparkles size={16} />
                {loading ? 'Matching...' : 'Match!'}
              </button>
            </form>
            <AnimatePresence>
              {error && (
                <motion.div
                  className={styles.errorMsg}
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                >
                  <AlertCircle size={15} />
                  {error}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Loading */}
        <AnimatePresence>
          {loading && (
            <motion.div
              className={styles.loadingState}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
            >
              <div className={styles.loadingOrb}>🧠</div>
              <p className={styles.loadingText}>AI is analyzing both taste profiles...</p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results */}
        <AnimatePresence>
          {result && !loading && (
            <motion.div
              className={styles.results}
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
            >
              {/* Compatibility Hero Card */}
              <div className={styles.compatCard}>
                <div className={styles.compatBg} />
                <div className={styles.compatPair}>
                  <div className={styles.compatAvatar}>{myInitial}</div>
                  <div className={styles.compatHeart}>💜</div>
                  <div className={styles.compatAvatar}>
                    {result.friend_name.charAt(0).toUpperCase()}
                  </div>
                </div>
                <div className={styles.compatLabel}>Taste Compatibility</div>
                <div className={styles.compatScoreWrapper}>
                  <span className={styles.compatScore}>{result.compatibility}%</span>
                </div>
                <p className={styles.compatDesc}>{getCompatDesc(result.compatibility)}</p>
                <div className={styles.compatBarWrapper}>
                  <div className={styles.compatBarTrack}>
                    <motion.div
                      className={styles.compatBarFill}
                      initial={{ width: 0 }}
                      animate={{ width: `${result.compatibility}%` }}
                      transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
                    />
                  </div>
                </div>
              </div>

              {/* Genre Overlap + Tip */}
              <div className={styles.grid2}>
                {/* Shared Genres */}
                <div className={styles.infoCard}>
                  <div className={styles.cardHeader}>
                    <Sparkles size={15} style={{ color: '#6366f1' }} />
                    Shared Genre DNA
                  </div>
                  {result.shared_genres.length > 0 ? (
                    result.shared_genres.map((g) => (
                      <div key={g.name} className={styles.genreBar}>
                        <div className={styles.genreBarLabel}>
                          <span>{g.name}</span>
                          <span style={{ color: '#6366f1' }}>{g.percentage}%</span>
                        </div>
                        <div className={styles.genreBarTrack}>
                          <motion.div
                            className={styles.genreBarFill}
                            initial={{ width: 0 }}
                            animate={{ width: `${g.percentage}%` }}
                            transition={{ duration: 0.8, ease: 'easeOut' }}
                          />
                        </div>
                      </div>
                    ))
                  ) : (
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                      Not enough data yet — rate more movies to reveal shared genres!
                    </p>
                  )}
                </div>

                {/* Match Details */}
                <div className={styles.infoCard}>
                  <div className={styles.cardHeader}>
                    <Users size={15} style={{ color: '#ec4899' }} />
                    Match Details
                  </div>
                  <div className={styles.tipBox}>
                    <span className={styles.tipIcon}>👤</span>
                    <span>
                      <strong style={{ color: 'var(--text-primary)' }}>You</strong> —{' '}
                      {result.my_genre_count} genre signals from your library.
                    </span>
                  </div>
                  <div className={styles.tipBox} style={{ marginTop: '14px' }}>
                    <span className={styles.tipIcon}>🤝</span>
                    <span>
                      <strong style={{ color: 'var(--text-primary)' }}>{result.friend_name}</strong> —{' '}
                      {result.friend_genre_count} genre signals from their library.
                    </span>
                  </div>
                  <div className={styles.tipBox} style={{ marginTop: '14px' }}>
                    <span className={styles.tipIcon}>💡</span>
                    <span>
                      Rate more movies to improve the accuracy of your compatibility score!
                    </span>
                  </div>
                </div>
              </div>

              {/* Common Movie Picks */}
              <div className={styles.picksSection}>
                <div className={styles.picksSectionHeader}>
                  <Film size={15} style={{ color: '#f59e0b' }} />
                  🍿 Tonight's Watch Party Picks — Perfect for Both of You
                </div>
                {result.common_picks.length > 0 ? (
                  <div className={styles.picksGrid}>
                    {result.common_picks.map((movie, i) => (
                      <motion.div
                        key={movie.id}
                        initial={{ opacity: 0, y: 16 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.05 }}
                      >
                        <Link to={`/movie/${movie.id}`} style={{ textDecoration: 'none' }}>
                          <div className={styles.movieCard}>
                            {movie.overlap_score > 0 && (
                              <div className={styles.matchBadge}>✓ MATCH</div>
                            )}
                            {movie.poster_path ? (
                              <img
                                src={movie.poster_path}
                                alt={movie.title}
                                className={styles.moviePoster}
                              />
                            ) : (
                              <div className={styles.moviePosterPlaceholder}>🎬</div>
                            )}
                            <div className={styles.movieInfo}>
                              <div className={styles.movieTitle}>{movie.title}</div>
                              <div className={styles.movieMeta}>
                                <Star size={11} className={styles.movieRating} />
                                <span className={styles.movieRating}>
                                  {movie.vote_average?.toFixed(1) || '—'}
                                </span>
                                {movie.release_date && (
                                  <span>· {movie.release_date.split('-')[0]}</span>
                                )}
                              </div>
                            </div>
                          </div>
                        </Link>
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '30px' }}>
                    No common picks found yet. Both of you should rate more movies!
                  </div>
                )}
              </div>

              {/* Try Again */}
              <div style={{ textAlign: 'center', marginTop: '36px' }}>
                <button
                  onClick={handleReset}
                  className={styles.matchBtn}
                  style={{ margin: '0 auto' }}
                  id="cineshare-reset-btn"
                >
                  <Users size={16} /> Try Another Friend
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Idle / Empty State */}
        {!result && !loading && (
          <div className={styles.idleState}>
            <div className={styles.idleIcon}>🎬</div>
            <h2 className={styles.idleTitle}>Find Your Movie Soulmate</h2>
            <p className={styles.idleDesc}>
              Enter a friend's email above to get started. Both of you need a MovieMind account for this to work!
            </p>
            <div className={styles.idleSteps}>
              <div className={styles.idleStep}>
                <div className={styles.idleStepNum}>1</div>
                <div className={styles.idleStepText}>Enter your friend's MovieMind email address</div>
              </div>
              <div className={styles.idleStep}>
                <div className={styles.idleStepNum}>2</div>
                <div className={styles.idleStepText}>AI analyzes both your taste profiles and calculates compatibility</div>
              </div>
              <div className={styles.idleStep}>
                <div className={styles.idleStepNum}>3</div>
                <div className={styles.idleStepText}>Get a curated Watch Party list perfect for both of you tonight!</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </PageTransition>
  );
};

export default CineSharePage;
