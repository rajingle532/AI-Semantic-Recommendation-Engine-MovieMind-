import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Brain, Search as SearchIcon } from 'lucide-react';
import api from '../services/api';
import { Movie } from '../types';
import MovieGrid from '../components/MovieGrid';
import Loader from '../components/Loader';
import styles from './SearchPage.module.css';

const SearchPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const [results, setResults] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<'title' | 'nlp'>('title');

  useEffect(() => {
    const performSearch = async () => {
      if (!query) return;
      setLoading(true);
      try {
        const endpoint = mode === 'nlp' ? '/movies/semantic' : '/movies/search';
        const { data } = await api.get(`${endpoint}?q=${encodeURIComponent(query)}`);
        setResults(data.results || []);
      } catch (err) {
        console.error("Search failed", err);
      } finally {
        setLoading(false);
      }
    };

    performSearch();
  }, [query, mode]);

  return (
    <div className={`${styles.page} container`}>
      <header className={styles.header}>
        <div className={styles.titleWrapper}>
          <h1 className={styles.title}>Results for "{query}"</h1>
          <p className={styles.subtitle}>Found {results.length} matches</p>
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
            onClick={() => setMode('nlp')}
          >
            <Brain size={16} /> NLP Search
          </button>
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
  );
};

export default SearchPage;

