import React from 'react';
import { Movie } from '../types';
import MovieCard from './MovieCard';
import Loader from './Loader';
import styles from './MovieGrid.module.css';

interface MovieGridProps {
  movies: Movie[];
  loading?: boolean;
  emptyMessage?: string;
}

const MovieGrid: React.FC<MovieGridProps> = ({ 
  movies, 
  loading = false, 
  emptyMessage = "No movies found." 
}) => {
  if (loading) return <Loader />;

  if (movies.length === 0) {
    return <div className={styles.empty}>{emptyMessage}</div>;
  }

  return (
    <div className={styles.grid}>
      {Array.isArray(movies) && movies.map((movie, index) => (
        <MovieCard key={`${movie.id}-${index}`} movie={movie} />
      ))}
    </div>
  );
};

export default MovieGrid;
