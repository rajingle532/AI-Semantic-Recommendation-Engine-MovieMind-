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
  const [imageError, setImageError] = React.useState(false);
  const placeholderUrl = 'https://images.unsplash.com/photo-1485846234645-a62644f84728?q=80&w=2059&auto=format&fit=crop';
  const posterUrl = !imageError && movie.poster_path ? movie.poster_path : placeholderUrl;
  const movieId = movie.id || (movie as any).movie_id;
  const movieTitle = movie.title || (movie as any).movie_title || (movie as any).name;
  const mediaType = movie.media_type || 'movie';
  const basePath = mediaType === 'tv' ? '/tv' : '/movie';

  return (
    <motion.div 
      className={styles.card}
      data-testid="movie-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ 
        scale: 1.05,
        y: -10,
        boxShadow: '0 20px 40px rgba(0,0,0,0.4)'
      }}
      transition={{ 
        type: 'spring',
        stiffness: 300,
        damping: 20
      }}
    >
      <Link to={`${basePath}/${movieId}`} className={styles.link}>
        <div className={styles.posterWrapper}>
          {mediaType === 'tv' && (
            <div className={styles.tvBadge}>TV</div>
          )}
          <img 
            src={posterUrl} 
            alt={movieTitle} 
            className={styles.poster} 
            loading="lazy" 
            onError={() => setImageError(true)}
          />
          <div className={styles.overlay}>
            <motion.button 
              className={styles.viewBtn}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              View Details
            </motion.button>
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
