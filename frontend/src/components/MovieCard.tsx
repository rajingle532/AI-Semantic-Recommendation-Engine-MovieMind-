import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Star } from 'lucide-react';
import { Movie } from '../types';
import styles from './MovieCard.module.css';

interface MovieCardProps {
  movie: Movie;
  showRating?: boolean;
}

const MovieCard: React.FC<MovieCardProps> = ({ movie, showRating = true }) => {
  // Using direct poster_path as it already contains the full URL
  const posterUrl = movie.poster_path || 'https://via.placeholder.com/500x750?text=No+Poster';

  const movieId = movie.id || (movie as any).movie_id;
  const movieTitle = movie.title || (movie as any).movie_title;

  return (
    <motion.div 
      className={styles.card}
      whileHover={{ scale: 1.05 }}
      transition={{ duration: 0.3 }}
    >
      <Link to={`/movie/${movieId}`} className={styles.link}>
        <div className={styles.posterWrapper}>
          <img src={posterUrl} alt={movieTitle} className={styles.poster} loading="lazy" />
          <div className={styles.overlay}>
            <button className={styles.viewBtn}>View Details</button>
          </div>
        </div>
        
        <div className={styles.info}>
          <h3 className={styles.title} title={movieTitle}>{movieTitle}</h3>
          <div className={styles.meta}>
            <span className={styles.year}>{movie.release_date?.split('-')[0] || 'N/A'}</span>
            {showRating && movie.vote_average !== undefined && (
              <span className={styles.rating}>
                <Star size={12} fill="var(--gold)" color="var(--gold)" />
                {movie.vote_average.toFixed(1)}
              </span>
            )}
          </div>
        </div>
      </Link>
    </motion.div>
  );
};

export default MovieCard;
