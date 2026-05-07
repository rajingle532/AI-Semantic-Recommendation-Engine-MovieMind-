import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Info, Play } from 'lucide-react';
import api from '../services/api';
import { Movie } from '../types';
import MovieGrid from '../components/MovieGrid';
import Loader from '../components/Loader';
import PageTransition from '../components/PageTransition';
import MoodSelector from '../components/MoodSelector';
import styles from './HomePage.module.css';

const LANGUAGES = [
  { code: 'all', name: 'All Languages', flag: '🌍' },
  { code: 'hi', name: 'Hindi', flag: '🇮🇳' },
  { code: 'mr', name: 'Marathi', flag: '🟠' },
  { code: 'ta', name: 'Tamil', flag: '🎬' },
  { code: 'te', name: 'Telugu', flag: '🎭' },
  { code: 'ml', name: 'Malayalam', flag: '🌴' },
  { code: 'kn', name: 'Kannada', flag: '⭐' },
  { code: 'bn', name: 'Bengali', flag: '🎪' },
  { code: 'pa', name: 'Punjabi', flag: '💛' },
  { code: 'ko', name: 'Korean', flag: '🌸' },
  { code: 'ja', name: 'Japanese', flag: '🗾' },
  { code: 'fr', name: 'French', flag: '🥐' },
  { code: 'es', name: 'Spanish', flag: '🌮' },
  { code: 'it', name: 'Italian', flag: '🍕' },
  { code: 'de', name: 'German', flag: '🇩🇪' },
  { code: 'zh', name: 'Chinese', flag: '🀄' },
  { code: 'ar', name: 'Arabic', flag: '🌙' },
  { code: 'tr', name: 'Turkish', flag: '🦃' },
  { code: 'ru', name: 'Russian', flag: '❄️' },
  { code: 'pt', name: 'Portuguese', flag: '🌊' },
];

const HomePage: React.FC = () => {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [heroMovie, setHeroMovie] = useState<Movie | null>(null);
  const [genres, setGenres] = useState<{id: number, name: string}[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [activeGenre, setActiveGenre] = useState<number | null>(null);
  const [activeLanguage, setActiveLanguage] = useState<string | null>(null);
  const [activeMood, setActiveMood] = useState<string | null>(null);
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
        if (trendingMovies.length > 0) setHeroMovie(trendingMovies[0]);
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

  const loadMore = async () => {
    setLoadingMore(true);
    const nextPage = page + 1;
    try {
      if (activeMood) {
        const { data } = await api.get(`/movies/mood/${activeMood}?page=${nextPage}`);
        const newMovies = Array.isArray(data) ? data : (data.results || []);
        setMovies(prev => [...prev, ...newMovies]);
      } else if (activeLanguage) {
        const endpoint = activeLanguage === 'all'
          ? `/movies/all?page=${nextPage}`
          : `/movies/language/${activeLanguage}?page=${nextPage}`;
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

  const handleLanguageClick = async (langCode: string) => {
    setLoading(true);
    setActiveLanguage(langCode);
    setActiveGenre(null);
    setActiveMood(null);
    setPage(1);
    try {
      if (langCode === 'all') {
        const { data } = await api.get(`/movies/all?page=1`);
        setMovies(Array.isArray(data) ? data : (data.results || []));
      } else {
        const { data } = await api.get(`/movies/language/${langCode}?page=1`);
        setMovies(Array.isArray(data) ? data : (data.results || []));
      }
    } catch (err) {
      console.error("Failed to fetch language movies", err);
    } finally {
      setLoading(false);
    }
  };

  const resetTrending = async () => {
    setLoading(true);
    setActiveGenre(null);
    setActiveLanguage(null);
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
        {heroMovie && !activeGenre && !activeLanguage && !activeMood && (
          <section className={styles.hero}>
            <div className={styles.heroBg}>
              <img src={heroMovie.poster_path || ''} alt={heroMovie.title} />
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
              className={`${styles.genreChip} ${activeGenre === null && activeLanguage === null && activeMood === null ? styles.chipActive : ''}`}
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

          <div className={styles.genreStrip} style={{ marginTop: '10px' }}>
            {LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                className={`${styles.genreChip} ${activeLanguage === lang.code ? styles.chipActive : ''}`}
                onClick={() => handleLanguageClick(lang.code)}
              >
                {lang.flag} {lang.name}
              </button>
            ))}
          </div>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>
              {activeMood 
                ? `${activeMood.charAt(0).toUpperCase() + activeMood.slice(1)} Movies`
                : activeLanguage 
                  ? `${LANGUAGES.find(l => l.code === activeLanguage)?.name} Movies`
                  : activeGenre
                    ? `${genres.find(g => g.id === activeGenre)?.name} Movies`
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
