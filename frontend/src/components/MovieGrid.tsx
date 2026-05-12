import React from 'react';
import { Movie } from '../types';
import MovieCard from './MovieCard';
import Skeleton from './Skeleton';
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
  if (loading) {
    return (
      <div className={styles.grid}>
        {[...Array(10)].map((_, i) => (
          <div key={i} style={{ aspectRatio: '2/3' }}>
            <Skeleton width="100%" height="100%" borderRadius="12px" />
          </div>
        ))}
      </div>
    );
  }

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
