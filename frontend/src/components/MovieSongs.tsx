import React, { useEffect, useState } from 'react';
import api from '../services/api';
import styles from './MovieSongs.module.css';

interface MovieSongsProps {
  movieTitle: string;
  releaseYear: string;
}

interface Song {
  id: string;
  title: string;
  thumbnail: string;
}

const MovieSongs: React.FC<MovieSongsProps> = ({ movieTitle, releaseYear }) => {
  const [songs, setSongs] = useState<Song[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchSongs = async () => {
      try {
        setLoading(true);
        // Extract year from release_date (e.g., "2023-09-07" -> "2023")
        const year = releaseYear ? releaseYear.split('-')[0] : '';
        const query = `${movieTitle} ${year} official song`;
        
        const response = await api.get(`/music/youtube/${encodeURIComponent(query)}`);
        
        if (response.data && response.data.results) {
          setSongs(response.data.results);
        } else {
          setError(true);
        }
      } catch (err) {
        console.error("Failed to fetch songs:", err);
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    if (movieTitle) {
      fetchSongs();
    }
  }, [movieTitle, releaseYear]);

  // Graceful degradation: If no songs or error, don't render anything to avoid breaking UI
  if (error || (!loading && songs.length === 0)) {
    return null;
  }

  return (
    <section className={styles.songsSection}>
      <h2 className={styles.sectionTitle}>Official Music Videos</h2>
      
      {loading ? (
        <div className={styles.loaderContainer}>
          <div className={styles.spinner}></div>
          <p>Finding tracks...</p>
        </div>
      ) : (
        <div className={styles.songsGrid}>
          {songs.map((song) => (
            <div key={song.id} className={styles.songCard}>
              <div className={styles.videoWrapper}>
                <iframe
                  src={`https://www.youtube.com/embed/${song.id}`}
                  title={song.title}
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                ></iframe>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
};

export default MovieSongs;
