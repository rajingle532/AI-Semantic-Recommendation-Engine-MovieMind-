import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Info, Play } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import api from '../services/api';
import { Movie } from '../types';
import MovieGrid from '../components/MovieGrid';
import Loader from '../components/Loader';
import Skeleton from '../components/Skeleton';
import PageTransition from '../components/PageTransition';
import styles from './HomePage.module.css';

const TVPage: React.FC = () => {
  const [tvShows, setTvShows] = useState<Movie[]>([]);
  const [heroShow, setHeroShow] = useState<Movie | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [activeLanguage, setActiveLanguage] = useState<string>('all');
  const [page, setPage] = useState(1);
  const navigate = useNavigate();

  const languages = [
    { code: 'all', name: 'All' },
    { code: 'hi', name: 'Hindi' },
    { code: 'ko', name: 'Korean' },
    { code: 'en', name: 'English' },
    { code: 'ja', name: 'Japanese' },
    { code: 'ta', name: 'Tamil' },
    { code: 'te', name: 'Telugu' },
    { code: 'es', name: 'Spanish' },
    { code: 'tr', name: 'Turkish' },
    { code: 'zh', name: 'Chinese' }
  ];

  const fetchTVShows = async (pageToLoad: number, language: string, isLoadMore = false) => {
    if (isLoadMore) setLoadingMore(true);
    else setLoading(true);

    try {
      let endpoint = language === 'all' ? `/tv/trending?page=${pageToLoad}` : `/tv/language/${language}?page=${pageToLoad}`;
      const res = await api.get(endpoint);
      const newShows = Array.isArray(res.data) ? res.data : (res.data.results || []);

      setTvShows(prev => {
        const combined = isLoadMore ? [...prev, ...newShows] : newShows;
        const uniqueMap = new Map();
        combined.forEach((m: any) => {
          if (m && m.id && !uniqueMap.has(m.id)) {
            uniqueMap.set(m.id, m);
          }
        });
        const finalShows = Array.from(uniqueMap.values());

        if (pageToLoad === 1 && finalShows.length > 0 && language === 'all') {
          setHeroShow(finalShows[0]);
        }

        return finalShows;
      });
    } catch (err) {
      console.error("Failed to fetch TV shows", err);
      toast.error("Failed to load TV shows");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  useEffect(() => {
    fetchTVShows(1, activeLanguage);
  }, [activeLanguage]);

  const loadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    fetchTVShows(nextPage, activeLanguage, true);
  };

  const handleLanguageClick = (code: string) => {
    setActiveLanguage(code);
    setPage(1);
  };

  return (
    <PageTransition>
      <div className={styles.home}>
        {!heroShow && loading && activeLanguage === 'all' ? (
          <section className={styles.hero}>
            <Skeleton width="100%" height="80vh" borderRadius="0" />
          </section>
        ) : heroShow && activeLanguage === 'all' && (
          <section className={styles.hero}>
            <div className={styles.heroBg}>
              <img src={(heroShow as any).backdrop_path || heroShow.poster_path || ''} alt={heroShow.title} />
              <div className={styles.heroOverlay}></div>
            </div>
            <div className={`${styles.heroContent} container`}>
              <motion.h1
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className={styles.heroTitle}
              >
                {heroShow.title}
              </motion.h1>
              <motion.p
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                className={styles.heroOverview}
              >
                {heroShow.overview}
              </motion.p>
              <div className={styles.heroActions}>
                <button
                  className={styles.playBtn}
                  onClick={() => navigate(`/tv/${heroShow.id}`)}
                >
                  <Play size={20} fill="currentColor" /> Watch
                </button>
                <button
                  className={styles.infoBtn}
                  onClick={() => navigate(`/tv/${heroShow.id}`)}
                >
                  <Info size={20} /> More Info
                </button>
              </div>
            </div>
          </section>
        )}

        <main className={`${styles.main} container`} style={{ marginTop: activeLanguage === 'all' ? '0' : '100px' }}>
          
          {/* Language Filters */}
          <div className={styles.genreStrip} style={{ marginBottom: '2rem' }}>
            {languages.map((lang) => (
              <button
                key={lang.code}
                className={`${styles.genreChip} ${activeLanguage === lang.code ? styles.chipActive : ''}`}
                onClick={() => handleLanguageClick(lang.code)}
              >
                {lang.name}
              </button>
            ))}
          </div>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>
              {activeLanguage === 'all' ? 'Trending Web Series' : `${languages.find(l => l.code === activeLanguage)?.name} Series`}
            </h2>
            <MovieGrid movies={tvShows} loading={loading && tvShows.length === 0} />
          </section>

          {!loading && tvShows.length > 0 && (
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
                {loadingMore ? 'Loading...' : 'Load More Series'}
              </button>
            </div>
          )}
        </main>
      </div>
    </PageTransition>
  );
};

export default TVPage;
