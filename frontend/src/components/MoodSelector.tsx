import React from 'react';
import { motion } from 'framer-motion';
import styles from './MoodSelector.module.css';

const moods = [
  { id: 'joy', label: 'Joy', emoji: '😊', color: '#FFD700' },
  { id: 'thrill', label: 'Thrill', emoji: '🔥', color: '#FF4500' },
  { id: 'sorrow', label: 'Sorrow', emoji: '😢', color: '#1E90FF' },
  { id: 'mystery', label: 'Mystery', emoji: '🕵️', color: '#9370DB' },
];

interface MoodSelectorProps {
  activeMood: string | null;
  onMoodSelect: (mood: string) => void;
}

const MoodSelector: React.FC<MoodSelectorProps> = ({ activeMood, onMoodSelect }) => {
  return (
    <div className={styles.moodContainer}>
      <h3 className={styles.subtitle}>How are you feeling today?</h3>
      <div className={styles.moodList}>
        {moods.map((mood) => (
          <motion.button
            key={mood.id}
            className={`${styles.moodButton} ${activeMood === mood.id ? styles.active : ''}`}
            onClick={() => onMoodSelect(mood.id)}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ '--mood-color': mood.color } as any}
          >
            <span className={styles.emoji}>{mood.emoji}</span>
            <span className={styles.label}>{mood.label}</span>
          </motion.button>
        ))}
        
        {activeMood && (
          <motion.button 
            className={styles.clearBtn}
            onClick={() => onMoodSelect('')}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            Clear
          </motion.button>
        )}
      </div>
    </div>
  );
};

export default MoodSelector;
