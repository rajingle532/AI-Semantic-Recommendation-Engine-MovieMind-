import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Brain, Search as SearchIcon } from 'lucide-react';
import api from '../services/api';
import { Movie } from '../types';
import MovieGrid from '../components/MovieGrid';
import Loader from '../components/Loader';
import PageTransition from '../components/PageTransition';
import styles from './SearchPage.module.css';

const SearchPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const [results, setResults] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<'title' | 'nlp'>('title');
  const [mediaType, setMediaType] = useState<'all' | 'movie' | 'tv'>('all');

  useEffect(() => {
    const performSearch = async () => {
      if (!query) return;
      setLoading(true);
      try {
        let allResults: Movie[] = [];
        if (mode === 'nlp') {
          const { data } = await api.get(`/movies/semantic?q=${encodeURIComponent(query)}`);
          allResults = data.results || [];
        } else {
          const [moviesRes, tvRes] = await Promise.all([
            (mediaType === 'all' || mediaType === 'movie') ? api.get(`/movies/search?q=${encodeURIComponent(query)}`) : Promise.resolve({ data: { results: [] } }),
            (mediaType === 'all' || mediaType === 'tv') ? api.get(`/tv/search?q=${encodeURIComponent(query)}`) : Promise.resolve({ data: { results: [] } })
          ]);
          allResults = [...(moviesRes.data.results || []), ...(tvRes.data.results || [])];
          
          // Sort by popularity/vote_average if available, or just interleave them
          allResults.sort((a, b) => (b.vote_average || 0) - (a.vote_average || 0));
        }
        setResults(allResults);
      } catch (err) {
        console.error("Search failed", err);
      } finally {
        setLoading(false);
      }
    };

    performSearch();
  }, [query, mode, mediaType]);

  return (
    <PageTransition>
      <div className={`${styles.page} container`}>
        <header className={styles.header}>
          <div className={styles.titleWrapper}>
            <h1 className={styles.title}>Results for "{query}"</h1>
            <p className={styles.subtitle}>Found {results.length} matches</p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', alignItems: 'flex-end' }}>
            <div className={styles.toggleContainer}>
              <button 
                className={`${styles.toggleBtn} ${mediaType === 'all' ? styles.active : ''}`}
                onClick={() => { setMediaType('all'); setMode('title'); }}
              >
                All
              </button>
              <button 
                className={`${styles.toggleBtn} ${mediaType === 'movie' ? styles.active : ''}`}
                onClick={() => setMediaType('movie')}
              >
                Movies
              </button>
              <button 
                className={`${styles.toggleBtn} ${mediaType === 'tv' ? styles.active : ''}`}
                onClick={() => { setMediaType('tv'); setMode('title'); }}
              >
                TV Shows
              </button>
            </div>

            <div className={styles.toggleContainer}>
              <button 
                className={`${styles.toggleBtn} ${mode === 'title' ? styles.active : ''}`}
                onClick={() => setMode('title')}
              >
                <SearchIcon size={16} /> Title Search
              </button>
              <button 
                className={`${styles.toggleBtn} ${mode === 'nlp' ? styles.active : ''}`}
                onClick={() => { setMode('nlp'); setMediaType('movie'); }}
              >
                <Brain size={16} /> NLP Search
              </button>
            </div>
          </div>
        </header>

        {loading ? (
          <Loader />
        ) : (
          <MovieGrid 
            movies={results} 
            emptyMessage={
              mode === 'nlp' 
                ? "Try describing the movie plot more clearly (e.g. 'a hero in space')" 
                : "No movies found with that title."
            } 
          />
        )}
      </div>
    </PageTransition>
  );
};

export default SearchPage;

