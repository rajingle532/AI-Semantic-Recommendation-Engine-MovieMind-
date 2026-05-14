import React, { useEffect, useState } from 'react';
import { Music, Play, Pause, ExternalLink } from 'lucide-react';
import api from '../services/api';
import styles from './SpotifySoundtrack.module.css';

interface Track {
  id: string;
  name: string;
  preview_url: string;
  duration_ms: number;
  track_number: number;
}

interface SoundtrackData {
  album_name: string;
  album_image: string;
  spotify_url: string;
  tracks: Track[];
}

interface SpotifySoundtrackProps {
  movieTitle: string;
}

const SpotifySoundtrack: React.FC<SpotifySoundtrackProps> = ({ movieTitle }) => {
  const [data, setData] = useState<SoundtrackData | null>(null);
  const [loading, setLoading] = useState(true);
  const [playingId, setPlayingId] = useState<string | null>(null);
  const audioRef = React.useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    const fetchSoundtrack = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/music/spotify/album/${encodeURIComponent(movieTitle)}`);
        if (response.data && response.data.tracks && response.data.tracks.length > 0) {
          setData(response.data);
        }
      } catch (err) {
        console.error("Failed to fetch Spotify soundtrack:", err);
      } finally {
        setLoading(false);
      }
    };

    if (movieTitle) {
      fetchSoundtrack();
    }
  }, [movieTitle]);

  const togglePlay = (track: Track) => {
    if (playingId === track.id) {
      audioRef.current?.pause();
      setPlayingId(null);
    } else {
      if (audioRef.current) {
        audioRef.current.src = track.preview_url;
        audioRef.current.play();
        setPlayingId(track.id);
      }
    }
  };

  const handleEnded = () => {
    setPlayingId(null);
  };

  if (!data) return (
    <section className={styles.soundtrackSection}>
      <h2 className={styles.sectionTitle}>Official Soundtrack</h2>
      <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '1rem' }}>
        {loading ? "Searching Spotify..." : "Spotify soundtrack not available for this movie."}
      </p>
    </section>
  );

  return (
    <section className={styles.soundtrackSection}>
      <div className={styles.header}>
        <div className={styles.albumArt}>
          <img src={data.album_image} alt={data.album_name} />
          <div className={styles.overlay}>
             <Music size={32} color="white" />
          </div>
        </div>
        <div className={styles.info}>
          <h2 className={styles.sectionTitle}>Official Soundtrack</h2>
          <p className={styles.albumName}>{data.album_name}</p>
          <a href={data.spotify_url} target="_blank" rel="noopener noreferrer" className={styles.spotifyLink}>
            <ExternalLink size={16} /> Open on Spotify
          </a>
        </div>
      </div>

      <div className={styles.trackList}>
        {data.tracks.map((track) => (
          <div 
            key={track.id} 
            className={`${styles.trackItem} ${playingId === track.id ? styles.active : ''}`}
            onClick={() => togglePlay(track)}
          >
            <div className={styles.playBtn}>
              {playingId === track.id ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" />}
            </div>
            <div className={styles.trackInfo}>
              <span className={styles.trackNumber}>{track.track_number}.</span>
              <span className={styles.trackName}>{track.name}</span>
            </div>
            <span className={styles.trackDuration}>
              {Math.floor(track.duration_ms / 60000)}:
              {Math.floor((track.duration_ms % 60000) / 1000).toString().padStart(2, '0')}
            </span>
          </div>
        ))}
      </div>

      <audio ref={audioRef} onEnded={handleEnded} />
    </section>
  );
};

export default SpotifySoundtrack;
