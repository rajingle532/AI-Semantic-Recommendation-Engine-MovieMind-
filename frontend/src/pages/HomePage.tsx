import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Info, Play } from 'lucide-react';
import api from '../services/api';
import { Movie } from '../types';
import MovieGrid from '../components/MovieGrid';
import Loader from '../components/Loader';
import PageTransition from '../components/PageTransition';
import MoodSelector from '../components/MoodSelector';
import FilterBar from '../components/FilterBar';
import styles from './HomePage.module.css';

const HomePage: React.FC = () => {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [heroMovie, setHeroMovie] = useState<Movie | null>(null);
  const [heroVideo, setHeroVideo] = useState<string | null>(null);
  const [genres, setGenres] = useState<{id: number, name: string}[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [activeGenre, setActiveGenre] = useState<number | null>(null);
  const [activeLanguage, setActiveLanguage] = useState<string | null>(null);
  const [activeMood, setActiveMood] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    year: '',
    minRating: '0',
    language: 'all'
  });
  const [page, setPage] = useState(1);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [trendingRes, genresRes] = await Promise.all([
          api.get('/movies/trending?page=1'),
          api.get('/movies/genres')
        ]);
        const trendingMovies = trendingRes.data.results || trendingRes.data || [];
        setMovies(trendingMovies);
        if (trendingMovies.length > 0) {
          const firstMovie = trendingMovies[0];
          setHeroMovie(firstMovie);
          
          // Fetch trailer for hero movie
          try {
            const { data: details } = await api.get(`/movies/${firstMovie.id}`);
            if (details.trailer_key) {
              setHeroVideo(details.trailer_key);
            }
          } catch (vErr) {
            console.error("Failed to fetch hero trailer", vErr);
          }
        }
        const genreData = genresRes.data;
        setGenres(Array.isArray(genreData) ? genreData : (genreData.genres || []));
      } catch (err) {
        console.error("Failed to fetch home data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Filter effect
  useEffect(() => {
    const fetchFiltered = async () => {
      if (filters.year || filters.minRating !== '0' || filters.language !== 'all') {
        setLoading(true);
        setActiveMood(null);
        setActiveGenre(null);
        setPage(1);
        try {
          const endpoint = `/movies/all?page=1&language=${filters.language}&year=${filters.year}&min_rating=${filters.minRating}`;
          console.log("DEBUG: Fetching filtered movies from:", endpoint);
          const { data } = await api.get(endpoint);
          setMovies(Array.isArray(data) ? data : (data.results || []));
        } catch (err) {
          console.error("Filter fetch failed", err);
        } finally {
          setLoading(false);
        }
      } else if (page === 1 && !activeMood && !activeGenre) {
         // This handles the reset when filters are cleared
         const fetchTrending = async () => {
           setLoading(true);
           const { data } = await api.get('/movies/trending?page=1');
           setMovies(data.results || data || []);
           setLoading(false);
         };
         fetchTrending();
      }
    };
    fetchFiltered();
  }, [filters]);

  const loadMore = async () => {
    setLoadingMore(true);
    const nextPage = page + 1;
    try {
      if (activeMood) {
        const { data } = await api.get(`/movies/mood/${activeMood}?page=${nextPage}`);
        const newMovies = Array.isArray(data) ? data : (data.results || []);
        setMovies(prev => [...prev, ...newMovies]);
      } else if (filters.year || filters.minRating !== '0' || filters.language !== 'all') {
        const endpoint = `/movies/all?page=${nextPage}&language=${filters.language}&year=${filters.year}&min_rating=${filters.minRating}`;
        const { data } = await api.get(endpoint);
        const newMovies = Array.isArray(data) ? data : (data.results || []);
        setMovies(prev => [...prev, ...newMovies]);
      } else if (activeGenre) {
        const { data } = await api.get(`/movies/genre/${activeGenre}?page=${nextPage}`);
        const newMovies = Array.isArray(data) ? data : (data.results || []);
        setMovies(prev => [...prev, ...newMovies]);
      } else {
        const { data } = await api.get(`/movies/trending?page=${nextPage}`);
        const newMovies = data.results || data || [];
        setMovies(prev => [...prev, ...newMovies]);
      }
      setPage(nextPage);
    } catch (err) {
      console.error("Failed to load more", err);
    } finally {
      setLoadingMore(false);
    }
  };

  const handleMoodSelect = async (mood: string) => {
    if (!mood) {
      resetTrending();
      return;
    }
    setLoading(true);
    setActiveMood(mood);
    setActiveGenre(null);
    setActiveLanguage(null);
    setPage(1);
    try {
      const { data } = await api.get(`/movies/mood/${mood}`);
      const moviesData = Array.isArray(data) ? data : (data.results || []);
      setMovies(moviesData);
    } catch (err) {
      console.error("Failed to fetch mood movies", err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenreClick = async (genreId: number) => {
    setLoading(true);
    setActiveGenre(genreId);
    setActiveLanguage(null);
    setActiveMood(null);
    setPage(1);
    try {
      const { data } = await api.get(`/movies/genre/${genreId}`);
      const movies = Array.isArray(data) ? data : (data.results || []);
      setMovies(movies);
    } catch (err) {
      console.error("Failed to fetch genre movies", err);
    } finally {
      setLoading(false);
    }
  };

  const resetTrending = async () => {
    setFilters({ year: '', minRating: '0', language: 'all' });
    setLoading(true);
    setActiveGenre(null);
    setActiveMood(null);
    setPage(1);
    try {
      const { data } = await api.get('/movies/trending?page=1');
      setMovies(data.results || data || []);
    } catch (err) {
      console.error("Failed to fetch trending", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && movies.length === 0) return <Loader />;

  return (
    <PageTransition>
      <div className={styles.home}>
        {heroMovie && !activeGenre && !activeMood && filters.language === 'all' && !filters.year && filters.minRating === '0' && (
          <section className={styles.hero}>
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
                <img src={heroMovie.poster_path || ''} alt={heroMovie.title} />
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
                <button className={styles.playBtn}>
                  <Play size={20} fill="currentColor" /> Play
                </button>
                <button className={styles.infoBtn}>
                  <Info size={20} /> More Info
                </button>
              </div>
            </div>
          </section>
        )}

        <main className={`${styles.main} container`}>
          <MoodSelector activeMood={activeMood} onMoodSelect={handleMoodSelect} />

          <div className={styles.genreStrip}>
            <button
              className={`${styles.genreChip} ${activeGenre === null && filters.language === 'all' && !filters.year && filters.minRating === '0' && activeMood === null ? styles.chipActive : ''}`}
              onClick={resetTrending}
            >
              Trending
            </button>
            {genres.map((genre) => (
              <button
                key={genre.id}
                className={`${styles.genreChip} ${activeGenre === genre.id ? styles.chipActive : ''}`}
                onClick={() => handleGenreClick(genre.id)}
              >
                {genre.name}
              </button>
            ))}
          </div>

          <FilterBar 
            filters={filters} 
            setFilters={setFilters} 
            onClear={() => setFilters({ year: '', minRating: '0', language: 'all' })} 
          />

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
            {loading ? <Loader /> : <MovieGrid movies={movies} />}
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
