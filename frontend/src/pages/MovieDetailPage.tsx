import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Check, Star, Clock, Calendar, Play, X, Share2 } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';
import { Movie } from '../types';
import MovieGrid from '../components/MovieGrid';
import Loader from '../components/Loader';
import RatingStars from '../components/RatingStars';
import PageTransition from '../components/PageTransition';
import ShareModal from '../components/ShareModal';
import MovieSongs from '../components/MovieSongs';
import SpotifySoundtrack from '../components/SpotifySoundtrack';
import MovieMusicAI from '../components/MovieMusicAI';
import styles from './MovieDetailPage.module.css';

const MovieDetailPage: React.FC = () => {
  const { id } = useParams();
  const [movie, setMovie] = useState<Movie | null>(null);
  const [similar, setSimilar] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [inWatchlist, setInWatchlist] = useState(false);
  const [userRating, setUserRating] = useState(0);
  const [showTrailer, setShowTrailer] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'watch' | 'music'>('overview');

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
        {/* Modal is now here at the top level of the component */}
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
                  <X size={40} />
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
                <div style={{ padding: '1rem', textAlign: 'center' }}>
                  <a
                    href={`https://www.youtube.com/watch?v=${(movie as any).trailer_key}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: '#aaa', fontSize: '0.8rem', textDecoration: 'underline' }}
                  >
                    Having trouble? Watch on YouTube
                  </a>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

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
                {Array.isArray(movie.genres) && movie.genres.map((g, i) => (
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

                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                  <button
                    className={`${styles.watchlistBtn} ${inWatchlist ? styles.active : ''}`}
                    onClick={toggleWatchlist}
                  >
                    {inWatchlist ? <Check size={20} /> : <Plus size={20} />}
                    {inWatchlist ? "In Watchlist" : "Add to Watchlist"}
                  </button>

                  <button
                    className={styles.trailerBtn}
                    onClick={() => {
                      if ((movie as any).trailer_key) {
                        setShowTrailer(true);
                      } else {
                        toast.error("Trailer not available for this movie");
                      }
                    }}
                    style={{ opacity: (movie as any).trailer_key ? 1 : 0.6 }}
                  >
                    <Play size={20} fill="currentColor" /> Watch Trailer
                  </button>

                  <button
                    className={styles.shareBtn}
                    onClick={() => setShowShareModal(true)}
                    title="Share Movie"
                  >
                    <Share2 size={20} color="var(--accent)" />
                    <span>Share</span>
                  </button>
                </div>

                {/* Watch Providers Section */}
                <div className={styles.providersSection}>
                  <p className={styles.sectionSmallTitle}>Where to Watch:</p>

                  {(movie as any).watch_providers ? (
                    <div className={styles.providerCategories}>
                      {/* Streaming (Subscription) */}
                      {Array.isArray((movie as any).watch_providers.flatrate) && (movie as any).watch_providers.flatrate.length > 0 && (
                        <div className={styles.providerCategory}>
                          <span className={styles.categoryLabel}>Stream</span>
                          <div className={styles.providerList}>
                            {(movie as any).watch_providers.flatrate.map((p: any) => (
                              <a
                                key={p.provider_id}
                                href={(movie as any).watch_providers.link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className={styles.providerItem}
                                title={p.provider_name}
                              >
                                {p.logo_path && <img src={p.logo_path} alt={p.provider_name} className={styles.providerLogo} />}
                                <span className={styles.providerName}>{p.provider_name}</span>
                              </a>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Rent */}
                      {Array.isArray((movie as any).watch_providers.rent) && (movie as any).watch_providers.rent.length > 0 && (
                        <div className={styles.providerCategory}>
                          <span className={styles.categoryLabel}>Rent</span>
                          <div className={styles.providerList}>
                            {(movie as any).watch_providers.rent.map((p: any) => (
                              <a
                                key={p.provider_id}
                                href={(movie as any).watch_providers.link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className={styles.providerItem}
                                title={p.provider_name}
                              >
                                {p.logo_path && <img src={p.logo_path} alt={p.provider_name} className={styles.providerLogo} />}
                                <span className={styles.providerName}>{p.provider_name}</span>
                              </a>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Buy */}
                      {Array.isArray((movie as any).watch_providers.buy) && (movie as any).watch_providers.buy.length > 0 && (
                        <div className={styles.providerCategory}>
                          <span className={styles.categoryLabel}>Buy</span>
                          <div className={styles.providerList}>
                            {(movie as any).watch_providers.buy.map((p: any) => (
                              <a
                                key={p.provider_id}
                                href={(movie as any).watch_providers.link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className={styles.providerItem}
                                title={p.provider_name}
                              >
                                {p.logo_path && <img src={p.logo_path} alt={p.provider_name} className={styles.providerLogo} />}
                                <span className={styles.providerName}>{p.provider_name}</span>
                              </a>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* No providers found */}
                      {(!((movie as any).watch_providers.flatrate?.length) &&
                        !((movie as any).watch_providers.rent?.length) &&
                        !((movie as any).watch_providers.buy?.length)) && (
                          <span className={styles.noProvider}>
                            Not available for streaming in your region.
                          </span>
                        )}
                    </div>
                  ) : (
                    <span className={styles.noProvider}>Loading provider data...</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Tabs Navigation */}
          <div className={styles.tabsContainer}>
            <div className={styles.tabs}>
              <button 
                className={`${styles.tabBtn} ${activeTab === 'overview' ? styles.active : ''}`}
                onClick={() => setActiveTab('overview')}
              >
                Overview
              </button>
              <button 
                className={`${styles.tabBtn} ${activeTab === 'watch' ? styles.active : ''}`}
                onClick={() => setActiveTab('watch')}
              >
                Watch
              </button>
              <button 
                className={`${styles.tabBtn} ${activeTab === 'music' ? styles.active : ''}`}
                onClick={() => setActiveTab('music')}
              >
                Music
              </button>
            </div>
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {activeTab === 'overview' && (
                <>
                  <section className={styles.overviewSection}>
                    <div className={styles.overviewText}>
                      <h2 className={styles.sectionTitle}>The Story</h2>
                      <p>{movie.overview}</p>
                    </div>
                  </section>

                  <section className={styles.castSection}>
                    <h2 className={styles.sectionTitle}>Top Cast</h2>
                    <div className={styles.castList}>
                      {Array.isArray((movie as any).cast) && (movie as any).cast.map((member: any) => (
                        <Link to={`/person/${member.id}`} key={member.id} className={styles.castCard}>
                          <div className={styles.castAvatar}>
                            {member.profile_path ? (
                              <img src={member.profile_path} alt={member.name} />
                            ) : (
                              <div className={styles.avatarPlaceholder}>{member.name[0]}</div>
                            )}
                          </div>
                          <div className={styles.castInfo}>
                            <p className={styles.castName}>{member.name}</p>
                            <p className={styles.castCharacter}>{member.character}</p>
                          </div>
                        </Link>
                      ))}
                    </div>
                  </section>
                </>
              )}

              {activeTab === 'watch' && (
                <section className={styles.watchSection}>
                  <h2 className={styles.sectionTitle}>Where to Watch</h2>
                  <div className={styles.providersFull}>
                    {(movie as any).watch_providers ? (
                      <div className={styles.providerCategories}>
                        {/* Streaming (Subscription) */}
                        {Array.isArray((movie as any).watch_providers.flatrate) && (movie as any).watch_providers.flatrate.length > 0 && (
                          <div className={styles.providerCategory}>
                            <span className={styles.categoryLabel}>Stream</span>
                            <div className={styles.providerList}>
                              {(movie as any).watch_providers.flatrate.map((p: any) => (
                                <a
                                  key={p.provider_id}
                                  href={(movie as any).watch_providers.link}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className={styles.providerItem}
                                  title={p.provider_name}
                                >
                                  {p.logo_path && <img src={p.logo_path} alt={p.provider_name} className={styles.providerLogo} />}
                                  <span className={styles.providerName}>{p.provider_name}</span>
                                </a>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Rent */}
                        {Array.isArray((movie as any).watch_providers.rent) && (movie as any).watch_providers.rent.length > 0 && (
                          <div className={styles.providerCategory}>
                            <span className={styles.categoryLabel}>Rent</span>
                            <div className={styles.providerList}>
                              {(movie as any).watch_providers.rent.map((p: any) => (
                                <a
                                  key={p.provider_id}
                                  href={(movie as any).watch_providers.link}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className={styles.providerItem}
                                  title={p.provider_name}
                                >
                                  {p.logo_path && <img src={p.logo_path} alt={p.provider_name} className={styles.providerLogo} />}
                                  <span className={styles.providerName}>{p.provider_name}</span>
                                </a>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Buy */}
                        {Array.isArray((movie as any).watch_providers.buy) && (movie as any).watch_providers.buy.length > 0 && (
                          <div className={styles.providerCategory}>
                            <span className={styles.categoryLabel}>Buy</span>
                            <div className={styles.providerList}>
                              {(movie as any).watch_providers.buy.map((p: any) => (
                                <a
                                  key={p.provider_id}
                                  href={(movie as any).watch_providers.link}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className={styles.providerItem}
                                  title={p.provider_name}
                                >
                                  {p.logo_path && <img src={p.logo_path} alt={p.provider_name} className={styles.providerLogo} />}
                                  <span className={styles.providerName}>{p.provider_name}</span>
                                </a>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* No providers found */}
                        {(!((movie as any).watch_providers.flatrate?.length) &&
                          !((movie as any).watch_providers.rent?.length) &&
                          !((movie as any).watch_providers.buy?.length)) && (
                            <div className={styles.noProviderBig}>
                              <p>Not available for streaming in your region.</p>
                            </div>
                          )}
                      </div>
                    ) : (
                      <div className={styles.noProviderBig}>
                        <p>Loading provider data...</p>
                      </div>
                    )}
                  </div>

                  {(movie as any).trailer_key && (
                    <div className={styles.trailerPreview}>
                      <h3 className={styles.sectionSmallTitle}>Official Trailer</h3>
                      <div className={styles.videoWrapper}>
                        <iframe
                          src={`https://www.youtube.com/embed/${(movie as any).trailer_key}`}
                          title="YouTube video player"
                          frameBorder="0"
                          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                          allowFullScreen
                        ></iframe>
                      </div>
                    </div>
                  )}
                </section>
              )}

              {activeTab === 'music' && (
                <div className={styles.musicTab}>
                  <MovieMusicAI
                    movieId={movie.id}
                    movieTitle={movie.title}
                  />
                  
                  <MovieSongs
                    movieTitle={movie.title}
                    releaseYear={movie.release_date || ''}
                  />
                  
                  <SpotifySoundtrack 
                    movieTitle={movie.title}
                  />
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          <section className={styles.similarSection}>
            <h2 className={styles.sectionTitle}>Similar Movies You Might Like</h2>
            <MovieGrid movies={similar} />
          </section>
        </div>
        <ShareModal
          isOpen={showShareModal}
          onClose={() => setShowShareModal(false)}
          title={movie.title}
          url={`/movie/${movie.id}`}
        />
      </div>
    </PageTransition>
  );
};

export default MovieDetailPage;
