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
  const movieId = movie.id || (movie as any).movie_id;
  const movieTitle = movie.title || (movie as any).movie_title || (movie as any).name || '?';
  const mediaType = movie.media_type || 'movie';
  const basePath = mediaType === 'tv' ? '/tv' : '/movie';

  // Dynamic per-movie placeholder — unique color per movie ID, shows title initial
  const colors = ['#e50914','#6366f1','#f59e0b','#10b981','#ec4899','#3b82f6','#8b5cf6'];
  const placeholderColor = colors[(movieId || 0) % colors.length];
  const initial = movieTitle.charAt(0).toUpperCase();
  const placeholderSvg = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='450' viewBox='0 0 300 450'%3E%3Crect width='300' height='450' fill='%23141414'/%3E%3Crect width='300' height='450' fill='${encodeURIComponent(placeholderColor)}' opacity='0.12'/%3E%3Ccircle cx='150' cy='185' r='70' fill='${encodeURIComponent(placeholderColor)}' opacity='0.2'/%3E%3Ctext x='150' y='205' font-family='Arial,sans-serif' font-size='72' font-weight='900' fill='${encodeURIComponent(placeholderColor)}' text-anchor='middle' opacity='0.9'%3E${encodeURIComponent(initial)}%3C/text%3E%3Ctext x='150' y='310' font-family='Arial,sans-serif' font-size='13' fill='%23ffffff' text-anchor='middle' opacity='0.5'%3ENo Poster Available%3C/text%3E%3C/svg%3E`;

  const posterUrl = !imageError && movie.poster_path ? movie.poster_path : placeholderSvg;

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
