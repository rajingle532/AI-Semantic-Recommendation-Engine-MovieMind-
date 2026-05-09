import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import styles from './TheatersPage.module.css';
import { FiSearch, FiMapPin, FiStar, FiInfo } from 'react-icons/fi';
import toast from 'react-hot-toast';

interface Theater {
  id: string;
  name: string;
  location: string;
  rating: number;
  tags: string[];
  distance: string;
}

const MOCK_THEATERS: Record<string, Theater[]> = {
  "pune": [
    { id: '1', name: "PVR ICON, Pavillion Mall", location: "Senapati Bapat Road", rating: 4.5, tags: ["IMAX", "Recliner", "Dolby Atmos"], distance: "2.5 km" },
    { id: '2', name: "INOX, Bund Garden", location: "Camp, Pune", rating: 4.2, tags: ["INSIGNIA", "4DX"], distance: "4.1 km" },
    { id: '3', name: "City Pride, Kothrud", location: "Kothrud", rating: 4.0, tags: ["Local Favorite", "Cheap"], distance: "1.2 km" },
    { id: '4', name: "Cinepolis, Seasons Mall", location: "Magarpatta City", rating: 4.4, tags: ["VIP", "Huge Screen"], distance: "8.5 km" },
  ],
  "mumbai": [
    { id: '5', name: "PVR Maison, Jio World Drive", location: "BKC, Mumbai", rating: 4.9, tags: ["Ultra Luxury", "Gourmet Food"], distance: "1.5 km" },
    { id: '6', name: "Inox, Nariman Point", location: "South Mumbai", rating: 4.6, tags: ["Sea View", "Premium"], distance: "12.0 km" },
    { id: '7', name: "Carnival Cinemas, Wadala", location: "Wadala", rating: 3.8, tags: ["IMAX", "Big Screen"], distance: "5.2 km" },
  ],
  "delhi": [
    { id: '8', name: "PVR Director's Cut", location: "Vasant Kunj", rating: 4.8, tags: ["Chef Crafted", "Luxury"], distance: "3.2 km" },
    { id: '9', name: "Delite Cinema", location: "Asaf Ali Road", rating: 4.3, tags: ["Heritage", "Single Screen"], distance: "0.5 km" },
  ]
};

const TheatersPage: React.FC = () => {
  const [city, setCity] = useState('pune');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [theaters, setTheaters] = useState<Theater[]>([]);

  useEffect(() => {
    setLoading(true);
    // Simulate API fetch
    setTimeout(() => {
      const cityLower = city.toLowerCase();
      const cityData = MOCK_THEATERS[cityLower] || MOCK_THEATERS['pune'];
      
      const filtered = cityData.filter(t => 
        t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.location.toLowerCase().includes(searchQuery.toLowerCase())
      );
      
      setTheaters(filtered);
      setLoading(false);
    }, 500);
  }, [city, searchQuery]);

  const handleBook = (theaterName: string) => {
    toast.success(`Redirecting to booking for ${theaterName}...`);
    // In a real app, this would open the booking modal or redirect
    setTimeout(() => {
      window.open(`https://in.bookmyshow.com/explore/movies-${city}`, '_blank');
    }, 1500);
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className={styles.container}
    >
      <header className={styles.header}>
        <div>
          <h1>Nearby Theaters</h1>
          <p>Find the best cinemas in your city</p>
        </div>
        
        <div className={styles.searchBox}>
          <FiSearch />
          <input 
            type="text" 
            placeholder="Search by theater or area..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </header>

      <div style={{ marginBottom: '2rem', display: 'flex', gap: '1rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
        {['Pune', 'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad'].map(c => (
          <button
            key={c}
            onClick={() => setCity(c.toLowerCase())}
            style={{
              padding: '0.5rem 1.5rem',
              borderRadius: '20px',
              border: 'none',
              background: city === c.toLowerCase() ? 'linear-gradient(to right, #ff4d4d, #f9cb28)' : 'rgba(255,255,255,0.1)',
              color: 'white',
              cursor: 'pointer',
              fontWeight: 600,
              whiteSpace: 'nowrap'
            }}
          >
            {c}
          </button>
        ))}
      </div>

      {loading ? (
        <div className={styles.loader}>Searching for best seats...</div>
      ) : (
        <div className={styles.theatersGrid}>
          {theaters.length > 0 ? (
            theaters.map((theater, index) => (
              <motion.div 
                key={theater.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={styles.theaterCard}
              >
                <div className={styles.theaterInfo}>
                  <h3>{theater.name}</h3>
                  <p><FiMapPin style={{ marginRight: '5px' }} /> {theater.location} ({theater.distance})</p>
                  <div className={styles.rating}>
                    <FiStar fill="currentColor" /> {theater.rating}
                  </div>
                </div>

                <div className={styles.features}>
                  {theater.tags.map(tag => (
                    <span key={tag} className={styles.featureTag}>{tag}</span>
                  ))}
                </div>

                <button 
                  className={styles.bookBtn}
                  onClick={() => handleBook(theater.name)}
                >
                  Book Tickets
                </button>
              </motion.div>
            ))
          ) : (
            <div className={styles.loader}>No theaters found in {city}. Try another city!</div>
          )}
        </div>
      )}
    </motion.div>
  );
};

export default TheatersPage;
