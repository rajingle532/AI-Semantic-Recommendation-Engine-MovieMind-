import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Plus, Check, Star, Clock, Calendar, Play } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';
import { Movie } from '../types';
import MovieGrid from '../components/MovieGrid';
import Loader from '../components/Loader';
import RatingStars from '../components/RatingStars';
import PageTransition from '../components/PageTransition';
import styles from './MovieDetailPage.module.css';

const MovieDetailPage: React.FC = () => {
  const { id } = useParams();
  const [movie, setMovie] = useState<Movie | null>(null);
  const [similar, setSimilar] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [inWatchlist, setInWatchlist] = useState(false);
  const [userRating, setUserRating] = useState(0);
  const [showTrailer, setShowTrailer] = useState(false);

  useEffect(() => {
    const fetchMovieData = async () => {
      setLoading(true);
      try {
        const [detailsRes, similarRes, watchlistRes, ratingsRes] = await Promise.all([
          api.get(`/movies/${id}`),
          api.get(`/recommend/${id}`).catch(() => ({ data: [] })),
          api.get('/watchlist/my').catch(() => ({ data: { watchlist: [] } })),
          api.get('/ratings/my').catch(() => ({ data: { ratings: [] } }))
        ]);
        
        setMovie(detailsRes.data);
        setSimilar(similarRes.data.recommendations || []);
        
        const watchlist = watchlistRes.data.watchlist || [];
        setInWatchlist(watchlist.some((m: any) => m.movie_id === parseInt(id!)));

        const ratings = ratingsRes.data.ratings || [];
        const existingRating = ratings.find((r: any) => r.movie_id === parseInt(id!));
        if (existingRating) {
          setUserRating(existingRating.rating);
        }
      } catch (err) {
        toast.error("Failed to load movie details");
      } finally {
        setLoading(false);
      }
    };

    fetchMovieData();
    window.scrollTo(0, 0);
  }, [id]);

  const toggleWatchlist = async () => {
    if (!movie) return;
    try {
      if (inWatchlist) {
        await api.delete(`/watchlist/${id}`);
        setInWatchlist(false);
        toast.success("Removed from watchlist");
      } else {
        await api.post('/watchlist/', { 
          movie_id: movie.id,
          movie_title: movie.title,
          poster_path: movie.poster_path,
          release_date: movie.release_date,
          vote_average: movie.vote_average
        });
        setInWatchlist(true);
        toast.success("Added to watchlist");
      }
    } catch (err) {
      toast.error("Please login to manage watchlist");
    }
  };

  const handleRate = async (rating: number) => {
    if (!movie) return;
    try {
      await api.post('/ratings/', { 
        movie_id: movie.id, 
        movie_title: movie.title,
        rating: rating,
        poster_path: movie.poster_path,
        release_date: movie.release_date,
        vote_average: movie.vote_average
      });
      setUserRating(rating);
      toast.success(`Rated ${rating} ⭐`);
    } catch (err) {
      toast.error("Please login to rate movies");
    }
  };

  if (loading) return <Loader />;
  if (!movie) return <div className="container">Movie not found</div>;

  const posterUrl = movie.poster_path || 'https://via.placeholder.com/500x750?text=No+Poster';

  return (
    <PageTransition>
      <div className={styles.page}>
        <div className={styles.backdrop}>
          <img src={posterUrl} alt="" />
          <div className={styles.backdropOverlay}></div>
        </div>

        <div className={`${styles.content} container`}>
          <div className={styles.mainInfo}>
            <motion.div 
              className={styles.posterWrapper}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
            >
              <img src={posterUrl} alt={movie.title} className={styles.poster} />
            </motion.div>

            <div className={styles.details}>
              <h1 className={styles.title}>{movie.title}</h1>
              
              <div className={styles.meta}>
                <span className={styles.ratingBadge}>
                  <Star size={16} fill="var(--gold)" color="var(--gold)" />
                  {movie.vote_average?.toFixed(1) || 'N/A'}
                </span>
                <span className={styles.metaItem}>
                  <Clock size={16} /> 124 min
                </span>
                <span className={styles.metaItem}>
                  <Calendar size={16} /> {movie.release_date || 'N/A'}
                </span>
              </div>

              <div className={styles.genres}>
                {movie.genres?.map((g, i) => (
                  <span key={i} className={styles.genreTag}>{g}</span>
                ))}
              </div>

              <div className={styles.overview}>
                <h3>Overview</h3>
                <p>{movie.overview}</p>
              </div>

              <div className={styles.actions}>
                <div className={styles.ratingSection}>
                  <p>Rate this movie:</p>
                  <RatingStars initialRating={userRating} onRate={handleRate} />
                </div>
                
                <button 
                  className={`${styles.watchlistBtn} ${inWatchlist ? styles.active : ''}`}
                  onClick={toggleWatchlist}
                >
                  {inWatchlist ? <Check size={20} /> : <Plus size={20} />}
                  {inWatchlist ? "In Watchlist" : "Add to Watchlist"}
                </button>

                {(movie as any).trailer_key && (
                  <button 
                    className={styles.trailerBtn}
                    onClick={() => setShowTrailer(true)}
                  >
                    <Play size={20} fill="currentColor" /> Watch Trailer
                  </button>
                )}
              </div>
            </div>
          </div>

          <AnimatePresence>
            {showTrailer && (movie as any).trailer_key && (
              <motion.div 
                className={styles.modalBackdrop}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setShowTrailer(false)}
              >
                <motion.div 
                  className={styles.modalContent}
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.8, opacity: 0 }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <button 
                    className={styles.closeModal}
                    onClick={() => setShowTrailer(false)}
                  >
                    &times;
                  </button>
                  <div className={styles.videoWrapper}>
                    <iframe 
                      src={`https://www.youtube.com/embed/${(movie as any).trailer_key}?autoplay=1`}
                      title="YouTube video player"
                      frameBorder="0"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                    ></iframe>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
            </div>
          </div>

          <section className={styles.similarSection}>
            <h2 className={styles.sectionTitle}>Similar Movies You Might Like</h2>
            <MovieGrid movies={similar} />
          </section>
        </div>
      </div>
    </PageTransition>
  );
};

export default MovieDetailPage;
