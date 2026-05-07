import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import MovieGrid from '../components/MovieGrid';
import PageTransition from '../components/PageTransition';
import styles from './ProfilePage.module.css';

const ProfilePage: React.FC = () => {
  const { user } = useAuth();
  const [watchlist, setWatchlist] = useState<any[]>([]);
  const [ratings, setRatings] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

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
          title: item.movie_title || item.title
        }));

        const ratingsRaw = ratingsRes.data.ratings || [];
        const ratingsFormatted = ratingsRaw.map((item: any) => ({
          ...item,
          id: item.movie_id,
          title: item.movie_title || item.title,
          vote_average: item.rating
        }));

        setWatchlist(watchlistFormatted);
        setRatings(ratingsFormatted);

        if (ratingsRaw.length > 0) {
          const topRated = [...ratingsRaw]
            .sort((a, b) => (b.rating || 0) - (a.rating || 0))
            .slice(0, 5);
            
          const allRecs: any[] = [];
          const seenIds = new Set<number>();

          for (const movie of topRated) {
            const movieId = movie.movie_id || movie.id;
            if (!movieId) continue;
            
            try {
              const res = await api.get(`/recommend/${movieId}`);
              const moviesList = res.data.recommendations || 
                                (Array.isArray(res.data) ? res.data : []) || 
                                (res.data.results) || [];
              
              moviesList.forEach((m: any) => {
                const mid = m.id || m.movie_id;
                if (mid && !seenIds.has(mid)) {
                  seenIds.add(mid);
                  allRecs.push({
                    ...m,
                    id: mid 
                  });
                }
              });
            } catch (e) {
              console.warn('Profile: Recommendation fetch failed', e);
            }
          }
          setRecommendations(allRecs.slice(0, 10));
        }
      } catch (err) {
        console.error("Failed to fetch profile data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, []);

  return (
    <PageTransition>
      <div className={`${styles.page} container`}>
        <header className={styles.header}>
          <div className={styles.userSection}>
            <div className={styles.avatar}>
              {(user?.name ?? "U").charAt(0).toUpperCase()}
            </div>
            <div className={styles.userInfo}>
              <h1 className={styles.name}>{user?.name}</h1>
              <p className={styles.email}>{user?.email}</p>
            </div>
          </div>
          
          <div className={styles.stats}>
            <div className={styles.statItem}>
              <span className={styles.statValue}>{watchlist.length}</span>
              <span className={styles.statLabel}>Watchlist</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statValue}>{ratings.length}</span>
              <span className={styles.statLabel}>Ratings</span>
            </div>
          </div>
        </header>

        <div className={styles.content}>
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Picked by MovieMind AI 🤖</h2>
            {recommendations.length > 0 ? (
              <MovieGrid movies={recommendations} />
            ) : (
              <div style={{textAlign: 'center', padding: '40px', color: 'var(--text-muted)'}}>
                {loading ? 'Analyzing your taste...' : 'Rate some movies to get personalized recommendations!'}
              </div>
            )}
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>My Watchlist</h2>
            <MovieGrid 
              movies={watchlist} 
              emptyMessage="Your watchlist is empty. Add some movies to watch later!" 
            />
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>My Ratings ⭐</h2>
            <MovieGrid 
              movies={ratings} 
              emptyMessage="You haven't rated any movies yet. Share your thoughts on what you've watched!" 
            />
          </section>
        </div>
      </div>
    </PageTransition>
  );
};

export default ProfilePage;
