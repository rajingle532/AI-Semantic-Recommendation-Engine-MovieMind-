import React, { useState, useEffect } from 'react';
import styles from './RatingStars.module.css';

interface RatingStarsProps {
  initialRating?: number;
  onRate?: (rating: number) => void;
  readonly?: boolean;
}

const RatingStars: React.FC<RatingStarsProps> = ({ initialRating = 0, onRate, readonly = false }) => {
  const [hover, setHover] = useState(0);
  const [rating, setRating] = useState(initialRating);

  useEffect(() => {
    setRating(initialRating);
  }, [initialRating]);

  const handleClick = (value: number) => {
    if (readonly) return;
    setRating(value);
    if (onRate) onRate(value);
  };

  return (
    <div className={styles.container}>
      <div className={styles.stars}>
        {[1, 2, 3, 4, 5].map((star) => (
          <span
            key={star}
            className={`${styles.star} ${(hover || rating) >= star ? styles.active : ''}`}
            onMouseEnter={() => !readonly && setHover(star)}
            onMouseLeave={() => !readonly && setHover(0)}
            onClick={() => handleClick(star)}
          >
            ★
          </span>
        ))}
      </div>
      {!readonly && rating > 0 && (
        <span className={styles.text}>Your rating: {rating}/5</span>
      )}
    </div>
  );
};

export default RatingStars;
