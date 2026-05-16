import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Check, Star, Calendar, Play, X, Share2, Tv, ChevronDown, ChevronUp } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';
import { Movie } from '../types';
import Loader from '../components/Loader';
import RatingStars from '../components/RatingStars';
import PageTransition from '../components/PageTransition';
import ShareModal from '../components/ShareModal';
import MovieGrid from '../components/MovieGrid';
import styles from './MovieDetailPage.module.css';

const TVDetailPage: React.FC = () => {
  const { id } = useParams();
  const [tvShow, setTvShow] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [inWatchlist, setInWatchlist] = useState(false);
  const [userRating, setUserRating] = useState(0);
  const [showShareModal, setShowShareModal] = useState(false);
  const [openSeason, setOpenSeason] = useState<number | null>(null);
  const [seasonDetails, setSeasonDetails] = useState<Record<number, any>>({});
  const [loadingSeason, setLoadingSeason] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchTVData = async () => {
      setLoading(true);
      try {
        const [detailsRes, watchlistRes, ratingsRes] = await Promise.all([
          api.get(`/tv/${id}`),
          api.get('/watchlist/my').catch(() => ({ data: { watchlist: [] } })),
          api.get('/ratings/my').catch(() => ({ data: { ratings: [] } }))
        ]);

        setTvShow(detailsRes.data);

        const watchlist = watchlistRes.data.watchlist || [];
        setInWatchlist(watchlist.some((m: any) => m.movie_id === parseInt(id!)));

        const ratings = ratingsRes.data.ratings || [];
        const existingRating = ratings.find((r: any) => r.movie_id === parseInt(id!));
        if (existingRating) {
          setUserRating(existingRating.rating);
        }
      } catch (err) {
        toast.error("Failed to load TV show details");
      } finally {
        setLoading(false);
      }
    };

    fetchTVData();
    window.scrollTo(0, 0);
  }, [id]);

  const toggleWatchlist = async () => {
    if (!tvShow) return;
    try {
      if (inWatchlist) {
        await api.delete(`/watchlist/${id}`);
        setInWatchlist(false);
        toast.success("Removed from watchlist");
      } else {
        await api.post('/watchlist/', {
          movie_id: tvShow.id,
          movie_title: tvShow.title,
          poster_path: tvShow.poster_path,
          release_date: tvShow.release_date,
          vote_average: tvShow.vote_average,
          media_type: 'tv'
        });
        setInWatchlist(true);
        toast.success("Added to watchlist");
      }
    } catch (err) {
      toast.error("Please login to manage watchlist");
    }
  };

  const handleRate = async (rating: number) => {
    if (!tvShow) return;
    try {
      await api.post('/ratings/', {
        movie_id: tvShow.id,
        movie_title: tvShow.title,
        rating: rating,
        poster_path: tvShow.poster_path,
        release_date: tvShow.release_date,
        vote_average: tvShow.vote_average,
        media_type: 'tv'
      });
      setUserRating(rating);
      toast.success(`Rated ${rating} ⭐`);
    } catch (err) {
      toast.error("Please login to rate shows");
    }
  };

  const handleSeasonToggle = async (seasonNumber: number) => {
    if (openSeason === seasonNumber) {
      setOpenSeason(null);
      return;
    }
    
    setOpenSeason(seasonNumber);
    if (!seasonDetails[seasonNumber]) {
      setLoadingSeason(true);
      try {
        const res = await api.get(`/tv/${id}/season/${seasonNumber}`);
        setSeasonDetails(prev => ({ ...prev, [seasonNumber]: res.data.episodes }));
      } catch (err) {
        toast.error("Failed to load episodes");
      } finally {
        setLoadingSeason(false);
      }
    }
  };

  if (loading) return <Loader />;
  if (!tvShow) return <div className="container">TV Show not found</div>;

  const posterUrl = tvShow.poster_path || 'https://via.placeholder.com/500x750?text=No+Poster';

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
              <div style={{ position: 'absolute', top: 10, left: 10, background: 'var(--accent)', color: 'white', padding: '5px 10px', borderRadius: '4px', fontWeight: 'bold', zIndex: 2 }}>TV SHOW</div>
              <img src={posterUrl} alt={tvShow.title} className={styles.poster} />
            </motion.div>

            <div className={styles.details}>
              <h1 className={styles.title}>{tvShow.title}</h1>

              <div className={styles.meta}>
                <span className={styles.ratingBadge}>
                  <Star size={16} fill="var(--gold)" color="var(--gold)" />
                  {tvShow.vote_average?.toFixed(1) || 'N/A'}
                </span>
                <span className={styles.metaItem}>
                  <Tv size={16} /> {tvShow.number_of_seasons} Seasons ({tvShow.number_of_episodes} Episodes)
                </span>
                <span className={styles.metaItem}>
                  <Calendar size={16} /> {tvShow.release_date ? tvShow.release_date.split('-')[0] : 'N/A'}
                </span>
              </div>

              <div className={styles.genres}>
                {Array.isArray(tvShow.genres) && tvShow.genres.map((g: string, i: number) => (
                  <span key={i} className={styles.genreTag}>{g}</span>
                ))}
              </div>

              <div className={styles.overview}>
                <h3>Overview</h3>
                <p>{tvShow.overview}</p>
              </div>

              <div className={styles.actions}>
                <div className={styles.ratingSection}>
                  <p>Rate this show:</p>
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
                    className={styles.shareBtn}
                    onClick={() => setShowShareModal(true)}
                    title="Share Show"
                  >
                    <Share2 size={20} color="var(--accent)" />
                    <span>Share</span>
                  </button>
                </div>

                {/* Watch Providers Section */}
                <div className={styles.providersSection}>
                  <p className={styles.sectionSmallTitle}>Where to Watch:</p>
                  {tvShow.watch_providers && (tvShow.watch_providers.flatrate.length > 0) ? (
                    <div className={styles.providerCategories}>
                      <div className={styles.providerCategory}>
                        <div className={styles.providerList}>
                          {tvShow.watch_providers.flatrate.map((p: any) => (
                            <a
                              key={p.provider_id}
                              href={tvShow.watch_providers.link}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={styles.providerItem}
                              title={p.provider_name}
                            >
                              {p.logo_path && <img src={p.logo_path} alt={p.provider_name} className={styles.providerLogo} />}
                            </a>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Streaming info not available.</p>
                  )}
                </div>

              </div>
            </div>
          </div>

          {/* Seasons Accordion */}
          <div style={{ marginTop: '3rem', width: '100%', maxWidth: '800px' }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>Seasons</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {tvShow.seasons && tvShow.seasons.filter((s: any) => s.season_number > 0).map((season: any) => (
                <div key={season.id} style={{ background: 'var(--surface-light)', borderRadius: '8px', overflow: 'hidden' }}>
                  <div 
                    onClick={() => handleSeasonToggle(season.season_number)}
                    style={{ padding: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', background: 'rgba(255,255,255,0.02)' }}
                  >
                    <div style={{ fontWeight: 'bold' }}>
                      Season {season.season_number} <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginLeft: '10px' }}>({season.episode_count} Episodes)</span>
                    </div>
                    {openSeason === season.season_number ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </div>
                  
                  <AnimatePresence>
                    {openSeason === season.season_number && (
                      <motion.div 
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        style={{ overflow: 'hidden' }}
                      >
                        <div style={{ padding: '1rem', borderTop: '1px solid var(--border)', background: 'var(--surface)' }}>
                          {loadingSeason ? (
                            <p>Loading episodes...</p>
                          ) : seasonDetails[season.season_number] ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                              {seasonDetails[season.season_number].map((ep: any) => (
                                <div key={ep.id} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                                  <div style={{ flexShrink: 0, width: '120px', aspectRatio: '16/9', background: '#333', borderRadius: '4px', overflow: 'hidden' }}>
                                    {ep.still_path ? (
                                      <img src={ep.still_path} alt={ep.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                                    ) : (
                                      <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666', fontSize: '0.8rem' }}>No Image</div>
                                    )}
                                  </div>
                                  <div>
                                    <div style={{ fontWeight: 'bold', fontSize: '1rem' }}>
                                      {ep.episode_number}. {ep.name}
                                    </div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: '4px 0' }}>
                                      {ep.air_date ? ep.air_date.split('-')[0] : ''} • {ep.runtime ? `${ep.runtime} min` : ''}
                                    </div>
                                    <p style={{ fontSize: '0.85rem', color: '#ccc', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                                      {ep.overview || "No description available."}
                                    </p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p>No episodes found.</p>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </div>
          </div>

          {/* Similar Shows */}
          {tvShow.similar && tvShow.similar.length > 0 && (
            <div style={{ marginTop: '4rem' }}>
              <h2 className={styles.sectionTitle}>Similar Shows</h2>
              <MovieGrid movies={tvShow.similar} loading={false} />
            </div>
          )}

        </div>
      </div>
      <ShareModal isOpen={showShareModal} title={tvShow.title} url={`/tv/${tvShow.id}`} onClose={() => setShowShareModal(false)} />
    </PageTransition>
  );
};

export default TVDetailPage;
