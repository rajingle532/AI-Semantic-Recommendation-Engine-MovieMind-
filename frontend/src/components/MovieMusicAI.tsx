import React, { useEffect, useState } from 'react';
import { Sparkles, Headphones, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import styles from './MovieMusicAI.module.css';

interface MusicRecommendation {
  title: string;
  description: string;
  query: string;
}

interface MovieMusicAIProps {
  movieId: number;
  movieTitle: string;
}

const MovieMusicAI: React.FC<MovieMusicAIProps> = ({ movieId, movieTitle }) => {
  const [recommendations, setRecommendations] = useState<MusicRecommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        setLoading(true);
        const { data } = await api.get(`/music/ai/recommend/movie/${movieId}`);
        setRecommendations(data.results || []);
      } catch (err) {
        console.error("Failed to fetch AI music recommendations:", err);
      } finally {
        setLoading(false);
      }
    };

    if (movieId) {
      fetchRecommendations();
    }
  }, [movieId]);

  if (!loading && recommendations.length === 0) return null;

  return (
    <section className={styles.aiSection}>
      <div className={styles.header}>
        <Sparkles className={styles.aiIcon} />
        <h2 className={styles.sectionTitle}>Watch + Listen Engine</h2>
      </div>
      
      <p className={styles.subtitle}>
        Since you liked the vibe of <strong>{movieTitle}</strong>, MovieMind AI suggests these soundscapes:
      </p>

      {loading ? (
        <div className={styles.loader}>
          <div className={styles.spinner}></div>
          <p>Analyzing movie tone...</p>
        </div>
      ) : (
        <div className={styles.grid}>
          <AnimatePresence>
            {recommendations.map((rec, index) => (
              <motion.div
                key={rec.title}
                className={styles.card}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <div className={styles.cardIcon}>
                  <Headphones size={20} />
                </div>
                <div className={styles.cardContent}>
                  <h3>{rec.title}</h3>
                  <p>{rec.description}</p>
                  <a 
                    href={`https://open.spotify.com/search/${encodeURIComponent(rec.query)}`}
                    target="_blank" 
                    rel="noopener noreferrer"
                    className={styles.spotifyLink}
                  >
                    Listen on Spotify <ArrowRight size={14} />
                  </a>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </section>
  );
};

export default MovieMusicAI;
