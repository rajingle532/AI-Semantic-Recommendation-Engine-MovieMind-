import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Calendar, MapPin, Star, ArrowLeft } from 'lucide-react';
import api from '../services/api';
import MovieGrid from '../components/MovieGrid';
import PageTransition from '../components/PageTransition';
import styles from './PersonDetailPage.module.css';

interface Person {
  id: number;
  name: string;
  biography: string;
  profile_path: string;
  birthday: string;
  place_of_birth: string;
  known_for_department: string;
}

const PersonDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [person, setPerson] = useState<Person | null>(null);
  const [movies, setMovies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPersonData = async () => {
      setLoading(true);
      try {
        const [personRes, moviesRes] = await Promise.all([
          api.get(`/movies/person/${id}`),
          api.get(`/movies/person/${id}/movies`)
        ]);
        setPerson(personRes.data);
        setMovies(moviesRes.data);
      } catch (err) {
        console.error("Failed to fetch person data", err);
      } finally {
        setLoading(false);
      }
    };

    fetchPersonData();
    window.scrollTo(0, 0);
  }, [id]);

  if (loading) return <div className="loading-container"><div className="loader"></div></div>;
  if (!person) return <div className="error-container">Person not found</div>;

  const profileUrl = person.profile_path 
    ? `https://image.tmdb.org/t/p/w500${person.profile_path}`
    : 'https://via.placeholder.com/500x750?text=No+Photo';

  return (
    <PageTransition>
      <div className={styles.personPage}>
        <Link to="/" className={styles.backBtn}>
          <ArrowLeft size={20} /> Back to Movies
        </Link>

        <div className={styles.header}>
          <motion.div 
            className={styles.profileWrapper}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <img src={profileUrl} alt={person.name} className={styles.profileImg} />
          </motion.div>

          <div className={styles.info}>
            <motion.h1 
              className={styles.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              {person.name}
            </motion.h1>

            <div className={styles.meta}>
              {person.birthday && (
                <span className={styles.metaItem}>
                  <Calendar size={18} /> Born: {person.birthday}
                </span>
              )}
              {person.place_of_birth && (
                <span className={styles.metaItem}>
                  <MapPin size={18} /> {person.place_of_birth}
                </span>
              )}
            </div>

            <div className={styles.bioSection}>
              <h3>Biography</h3>
              <p className={styles.biography}>
                {person.biography || "No biography available for this person."}
              </p>
            </div>
          </div>
        </div>

        <section className={styles.creditsSection}>
          <h2 className={styles.sectionTitle}>Known For</h2>
          {movies.length > 0 ? (
            <MovieGrid movies={movies} />
          ) : (
            <p className={styles.noMovies}>No movies found for this person.</p>
          )}
        </section>
      </div>
    </PageTransition>
  );
};

export default PersonDetailPage;
