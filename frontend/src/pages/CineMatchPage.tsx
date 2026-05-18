import React, { useState, useEffect } from 'react';
import { motion, useMotionValue, useTransform, AnimatePresence } from 'framer-motion';
import { X, Star, Heart, RotateCcw, Compass, Flame } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import PageTransition from '../components/PageTransition';
import styles from './CineMatchPage.module.css';

interface Movie {
  id: number;
  title: string;
  poster_path: string;
  release_date?: string;
  vote_average?: number;
  overview?: string;
}

const CineMatchPage: React.FC = () => {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [ratingMovie, setRatingMovie] = useState<Movie | null>(null);
  const [hoveredStar, setHoveredStar] = useState<number | null>(null);
  const [swipeDirection, setSwipeDirection] = useState<'left' | 'right' | 'up' | null>(null);

  const navigate = useNavigate();

  // Motion Values for dragging top card
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  // Transforms for rotational effect on drag
  const rotate = useTransform(x, [-200, 200], [-25, 25]);
  const opacity = useTransform(x, [-200, -150, 0, 150, 200], [0.5, 0.8, 1, 0.8, 0.5]);

  // Color glow overlays based on drag direction
  const glowBg = useTransform(
    x,
    [-150, 0, 150],
    [
      'radial-gradient(circle at 50% 30%, rgba(255, 75, 43, 0.2) 0%, var(--bg-primary) 100%)',
      'radial-gradient(circle at 50% 30%, rgba(255, 255, 255, 0.02) 0%, var(--bg-primary) 100%)',
      'radial-gradient(circle at 50% 30%, rgba(46, 204, 113, 0.2) 0%, var(--bg-primary) 100%)'
    ]
  );

  // Dynamic badges opacity based on drag position
  const leftBadgeOpacity = useTransform(x, [-120, -40], [1, 0]);
  const rightBadgeOpacity = useTransform(x, [40, 120], [0, 1]);

  const fetchSwipePool = async () => {
    setLoading(true);
    try {
      const res = await api.get('/movies/swipe-pool');
      setMovies(res.data.results || []);
      setCurrentIndex(0);
    } catch (e) {
      console.error('Failed to load swipe candidates', e);
      toast.error('Could not load matches. Please try again!');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSwipePool();
  }, []);

  // Listen to keyboard arrow keys for Tinder swipes!
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (ratingMovie || loading || movies.length === 0 || currentIndex >= movies.length) {
        return;
      }
      if (e.key === 'ArrowLeft') {
        handleSwipeAction('left');
      } else if (e.key === 'ArrowRight') {
        handleSwipeAction('right');
      } else if (e.key === 'ArrowUp') {
        handleSwipeAction('up');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentIndex, movies, ratingMovie, loading]);

  const currentMovie = movies[currentIndex];

  const handleSwipeAction = async (direction: 'left' | 'right' | 'up', ratingValue?: number) => {
    if (!currentMovie) return;

    setSwipeDirection(direction);

    // 1. Perform Backend Mutations
    if (direction === 'right') {
      // Add to watchlist
      try {
        await api.post('/watchlist', {
          movie_id: currentMovie.id,
          movie_title: currentMovie.title,
          poster_path: currentMovie.poster_path,
          release_date: currentMovie.release_date || '',
          vote_average: currentMovie.vote_average || 0.0
        });
        toast.success(`Added ${currentMovie.title} to watchlist! ❤️`);
      } catch (err) {
        console.error(err);
      }
    } else if (direction === 'up' && ratingValue) {
      // Add to ratings
      try {
        await api.post('/ratings', {
          movie_id: currentMovie.id,
          movie_title: currentMovie.title,
          poster_path: currentMovie.poster_path,
          rating: ratingValue,
          review: ''
        });
        toast.success(`Rated ${currentMovie.title} ${ratingValue} stars! ⭐`);
      } catch (err) {
        console.error(err);
      }
    } else if (direction === 'left') {
      toast(`Skipped ${currentMovie.title}`, { icon: '👀' });
    }

    // 2. Animate to next card
    setTimeout(() => {
      setCurrentIndex((prev) => prev + 1);
      setSwipeDirection(null);
      setRatingMovie(null);
      x.set(0);
      y.set(0);
    }, 200);
  };

  const handleDragEnd = (event: any, info: any) => {
    const threshold = 120;
    const swipeX = info.offset.x;
    const swipeY = info.offset.y;

    if (swipeX > threshold) {
      handleSwipeAction('right');
    } else if (swipeX < -threshold) {
      handleSwipeAction('left');
    } else if (swipeY < -threshold) {
      // Swipe Up -> open ratings overlay
      setRatingMovie(currentMovie);
    } else {
      // Reset position
      x.set(0);
      y.set(0);
    }
  };

  const getPosterUrl = (path: string) => {
    if (!path) return 'https://via.placeholder.com/500x750?text=No+Poster';
    if (path.startsWith('http')) return path;
    return `https://image.tmdb.org/t/p/w500${path}`;
  };

  return (
    <PageTransition>
      <motion.div className={styles.container} style={{ background: glowBg }}>
        <div className={styles.header}>
          <h1>
            <Flame size={28} fill="#ff4b2b" style={{ color: '#ff4b2b' }} /> AI CineMatch
          </h1>
          <p>Swipe right to watch, left to skip, and up to rate!</p>
        </div>

        {loading ? (
          <div className={styles.cardContainer}>
            <div className={styles.card} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div className="loader"></div>
            </div>
          </div>
        ) : currentIndex < movies.length ? (
          <>
            <div className={styles.cardContainer}>
              <AnimatePresence>
                {/* ── Background Card Preview ── */}
                {currentIndex + 1 < movies.length && (
                  <motion.div
                    className={styles.card}
                    style={{
                      scale: 0.95,
                      y: 15,
                      zIndex: 5,
                      opacity: 0.7,
                      pointerEvents: 'none'
                    }}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 0.7, scale: 0.95, y: 15 }}
                  >
                    <div className={styles.posterWrapper}>
                      <img
                        className={styles.poster}
                        src={getPosterUrl(movies[currentIndex + 1].poster_path)}
                        alt={movies[currentIndex + 1].title}
                      />
                    </div>
                  </motion.div>
                )}

                {/* ── Active Swiping Card ── */}
                <motion.div
                  key={currentMovie.id}
                  className={`${styles.card} ${styles.cardActive}`}
                  style={{
                    x,
                    y,
                    rotate,
                    opacity,
                    zIndex: 10
                  }}
                  drag
                  dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
                  onDragEnd={handleDragEnd}
                  animate={
                    swipeDirection === 'left'
                      ? { x: -400, opacity: 0 }
                      : swipeDirection === 'right'
                      ? { x: 400, opacity: 0 }
                      : swipeDirection === 'up'
                      ? { y: -400, opacity: 0 }
                      : { x: 0, y: 0 }
                  }
                  transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                >
                  <div className={styles.posterWrapper}>
                    {/* Dynamic Direction Badges */}
                    <motion.div className={`${styles.directionBadge} ${styles.badgeLeft}`} style={{ opacity: leftBadgeOpacity }}>
                      Skip
                    </motion.div>
                    <motion.div className={`${styles.directionBadge} ${styles.badgeRight}`} style={{ opacity: rightBadgeOpacity }}>
                      Watch
                    </motion.div>

                    <img
                      className={styles.poster}
                      src={getPosterUrl(currentMovie.poster_path)}
                      alt={currentMovie.title}
                    />
                    <div className={styles.posterGradient}></div>
                  </div>

                  <div className={styles.info}>
                    <div>
                      <div className={styles.infoTop}>
                        <h2 className={styles.title}>{currentMovie.title}</h2>
                      </div>
                      <div className={styles.yearRating}>
                        <span>{currentMovie.release_date ? currentMovie.release_date.split('-')[0] : 'Release N/A'}</span>
                        {currentMovie.vote_average ? (
                          <span className={styles.ratingTag}>
                            <Star size={12} fill="currentColor" /> {currentMovie.vote_average.toFixed(1)}
                          </span>
                        ) : null}
                      </div>
                    </div>
                    {currentMovie.overview && (
                      <p className={styles.overview}>{currentMovie.overview}</p>
                    )}
                  </div>

                  {/* Rating Selector Modal Overlay */}
                  <AnimatePresence>
                    {ratingMovie && ratingMovie.id === currentMovie.id && (
                      <motion.div
                        className={styles.ratingOverlay}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                      >
                        <h3>Rate {currentMovie.title}</h3>
                        <p>How many stars would you give this movie?</p>
                        
                        <div className={styles.starsRow}>
                          {[1, 2, 3, 4, 5].map((star) => (
                            <button
                              key={star}
                              className={`${styles.starBtn} ${(hoveredStar !== null ? star <= hoveredStar : false) || (hoveredStar === null && false) ? styles.starBtnActive : ''}`}
                              onMouseEnter={() => setHoveredStar(star)}
                              onMouseLeave={() => setHoveredStar(null)}
                              onClick={() => handleSwipeAction('up', star)}
                              style={{ color: (hoveredStar !== null ? star <= hoveredStar : false) ? '#f1c40f' : 'rgba(255,255,255,0.2)' }}
                            >
                              <Star size={32} fill={hoveredStar !== null && star <= hoveredStar ? 'currentColor' : 'none'} />
                            </button>
                          ))}
                        </div>

                        <button className={styles.cancelRate} onClick={() => setRatingMovie(null)}>
                          Cancel
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              </AnimatePresence>
            </div>

            {/* Swiper Controls */}
            <div className={styles.controls}>
              <button
                className={`${styles.controlBtn} ${styles.skipBtn}`}
                onClick={() => handleSwipeAction('left')}
                title="Skip (ArrowLeft)"
              >
                <X size={24} />
              </button>
              <button
                className={`${styles.controlBtn} ${styles.rateBtn}`}
                onClick={() => setRatingMovie(currentMovie)}
                title="Rate Up (ArrowUp)"
                style={{ color: '#f1c40f' }}
              >
                <Star size={28} />
              </button>
              <button
                className={`${styles.controlBtn} ${styles.loveBtn}`}
                onClick={() => handleSwipeAction('right')}
                title="Add to Watchlist (ArrowRight)"
                style={{ color: '#2ecc71' }}
              >
                <Heart size={24} fill="currentColor" />
              </button>
            </div>

            {/* Keyboard shortcuts hints */}
            <div className={styles.keyboardHints}>
              <span className={styles.keyHint}>
                <kbd>←</kbd> Skip
              </span>
              <span className={styles.keyHint}>
                <kbd>↑</kbd> Rate
              </span>
              <span className={styles.keyHint}>
                <kbd>→</kbd> Watchlist
              </span>
            </div>
          </>
        ) : (
          /* Empty/Finished State */
          <motion.div
            className={styles.emptyState}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            <div className={styles.emptyIcon}>🎉</div>
            <h2>Swipe Deck Cleared!</h2>
            <p>You've swiped through all movies in this round! Your taste profile is now super-charged with fresh insights.</p>

            <div className={styles.actionsRow}>
              <button className={styles.primaryBtn} onClick={fetchSwipePool}>
                <RotateCcw size={18} /> Fresh Deck
              </button>
              <button className={styles.secondaryBtn} onClick={() => navigate('/profile#ai')}>
                <Compass size={18} /> See AI Picks
              </button>
            </div>
          </motion.div>
        )}
      </motion.div>
    </PageTransition>
  );
};

export default CineMatchPage;
