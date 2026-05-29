import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MapPin, 
  Calendar, 
  ChevronDown, 
  ChevronUp, 
  ExternalLink, 
  Ticket, 
  Info, 
  Clock, 
  Sparkles, 
  AlertCircle 
} from 'lucide-react';
import api from '../services/api';
import PageTransition from '../components/PageTransition';
import styles from './TicketsPage.module.css';

interface Movie {
  id: number;
  title: string;
  overview: string;
  poster_path: string;
  backdrop_path: string;
  vote_average: number;
  release_date: string;
  genres: string[];
  language: string;
}

interface ShowtimeTime {
  time: string;
  status: 'Available' | 'Filling Fast' | 'Houseful';
}

interface ShowtimeShow {
  format: string;
  timings: ShowtimeTime[];
}

interface ShowtimeTheater {
  name: string;
  booking_link: string;
  shows: ShowtimeShow[];
}

interface ShowtimeDay {
  day: string;
  theaters: ShowtimeTheater[];
}

interface ShowtimesResponse {
  movie: string;
  city: string;
  showtimes: ShowtimeDay[];
  bms_link: string;
  paytm_link: string;
  google_search_link?: string;
}

const TicketsPage: React.FC = () => {
  const [cities, setCities] = useState<string[]>(['Pune', 'Mumbai', 'Delhi NCR', 'Bangalore', 'Hyderabad']);
  const [selectedCity, setSelectedCity] = useState<string>('Pune');
  const [cityInput, setCityInput] = useState<string>('Pune');
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loadingMovies, setLoadingMovies] = useState<boolean>(true);
  const [activeMovieId, setActiveMovieId] = useState<number | null>(null);
  
  // Showtimes state
  const [showtimesData, setShowtimesData] = useState<ShowtimesResponse | null>(null);
  const [loadingShowtimes, setLoadingShowtimes] = useState<boolean>(false);
  const [selectedDayIndex, setSelectedDayIndex] = useState<number>(0);

  // Fetch Cities on mount
  useEffect(() => {
    const fetchCities = async () => {
      try {
        const { data } = await api.get('/tickets/cities');
        if (data && Array.isArray(data)) {
          setCities(data);
        }
      } catch (err) {
        console.error('Error fetching cities:', err);
      }
    };
    fetchCities();
  }, []);

  // Fetch Now Playing Movies when city changes
  useEffect(() => {
    const fetchNowPlaying = async () => {
      try {
        setLoadingMovies(true);
        setActiveMovieId(null);
        setShowtimesData(null);
        
        const { data } = await api.get(`/tickets/now-playing?city=${encodeURIComponent(selectedCity)}`);
        if (data && data.results) {
          setMovies(data.results);
        }
      } catch (err) {
        console.error('Error fetching now playing movies:', err);
      } finally {
        setLoadingMovies(false);
      }
    };
    
    fetchNowPlaying();
  }, [selectedCity]);

  // Fetch Showtimes for a selected movie
  const handleMovieClick = async (movie: Movie) => {
    if (activeMovieId === movie.id) {
      // Toggle close
      setActiveMovieId(null);
      setShowtimesData(null);
      return;
    }

    setActiveMovieId(movie.id);
    setShowtimesData(null);
    setLoadingShowtimes(true);
    setSelectedDayIndex(0);

    try {
      const { data } = await api.get(
        `/tickets/showtimes?movie=${encodeURIComponent(movie.title)}&city=${encodeURIComponent(selectedCity)}`
      );
      setShowtimesData(data);
    } catch (err) {
      console.error('Error fetching showtimes:', err);
    } finally {
      setLoadingShowtimes(false);
    }
  };

  // Status Color Resolver
  const getStatusClass = (status: string) => {
    switch (status) {
      case 'Houseful':
        return styles.statusHouseful;
      case 'Filling Fast':
        return styles.statusFilling;
      case 'Available':
      default:
        return styles.statusAvailable;
    }
  };

  return (
    <PageTransition>
      <div className={styles.page}>
        {/* Decorative Glow */}
        <div className={styles.heroGlow}></div>

        {/* Hero Section */}
        <header className={styles.hero}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6 }}
            className={styles.badgeContainer}
          >
            <span className={styles.heroBadge}>
              <Ticket size={14} /> LIVE BOOKING
            </span>
          </motion.div>
          <motion.h1
            className={styles.title}
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            Smart Ticket <span className={styles.accent}>Booking</span>
          </motion.h1>
          <motion.p
            className={styles.subtitle}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            Check real-time theater showtimes and ticket availability near you in just one click!
          </motion.p>
        </header>

        {/* Controls / Filter Bar */}
        <div className={styles.filterBar}>
          <div className={styles.citySelector}>
            <MapPin size={18} className={styles.mapPin} />
            <span className={styles.cityLabel}>Select City:</span>
            <div className={styles.cityInputWrapper}>
              <input
                type="text"
                list="cities-list"
                value={cityInput}
                onChange={(e) => {
                  const val = e.target.value;
                  setCityInput(val);
                  if (cities.includes(val)) {
                    setSelectedCity(val);
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    setSelectedCity(cityInput.trim());
                  }
                }}
                placeholder="Type or select city..."
                className={styles.cityInput}
              />
              <datalist id="cities-list">
                {cities.map((city) => (
                  <option key={city} value={city} />
                ))}
              </datalist>
              <button
                onClick={() => setSelectedCity(cityInput.trim())}
                className={styles.citySearchBtn}
              >
                Search
              </button>
            </div>
          </div>
          
          <div className={styles.offerBadge}>
            <Sparkles size={14} className={styles.sparkIcon} />
            <span>ICICI Buy 1 Get 1 Live Today!</span>
          </div>
        </div>

        {/* Movies Grid */}
        {loadingMovies ? (
          <div className={styles.loader}>
            <div className={styles.spinner}></div>
            <p>Fetching movies currently playing in {selectedCity}...</p>
          </div>
        ) : movies.length === 0 ? (
          <div className={styles.noMovies}>
            <AlertCircle size={48} className={styles.noMoviesIcon} />
            <h2>No movies playing currently</h2>
            <p>Try switching to another city or check back later.</p>
          </div>
        ) : (
          <div className={styles.movieGrid}>
            {movies.map((movie) => {
              const isActive = activeMovieId === movie.id;
              
              return (
                <div 
                  key={movie.id} 
                  className={`${styles.movieWrapper} ${isActive ? styles.movieWrapperActive : ''}`}
                >
                  <motion.div
                    className={styles.movieCard}
                    layoutId={`movie-card-${movie.id}`}
                    onClick={() => handleMovieClick(movie)}
                  >
                    <div className={styles.posterContainer}>
                      <img
                        src={movie.poster_path}
                        alt={movie.title}
                        className={styles.poster}
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = "https://via.placeholder.com/500x750?text=No+Poster";
                        }}
                      />
                      <div className={styles.ratingBadge}>
                        ★ {movie.vote_average.toFixed(1)}
                      </div>
                    </div>
                    
                    <div className={styles.movieInfo}>
                      <h3 className={styles.movieTitle}>{movie.title}</h3>
                      <div className={styles.metaRow}>
                        <span className={styles.langTag}>{movie.language}</span>
                        <span className={styles.releaseDate}>{movie.release_date.split('-')[0]}</span>
                      </div>
                      
                      <div className={styles.genreRow}>
                        {movie.genres.slice(0, 3).map((g) => (
                          <span key={g} className={styles.genreTag}>{g}</span>
                        ))}
                      </div>

                      <button 
                        className={`${styles.showtimeBtn} ${isActive ? styles.showtimeBtnActive : ''}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleMovieClick(movie);
                        }}
                      >
                        {isActive ? (
                          <>Close Details <ChevronUp size={16} /></>
                        ) : (
                          <>Check Showtimes <ChevronDown size={16} /></>
                        )}
                      </button>
                    </div>
                  </motion.div>

                  {/* Showtimes & Details Accordion */}
                  <AnimatePresence>
                    {isActive && (
                      <motion.div
                        className={styles.accordionContent}
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <div className={styles.accordionInner}>
                          {/* Overview Block */}
                          <div className={styles.movieOverview}>
                            <h4>Overview</h4>
                            <p>{movie.overview || "No overview available for this film."}</p>
                          </div>

                          <hr className={styles.divider} />

                          {/* Showtimes Section */}
                          <div className={styles.showtimesSection}>
                            <div className={styles.sectionHeader}>
                              <Calendar size={18} />
                              <h4>Showtimes in {selectedCity}</h4>
                            </div>

                            {loadingShowtimes ? (
                              <div className={styles.showtimesLoader}>
                                <div className={styles.miniSpinner}></div>
                                <p>Searching live showtimes from SerpApi...</p>
                              </div>
                            ) : showtimesData && showtimesData.showtimes && showtimesData.showtimes.length > 0 ? (
                              <>
                                {/* Days Selector tabs */}
                                <div className={styles.dayTabs}>
                                  {showtimesData.showtimes.map((dayBlock, index) => (
                                    <button
                                      key={dayBlock.day}
                                      className={`${styles.dayTab} ${selectedDayIndex === index ? styles.dayTabActive : ''}`}
                                      onClick={() => setSelectedDayIndex(index)}
                                    >
                                      {dayBlock.day}
                                    </button>
                                  ))}
                                </div>

                                {/* Theaters and Times slots */}
                                <div className={styles.theatersContainer}>
                                  {showtimesData.showtimes[selectedDayIndex].theaters.map((theater, tIndex) => (
                                    <div key={tIndex} className={styles.theaterRow}>
                                      <div className={styles.theaterDetails}>
                                        <h5 className={styles.theaterName}>{theater.name}</h5>
                                        <div className={styles.showsBlock}>
                                          {theater.shows.map((show, sIndex) => (
                                            <div key={sIndex} className={styles.showVariant}>
                                              <span className={styles.formatLabel}>{show.format}</span>
                                              <div className={styles.timingsGrid}>
                                                {show.timings.map((timeObj, timeIndex) => (
                                                  <div 
                                                    key={timeIndex} 
                                                    className={`${styles.timingSlot} ${getStatusClass(timeObj.status)}`}
                                                    title={`Status: ${timeObj.status}`}
                                                  >
                                                    <span className={styles.slotTime}>{timeObj.time}</span>
                                                    <span className={styles.slotIndicator}></span>
                                                  </div>
                                                ))}
                                              </div>
                                            </div>
                                          ))}
                                        </div>
                                      </div>

                                      <div className={styles.bookingAction}>
                                        <a
                                          href={theater.booking_link}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className={styles.bmsBookBtn}
                                        >
                                          Book Now <ExternalLink size={14} />
                                        </a>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </>
                            ) : (
                              <div className={styles.noShowtimes}>
                                <AlertCircle size={32} className={styles.noMoviesIcon} />
                                <p>Booking links are ready for "{movie.title}" in {selectedCity}!</p>
                                <div className={styles.directLinks}>
                                  <a
                                    href={showtimesData?.bms_link || `https://in.bookmyshow.com`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className={styles.directBmsLink}
                                  >
                                    Book on BookMyShow <ExternalLink size={14} />
                                  </a>
                                  <a
                                    href={showtimesData?.paytm_link || `https://paytm.com/movies`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className={styles.directPaytmLink}
                                  >
                                    Book on Paytm <ExternalLink size={14} />
                                  </a>
                                </div>
                              </div>
                            )}

                            {/* Legend */}
                            {showtimesData && showtimesData.showtimes && showtimesData.showtimes.length > 0 && (
                              <div className={styles.legend}>
                                <div className={styles.legendItem}>
                                  <span className={`${styles.legendColor} ${styles.bgAvailable}`}></span>
                                  <span>Available</span>
                                </div>
                                <div className={styles.legendItem}>
                                  <span className={`${styles.legendColor} ${styles.bgFilling}`}></span>
                                  <span>Filling Fast</span>
                                </div>
                                <div className={styles.legendItem}>
                                  <span className={`${styles.legendColor} ${styles.bgHouseful}`}></span>
                                  <span>Houseful</span>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </PageTransition>
  );
};

export default TicketsPage;
