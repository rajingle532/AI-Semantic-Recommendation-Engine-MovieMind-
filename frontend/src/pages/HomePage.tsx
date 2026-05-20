import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Info, Play, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import api from '../services/api';
import { Movie } from '../types';
import MovieGrid from '../components/MovieGrid';
import Loader from '../components/Loader';
import Skeleton from '../components/Skeleton';
import PageTransition from '../components/PageTransition';
import MoodSelector from '../components/MoodSelector';
import FilterBar from '../components/FilterBar';
import styles from './HomePage.module.css';

const HomePage: React.FC = () => {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [heroMovie, setHeroMovie] = useState<Movie | null>(null);
  const [heroVideo, setHeroVideo] = useState<string | null>(null);
  const [heroCandidates, setHeroCandidates] = useState<Movie[]>([]);
  const [currentHeroIndex, setCurrentHeroIndex] = useState<number>(0);
  const [genres, setGenres] = useState<{ id: number, name: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [activeGenre, setActiveGenre] = useState<number | null>(null);
  const [activeMood, setActiveMood] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    year: '',
    minRating: '0',
    language: 'all'
  });
  const [page, setPage] = useState(1);
  const [showTrailer, setShowTrailer] = useState(false);

  // Lock scroll when modal is open
  useEffect(() => {
    if (showTrailer) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [showTrailer]);
  const navigate = useNavigate();

  const fetchMovies = async (pageToLoad: number, isLoadMore = false, currentFilters = filters, genre = activeGenre, mood = activeMood) => {
    if (isLoadMore) setLoadingMore(true);
    else setLoading(true);

    try {
      let endpoint = '';
      let params: any = { page: pageToLoad };

      if (mood) {
        endpoint = `/movies/mood/${mood}`;
      } else if (currentFilters.year || currentFilters.minRating !== '0' || currentFilters.language !== 'all') {
        endpoint = '/movies/all';
        params = {
          ...params,
          year: currentFilters.year || null,
          min_rating: currentFilters.minRating !== '0' ? currentFilters.minRating : null,
          language: currentFilters.language === 'all' ? null : currentFilters.language
        };
      } else if (genre) {
        endpoint = `/movies/genre/${genre}`;
      } else {
        endpoint = '/movies/trending';
      }

      const res = await api.get(endpoint, { params });
      let newMovies = Array.isArray(res.data) ? res.data : (res.data.results || []);

      setMovies(prev => {
        const combined = isLoadMore ? [...prev, ...newMovies] : newMovies;
        const uniqueMoviesMap = new Map();
        combined.forEach((m: any) => {
          if (m && m.id && !uniqueMoviesMap.has(m.id)) {
            uniqueMoviesMap.set(m.id, m);
          }
        });
        const finalMovies = Array.from(uniqueMoviesMap.values());

        if (pageToLoad === 1 && finalMovies.length > 0) {
          updateHeroMovie(finalMovies[0]);
        }

        return finalMovies;
      });
    } catch (err) {
      console.error("Failed to fetch movies", err);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const updateHeroMovie = async (movie: Movie) => {
    // Set basic movie info immediately (including backdrop from list if available)
    setHeroMovie(movie);
    
    try {
      // Fetch additional details like trailer_key
      const { data: details } = await api.get(`/movies/${movie.id}`);
      if (details.error) {
        throw new Error(details.error);
      }
      // Merge details with the existing movie object to preserve what we already have
      setHeroMovie(prev => ({ ...prev, ...details }));
      setHeroVideo(details.trailer_key || null);
      return details.trailer_key || null;
    } catch (err) {
      console.error("Failed to fetch hero details", err);
      setHeroVideo(null);
      return null;
    }
  };

  /**
   * Try multiple movies until we find one with a trailer for the hero section.
   * Falls back to the first movie if none have trailers.
   */
  const selectHeroWithTrailer = async (movieList: Movie[]) => {
    // Select the top 12 movies as potential hero candidates to ensure a rich list of choices
    const candidates = [...movieList].slice(0, Math.min(12, movieList.length));
    
    try {
      // Fetch details in parallel to quickly gather working YouTube trailers
      const detailsPromises = candidates.map(async (movie) => {
        try {
          const { data: details } = await api.get(`/movies/${movie.id}`);
          if (details && details.trailer_key) {
            return { ...movie, ...details };
          }
        } catch (e) {
          console.error(`Failed to fetch candidate details for ${movie.title}`, e);
        }
        return null;
      });
      
      const resolved = await Promise.all(detailsPromises);
      const validMovies = resolved.filter(m => m !== null) as Movie[];
      
      if (validMovies.length > 0) {
        setHeroCandidates(validMovies);
        // Start at a random index for variety on every load
        const startIndex = Math.floor(Math.random() * validMovies.length);
        setCurrentHeroIndex(startIndex);
        setHeroMovie(validMovies[startIndex]);
        setHeroVideo((validMovies[startIndex] as any).trailer_key || null);
        console.log(`Hero Carousel initialized with ${validMovies.length} movies. Starting at index ${startIndex}`);
      } else {
        // Fallback: use first movie from list
        setHeroMovie(movieList[0]);
        await updateHeroMovie(movieList[0]);
      }
    } catch (err) {
      console.error("Error setting up hero carousel", err);
      setHeroMovie(movieList[0]);
      await updateHeroMovie(movieList[0]);
    }
  };

  // Automatic Hero Carousel Rotation (15s interval)
  useEffect(() => {
    if (heroCandidates.length <= 1) return;
    
    const rotationInterval = setInterval(() => {
      setCurrentHeroIndex((prevIndex) => {
        const nextIndex = (prevIndex + 1) % heroCandidates.length;
        const nextMovie = heroCandidates[nextIndex];
        
        // Update hero states
        setHeroMovie(nextMovie);
        setHeroVideo((nextMovie as any).trailer_key || null);
        console.log(`Hero Carousel rotating to: "${nextMovie.title}"`);
        
        return nextIndex;
      });
    }, 15000); // Rotate every 15 seconds for a premium, dynamic feel
    
    return () => clearInterval(rotationInterval);
  }, [heroCandidates]);

  const [retryCount, setRetryCount] = useState(0);
  const [backendWaking, setBackendWaking] = useState(false);
  const MAX_RETRIES = 3;
  const RETRY_DELAY_MS = 3000;

  useEffect(() => {
    const initPage = async (attempt = 0) => {
      try {
        setLoading(true);
        if (attempt > 0) {
          setBackendWaking(true);
        }

        const [movieRes, genreRes] = await Promise.all([
          api.get('/movies/trending', { params: { page: 1 } }),
          api.get('/movies/genres')
        ]);
        
        // Handle Genres
        const genreData = genreRes.data;
        setGenres(Array.isArray(genreData) ? genreData : (genreData.genres || []));

        // Handle Movies - Robust list extraction
        const newMovies = Array.isArray(movieRes.data) 
          ? movieRes.data 
          : (movieRes.data.results || movieRes.data.movies || []);
        
        console.log("DEBUG: Fetched movies count:", newMovies.length);
        setMovies(newMovies);
        setBackendWaking(false);
        setRetryCount(0);
        
        if (newMovies.length > 0) {
          // Try to find a hero movie with a trailer available
          await selectHeroWithTrailer(newMovies);
        }
      } catch (err) {
        console.error(`Initial load failed (attempt ${attempt + 1}/${MAX_RETRIES + 1})`, err);
        
        if (attempt < MAX_RETRIES) {
          setRetryCount(attempt + 1);
          setBackendWaking(true);
          console.log(`Retrying in ${RETRY_DELAY_MS / 1000}s... (backend may be waking up)`);
          await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
          return initPage(attempt + 1);
        }
        
        // All retries exhausted
        setBackendWaking(false);
        toast.error("Unable to connect to server. Please refresh the page.");
      } finally {
        setLoading(false);
      }
    };

    initPage();
  }, []);

  const loadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    fetchMovies(nextPage, true);
  };

  const handleMoodSelect = (mood: string) => {
    setActiveMood(mood);
    setActiveGenre(null);
    setFilters({ year: '', minRating: '0', language: 'all' });
    setPage(1);
    fetchMovies(1, false, { year: '', minRating: '0', language: 'all' }, null, mood);
  };

  const handleGenreClick = (genreId: number) => {
    setActiveGenre(genreId);
    setActiveMood(null);
    setFilters({ year: '', minRating: '0', language: 'all' });
    setPage(1);
    fetchMovies(1, false, { year: '', minRating: '0', language: 'all' }, genreId, null);
  };

  const resetTrending = () => {
    setFilters({ year: '', minRating: '0', language: 'all' });
    setActiveGenre(null);
    setActiveMood(null);
    setPage(1);
    fetchMovies(1, false, { year: '', minRating: '0', language: 'all' }, null, null);
  };

  const onFilterChange = (newFilters: any) => {
    setFilters(newFilters);
    setActiveGenre(null);
    setActiveMood(null);
    setPage(1);
    fetchMovies(1, false, newFilters, null, null);
  };

  // We don't return a blocking loader here anymore. 
  // Instead, we show skeletons in the components below.

  return (
    <PageTransition>
      <div className={styles.home}>
        {/* Backend wake-up overlay */}
        {backendWaking && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(0,0,0,0.85)',
            zIndex: 9999,
            gap: '1.5rem',
          }}>
            <Loader />
            <p style={{ color: '#fff', fontSize: '1.3rem', fontWeight: 600 }}>
              Loading MovieMind...
            </p>
            <p style={{ color: '#aaa', fontSize: '0.95rem' }}>
              {retryCount > 0
                ? `Server is waking up — retry ${retryCount}/${MAX_RETRIES}...`
                : 'Connecting to server...'}
            </p>
          </div>
        )}

        {!heroMovie && loading ? (
          <section className={styles.hero}>
            <Skeleton width="100%" height="80vh" borderRadius="0" />
          </section>
        ) : heroMovie && (
          <section className={styles.hero} key={heroMovie.id}>
            <div className={styles.heroBg}>
              {heroVideo ? (
                <div className={styles.videoWrapper}>
                  <iframe
                    src={`https://www.youtube.com/embed/${heroVideo}?autoplay=1&mute=1&controls=0&loop=1&playlist=${heroVideo}&showinfo=0&rel=0&iv_load_policy=3&modestbranding=1`}
                    title="Hero Trailer"
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  ></iframe>
                </div>
              ) : (
                <img src={(heroMovie as any).backdrop_path || heroMovie.poster_path || ''} alt={heroMovie.title} />
              )}
              <div className={styles.heroOverlay}></div>
            </div>
            <div className={`${styles.heroContent} container`}>
              <motion.h1
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className={styles.heroTitle}
              >
                {heroMovie.title}
              </motion.h1>
              <motion.p
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                className={styles.heroOverview}
              >
                {heroMovie.overview}
              </motion.p>
              <div className={styles.heroActions}>
                <button
                  className={styles.playBtn}
                  onClick={() => {
                    if (heroVideo) {
                      setShowTrailer(true);
                    } else {
                      toast.error("Trailer not available for this movie");
                    }
                  }}
                >
                  <Play size={20} fill="currentColor" /> Play
                </button>
                <button
                  className={styles.infoBtn}
                  onClick={() => navigate(`/movie/${heroMovie.id}`)}
                >
                  <Info size={20} /> More Info
                </button>
              </div>
            </div>
          </section>
        )}

        <AnimatePresence>
          {showTrailer && heroVideo && (
            <motion.div
              className={styles.modalBackdrop}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowTrailer(false)}
            >
              <motion.div
                className={styles.modalContent}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                onClick={(e) => e.stopPropagation()}
              >
                <button
                  className={styles.closeModal}
                  onClick={() => setShowTrailer(false)}
                >
                  <X size={40} />
                </button>
                <div className={styles.videoWrapperModal}>
                  <iframe
                    src={`https://www.youtube.com/embed/${heroVideo}?autoplay=1`}
                    title="Hero Trailer Player"
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  ></iframe>
                </div>
                <div style={{ padding: '1rem', textAlign: 'center' }}>
                  <a
                    href={`https://www.youtube.com/watch?v=${heroVideo}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: '#aaa', fontSize: '0.8rem', textDecoration: 'underline' }}
                  >
                    Having trouble? Watch on YouTube
                  </a>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        <main className={`${styles.main} container`}>
          <MoodSelector activeMood={activeMood} onMoodSelect={handleMoodSelect} />

          <div className={styles.genreStrip}>
            <button
              className={`${styles.genreChip} ${activeGenre === null && filters.language === 'all' && !filters.year && filters.minRating === '0' && activeMood === null ? styles.chipActive : ''}`}
              onClick={resetTrending}
            >
              Trending
            </button>
            {Array.isArray(genres) && genres.map((genre) => (
              <button
                key={genre.id}
                className={`${styles.genreChip} ${activeGenre === genre.id ? styles.chipActive : ''}`}
                onClick={() => handleGenreClick(genre.id)}
              >
                {genre.name}
              </button>
            ))}
          </div>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>
              {activeMood
                ? `${activeMood.charAt(0).toUpperCase() + activeMood.slice(1)} Movies`
                : activeGenre
                  ? `${genres.find(g => g.id === activeGenre)?.name} Movies`
                  : filters.year || filters.minRating !== '0' || filters.language !== 'all'
                    ? 'Filtered Results'
                    : 'Trending This Week'}
            </h2>
            <MovieGrid movies={movies} loading={loading && movies.length === 0} />
          </section>

          {!loading && movies.length > 0 && (
            <div style={{ textAlign: 'center', marginTop: '40px', marginBottom: '60px' }}>
              <button
                onClick={loadMore}
                disabled={loadingMore}
                style={{
                  background: '#e50914',
                  color: 'white',
                  border: 'none',
                  padding: '14px 48px',
                  borderRadius: '4px',
                  fontSize: '1rem',
                  fontWeight: '700',
                  cursor: loadingMore ? 'not-allowed' : 'pointer',
                  opacity: loadingMore ? 0.7 : 1,
                  transition: 'all 0.3s ease'
                }}
              >
                {loadingMore ? 'Loading...' : 'Load More Movies'}
              </button>
            </div>
          )}
        </main>
      </div>
    </PageTransition>
  );
};

export default HomePage;
