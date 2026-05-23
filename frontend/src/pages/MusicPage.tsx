import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Headphones, ArrowRight } from 'lucide-react';
import api from '../services/api';
import PageTransition from '../components/PageTransition';
import styles from './MusicPage.module.css';

interface AIRecommendation {
  title: string;
  description: string;
  query: string;
}

const MusicPage: React.FC = () => {
  const [selectedMood, setSelectedMood] = useState('joy');
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>([]);
  const [loading, setLoading] = useState(false);

  const moods = [
    { id: 'joy', emoji: '😊', label: 'Joy' },
    { id: 'thrill', emoji: '🔥', label: 'Thrill' },
    { id: 'sorrow', emoji: '😢', label: 'Sorrow' },
    { id: 'mystery', emoji: '🕵️', label: 'Mystery' }
  ];

  const fetchRecommendations = async (mood: string) => {
    try {
      setLoading(true);
      const { data } = await api.get(`/music/ai/recommend/${mood}`);
      setRecommendations(data.results || []);
    } catch (err) {
      console.error("AI Music Error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations(selectedMood);
  }, [selectedMood]);

  return (
    <PageTransition>
      <div className={styles.page}>
        <header className={styles.hero}>
          <div className={styles.heroGlow}></div>
          <motion.h1 
            className={styles.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            MediaMind <span className={styles.accent}>Music Hub</span>
          </motion.h1>
          <p className={styles.subtitle}>AI-powered cinematic soundscapes curated for your mood.</p>
        </header>

        <section className={styles.moodSection}>
          <h2 className={styles.sectionTitle}>How are you feeling?</h2>
          <div className={styles.moodGrid}>
            {moods.map((mood) => (
              <button
                key={mood.id}
                className={`${styles.moodBtn} ${selectedMood === mood.id ? styles.active : ''}`}
                onClick={() => setSelectedMood(mood.id)}
              >
                <span className={styles.emoji}>{mood.emoji}</span>
                <span className={styles.label}>{mood.label}</span>
              </button>
            ))}
          </div>
        </section>

        <section className={styles.recommendations}>
          <div className={styles.sectionHeader}>
            <Sparkles className={styles.aiIcon} />
            <h2 className={styles.sectionTitle}>AI Picks for {selectedMood}</h2>
          </div>

          {loading ? (
            <div className={styles.loader}>
              <div className={styles.spinner}></div>
              <p>Consulting the AI maestro...</p>
            </div>
          ) : (
            <div className={styles.grid}>
              <AnimatePresence mode="wait">
                {recommendations.map((rec, index) => (
                  <motion.div
                    key={rec.title}
                    className={styles.card}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <div className={styles.cardIcon}>
                      <Headphones />
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
      </div>
    </PageTransition>
  );
};

export default MusicPage;
