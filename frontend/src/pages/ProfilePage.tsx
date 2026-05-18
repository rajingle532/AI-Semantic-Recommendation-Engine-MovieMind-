import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLocation, Link } from 'react-router-dom';
import api from '../services/api';
import MovieGrid from '../components/MovieGrid';
import PageTransition from '../components/PageTransition';
import styles from './ProfilePage.module.css';
import {
  Bookmark, Star, Sparkles, Brain, TrendingUp,
  Film, Clock, Zap, ChevronRight, RefreshCw,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const ProfilePage: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();
  const [watchlist, setWatchlist] = useState<any[]>([]);
  const [ratings, setRatings] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'watchlist' | 'ratings' | 'ai' | 'dna'>('watchlist');
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiInsight, setAiInsight] = useState('');
  const [aiError, setAiError] = useState(false);

  useEffect(() => {
    const hash = location.hash;
    if (hash === '#watchlist') setActiveTab('watchlist');
    else if (hash === '#ai') setActiveTab('ai');
    else if (hash === '#ratings') setActiveTab('ratings');
    else if (hash === '#dna') setActiveTab('dna');
    else setActiveTab('watchlist');
  }, [location.hash]);

  const [tasteProfile, setTasteProfile] = useState<{ top_genres: string[]; top_language: string; rated_count: number; watchlist_count: number } | null>(null);

  const [dnaData, setDnaData] = useState<{
    title: string;
    genres: { name: string; score: number; percentage: number }[];
    tags: string[];
    stats: { rated_count: number; watchlist_count: number; total_inputs: number };
  } | null>(null);
  const [dnaLoading, setDnaLoading] = useState(false);

  const fetchDnaData = async () => {
    setDnaLoading(true);
    try {
      const res = await api.get('/recommend/taste-dna');
      setDnaData(res.data);
    } catch (e) {
      console.warn('Taste DNA fetch failed', e);
    } finally {
      setDnaLoading(false);
    }
  };

  const fetchRecommendations = async () => {
    setAiLoading(true);
    setAiError(false);
    try {
      const res = await api.get('/recommend/smart/me?n=20');
      const recs = res.data.recommendations || [];
      const profile = res.data.profile;
      setRecommendations(recs);
      setTasteProfile(profile);

      if (profile && recs.length > 0) {
        const topGenres = profile.top_genres || [];
        const genreList = topGenres.slice(0, 2).join(' & ') || 'good';
        const langMap: { [key: string]: string } = { en: 'English', es: 'Spanish', hi: 'Hindi', ja: 'Japanese', ko: 'Korean' };
        const langName = langMap[profile.top_language] || profile.top_language || 'foreign';
        setAiInsight(`Based on your ${profile.rated_count} ratings & ${profile.watchlist_count} watchlist movies — you love ${genreList} films in ${langName}. Here are ${recs.length} handpicked picks!`);
      } else if (recs.length > 0) {
        setAiInsight(`Rate and add movies to your watchlist to get hyper-personalized picks. Showing popular recommendations for now.`);
      }
    } catch (e) {
      console.warn('Smart recommendation fetch failed', e);
      setAiError(true);
    } finally {
      setAiLoading(false);
    }
  };

  useEffect(() => {
    const fetchUserData = async () => {
      setLoading(true);
      try {
        const [watchlistRes, ratingsRes] = await Promise.all([
          api.get('/watchlist/my'),
          api.get('/ratings/my'),
        ]);

        const watchlistRaw = watchlistRes.data.watchlist || [];
        const watchlistFormatted = watchlistRaw.map((item: any) => ({
          ...item,
          id: item.movie_id,
          title: item.movie_title || item.title,
        }));

        const ratingsRaw = ratingsRes.data.ratings || [];
        const ratingsFormatted = ratingsRaw.map((item: any) => ({
          ...item,
          id: item.movie_id,
          title: item.movie_title || item.title,
          vote_average: item.rating,
        }));

        setWatchlist(watchlistFormatted);
        setRatings(ratingsFormatted);
        await Promise.all([
          fetchRecommendations(),
          fetchDnaData(),
        ]);
      } catch (err) {
        console.error('Failed to fetch profile data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchUserData();
  }, []);

  const initials = (user?.name ?? 'U').charAt(0).toUpperCase();
  const avgRating = ratings.length > 0
    ? (ratings.reduce((s, r) => s + (r.vote_average || 0), 0) / ratings.length).toFixed(1)
    : '—';

  const tabs = [
    { key: 'watchlist', label: 'Watchlist', count: watchlist.length, icon: <Bookmark size={16} /> },
    { key: 'ratings', label: 'My Ratings', count: ratings.length, icon: <Star size={16} /> },
    { key: 'ai', label: 'AI Picks', count: recommendations.length, icon: <Sparkles size={16} /> },
    { key: 'dna', label: 'Taste DNA', count: '🧬', icon: <Brain size={16} /> },
  ] as const;

  const renderRadarChart = () => {
    if (!dnaData || !dnaData.genres || dnaData.genres.length === 0) {
      return <div style={{ color: 'var(--text-secondary)' }}>Not enough data for Radar Chart</div>;
    }
    const genres = dnaData.genres;
    const N = genres.length;
    const centerX = 160;
    const centerY = 160;
    const radius = 100;
    
    const gridLevels = [0.2, 0.4, 0.6, 0.8, 1.0];
    
    const points = genres.map((g, i) => {
      const angle = (i * 2 * Math.PI) / N - Math.PI / 2;
      const val = Math.max(15, g.percentage);
      const x = centerX + radius * Math.cos(angle) * (val / 100);
      const y = centerY + radius * Math.sin(angle) * (val / 100);
      return { x, y, name: g.name, angle, percentage: g.percentage };
    });
    
    const polygonPath = points.map(p => `${p.x},${p.y}`).join(' ');
    
    return (
      <svg width="320" height="320" viewBox="0 0 320 320" style={{ overflow: 'visible' }}>
        <defs>
          <radialGradient id="radarGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(255, 75, 43, 0.45)" />
            <stop offset="60%" stopColor="rgba(255, 9, 121, 0.25)" />
            <stop offset="100%" stopColor="rgba(99, 102, 241, 0.05)" />
          </radialGradient>
        </defs>
        
        {gridLevels.map((lvl, index) => {
          const r = radius * lvl;
          return (
            <circle
              key={index}
              cx={centerX}
              cy={centerY}
              r={r}
              fill="none"
              stroke="rgba(255, 255, 255, 0.08)"
              strokeWidth="1"
              strokeDasharray="3 3"
            />
          );
        })}
        
        {points.map((p, i) => {
          const outerX = centerX + radius * Math.cos(p.angle);
          const outerY = centerY + radius * Math.sin(p.angle);
          return (
            <line
              key={i}
              x1={centerX}
              y1={centerY}
              x2={outerX}
              y2={outerY}
              stroke="rgba(255, 255, 255, 0.08)"
              strokeWidth="1.5"
            />
          );
        })}
        
        <polygon
          points={polygonPath}
          fill="url(#radarGlow)"
          stroke="rgba(255, 75, 43, 0.85)"
          strokeWidth="2"
          style={{ filter: 'drop-shadow(0 0 6px rgba(255, 75, 43, 0.5))' }}
        />
        
        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r="4.5"
            fill="#ff0979"
            stroke="#ffffff"
            strokeWidth="1.5"
            style={{ filter: 'drop-shadow(0 0 4px rgba(255, 9, 121, 0.8))' }}
          />
        ))}
        
        {points.map((p, i) => {
          const labelRadius = radius + 22;
          const labelX = centerX + labelRadius * Math.cos(p.angle);
          const labelY = centerY + labelRadius * Math.sin(p.angle) + 4;
          
          let textAnchor: 'middle' | 'start' | 'end' = 'middle';
          if (Math.cos(p.angle) > 0.1) textAnchor = 'start';
          else if (Math.cos(p.angle) < -0.1) textAnchor = 'end';
          
          return (
            <text
              key={i}
              x={labelX}
              y={labelY}
              fill="#ffffff"
              fontSize="11"
              fontWeight="700"
              textAnchor={textAnchor}
              style={{ opacity: 0.95, textShadow: '0 2px 4px rgba(0,0,0,0.8)' }}
            >
              {p.name} ({p.percentage}%)
            </text>
          );
        })}
      </svg>
    );
  };

  return (
    <PageTransition>
      <div className={styles.page}>
        {/* ── Hero Profile Header ── */}
        <div className={styles.heroBanner}>
          <div className={styles.heroBg} />
          <div className={`${styles.heroContent} container`}>
            <div className={styles.avatarRing}>
              <div className={styles.avatar}>{initials}</div>
            </div>
            <div className={styles.heroInfo}>
              <h1>{user?.name}</h1>
              <p>{user?.email}</p>
            </div>
            <div className={styles.heroStats}>
              <div className={styles.heroStat}>
                <Bookmark size={18} className={styles.heroStatIcon} />
                <span className={styles.heroStatValue}>{watchlist.length}</span>
                <span className={styles.heroStatLabel}>Watchlist</span>
              </div>
              <div className={styles.heroStatDivider} />
              <div className={styles.heroStat}>
                <Star size={18} className={styles.heroStatIcon} />
                <span className={styles.heroStatValue}>{ratings.length}</span>
                <span className={styles.heroStatLabel}>Ratings</span>
              </div>
              <div className={styles.heroStatDivider} />
              <div className={styles.heroStat}>
                <TrendingUp size={18} className={styles.heroStatIcon} />
                <span className={styles.heroStatValue}>{avgRating}</span>
                <span className={styles.heroStatLabel}>Avg Score</span>
              </div>
            </div>
            <Link to="/account" className={styles.editProfileBtn}>
              Edit Profile <ChevronRight size={15} />
            </Link>
          </div>
        </div>

        <div className={`${styles.main} container`}>
          {/* ── Tabs ── */}
          <div className={styles.tabsRow}>
            {tabs.map((t) => (
              <button
                key={t.key}
                className={`${styles.tab} ${activeTab === t.key ? styles.activeTab : ''}`}
                onClick={() => setActiveTab(t.key)}
              >
                {t.icon}
                {t.label}
                <span className={`${styles.tabBadge} ${activeTab === t.key ? styles.tabBadgeActive : ''}`}>
                  {t.count}
                </span>
              </button>
            ))}
          </div>

          {/* ── Tab Content ── */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25 }}
            >
              {activeTab === 'watchlist' && (
                <section>
                  {loading ? (
                    <div className={styles.shimmerGrid}>
                      {[...Array(10)].map((_, i) => <div key={i} className={styles.shimmerCard} />)}
                    </div>
                  ) : (
                    <MovieGrid
                      movies={watchlist}
                      emptyMessage="Your watchlist is empty. Browse movies and add them to watch later!"
                    />
                  )}
                </section>
              )}

              {activeTab === 'ratings' && (
                <section>
                  {loading ? (
                    <div className={styles.shimmerGrid}>
                      {[...Array(10)].map((_, i) => <div key={i} className={styles.shimmerCard} />)}
                    </div>
                  ) : (
                    <MovieGrid
                      movies={ratings}
                      emptyMessage="You haven't rated any movies yet. Rate movies to unlock AI recommendations!"
                    />
                  )}
                </section>
              )}

              {activeTab === 'ai' && (
                <section>
                  {/* AI Insight Banner */}
                  <div className={styles.aiInsightBanner}>
                    <div className={styles.aiInsightIcon}>
                      <Brain size={22} />
                    </div>
                    <div className={styles.aiInsightText}>
                      <h3>
                        <Zap size={14} style={{ display: 'inline', marginRight: '5px', color: '#f59e0b' }} />
                        AI-Powered Recommendations
                      </h3>
                      <p>
                        {aiLoading
                          ? 'Analyzing your taste profile...'
                          : aiInsight || 'Rate some movies to let our AI learn your taste!'}
                      </p>
                      {tasteProfile?.top_genres && (
                        <div className={styles.genreChips}>
                          {tasteProfile.top_genres.map(g => <span key={g} className={styles.genreChip}>{g}</span>)}
                        </div>
                      )}
                    </div>
                    <button
                      className={styles.refreshBtn}
                      onClick={() => fetchRecommendations()}
                      title="Refresh recommendations"
                    >
                      <RefreshCw size={16} className={aiLoading ? styles.spinning : ''} />
                    </button>
                  </div>

                   {/* Error state retry block */}
                  {aiError && !aiLoading && (
                    <div className={styles.aiEmptyState} style={{ borderColor: 'rgba(239, 68, 68, 0.2)', background: 'linear-gradient(180deg, rgba(239, 68, 68, 0.05) 0%, rgba(20, 20, 20, 0.95) 100%)' }}>
                      <div className={styles.aiEmptyIcon} style={{ color: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)' }}>
                        <RefreshCw size={40} className={styles.spinning} style={{ animationDuration: '4s' }} />
                      </div>
                      <h3 style={{ color: '#fca5a5' }}>AI Engine Connection Interrupted</h3>
                      <p style={{ maxWidth: '480px', margin: '0 auto 24px' }}>
                        The smart recommendation engine is currently waking up or experiencing a brief latency spike.
                      </p>
                      <button onClick={() => fetchRecommendations()} className={styles.browseCta} style={{ background: 'linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)', border: 'none', cursor: 'pointer' }}>
                        <RefreshCw size={16} /> Reconnect AI Engine
                      </button>
                    </div>
                  )}

                  {/* How it works */}
                  {!aiError && recommendations.length === 0 && !aiLoading && (
                    <div className={styles.aiEmptyState}>
                      <div className={styles.aiEmptyIcon}>
                        <Film size={40} />
                      </div>
                      <h3>Your AI engine is waiting</h3>
                      <p>Rate at least 3–5 movies and our semantic AI will find hidden gems that match your exact taste.</p>
                      <div className={styles.aiSteps}>
                        <div className={styles.aiStep}>
                          <span>1</span>
                          <p>Browse & rate movies you've seen</p>
                        </div>
                        <div className={styles.aiStep}>
                          <span>2</span>
                          <p>AI analyzes your unique taste profile</p>
                        </div>
                        <div className={styles.aiStep}>
                          <span>3</span>
                          <p>Get hyper-personalized picks</p>
                        </div>
                      </div>
                      <Link to="/" className={styles.browseCta}>
                        <Film size={16} /> Browse Movies
                      </Link>
                    </div>
                  )}

                  {aiLoading && (
                    <div className={styles.shimmerGrid}>
                      {[...Array(10)].map((_, i) => <div key={i} className={styles.shimmerCard} />)}
                    </div>
                  )}

                  {!aiLoading && recommendations.length > 0 && (
                    <>
                      <p className={styles.aiSubtitle}>
                        <Clock size={13} style={{ display: 'inline', marginRight: '5px' }} />
                        Personalized just for you · Refreshes as you rate more movies
                      </p>
                      <MovieGrid movies={recommendations} />
                    </>
                  )}
                </section>
              )}

              {activeTab === 'dna' && (
                <section>
                  {dnaLoading ? (
                    <div className={styles.shimmerGrid}>
                      {[...Array(6)].map((_, i) => <div key={i} className={styles.shimmerCard} />)}
                    </div>
                  ) : !dnaData || !dnaData.genres || dnaData.genres.length === 0 ? (
                    <div className={styles.aiEmptyState}>
                      <div className={styles.aiEmptyIcon}>
                        <Brain size={40} />
                      </div>
                      <h3>Your Taste DNA is compiling...</h3>
                      <p>Rate or watchlist at least 1 movie to generate your unique cinematic Taste DNA dashboard.</p>
                      <Link to="/" className={styles.browseCta}>
                        <Film size={16} /> Browse & Rate Movies
                      </Link>
                    </div>
                  ) : (
                    <div className={styles.dnaDashboard}>
                      {/* Left Side: Radar Chart & Stats */}
                      <div className={styles.dnaLeft}>
                        <div className={styles.dnaCard}>
                          <h3 className={styles.sectionHeader}>
                            <Brain size={18} style={{ color: '#ff4b2b' }} /> Taste Genre Radar
                          </h3>
                          <div className={styles.radarWrapper}>
                            {renderRadarChart()}
                          </div>
                        </div>

                        <div className={styles.dnaCard}>
                          <h3 className={styles.sectionHeader}>
                            <TrendingUp size={18} style={{ color: '#ff0979' }} /> Profile Stats DNA
                          </h3>
                          <div className={styles.statsGrid}>
                            <div className={styles.statBlock}>
                              <div className={styles.statNumber}>{dnaData.stats.rated_count}</div>
                              <div className={styles.statLabel}>Rated</div>
                            </div>
                            <div className={styles.statBlock}>
                              <div className={styles.statNumber}>{dnaData.stats.watchlist_count}</div>
                              <div className={styles.statLabel}>Watchlist</div>
                            </div>
                            <div className={styles.statBlock}>
                              <div className={styles.statNumber}>{dnaData.stats.total_inputs}</div>
                              <div className={styles.statLabel}>Inputs</div>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Right Side: Personality & Tag Cloud */}
                      <div className={styles.dnaRight}>
                        <div className={styles.dnaCard} style={{ background: 'linear-gradient(135deg, rgba(255, 75, 43, 0.05) 0%, rgba(255, 9, 121, 0.05) 100%)', borderColor: 'rgba(255, 75, 43, 0.15)' }}>
                          <div className={styles.personalityHeader}>
                            <Sparkles size={14} style={{ color: '#ff4b2b' }} /> AI Taste Personality
                          </div>
                          <h2 className={styles.personalityTitle}>{dnaData.title}</h2>
                          <p className={styles.personalityDesc}>
                            Your viewing habits demonstrate a highly refined interest in theme-driven storytelling. You tend to prioritize complex characters, immersive atmospheres, and strong genre elements. This title is automatically synthesized by analyzing the relationship weights of your rated movies and watchlist collections!
                          </p>
                        </div>

                        <div className={styles.dnaCard}>
                          <h3 className={styles.sectionHeader}>
                            <Zap size={18} style={{ color: '#f59e0b' }} /> Cinematic Sub-themes
                          </h3>
                          <div className={styles.tagCloud}>
                            {dnaData.tags.map((tag, idx) => (
                              <span key={idx} className={styles.dnaTag}>
                                #{tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </section>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </PageTransition>
  );
};

export default ProfilePage;
