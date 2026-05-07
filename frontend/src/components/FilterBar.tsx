import React from 'react';
import { Calendar, Star, Languages, X } from 'lucide-react';
import styles from './FilterBar.module.css';

interface FilterBarProps {
  filters: {
    year: string;
    minRating: string;
    language: string;
  };
  setFilters: (filters: any) => void;
  onClear: () => void;
}

const FilterBar: React.FC<FilterBarProps> = ({ filters, setFilters, onClear }) => {
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 30 }, (_, i) => (currentYear - i).toString());
  
  const ratings = ['9+', '8+', '7+', '6+', '5+'];
  
  const languages = [
    { code: 'all', name: 'All Languages' },
    { code: 'en', name: 'English' },
    { code: 'hi', name: 'Hindi' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'ja', name: 'Japanese' },
    { code: 'ko', name: 'Korean' },
  ];

  const hasFilters = filters.year || filters.minRating !== '0' || filters.language !== 'all';

  return (
    <div className={styles.filterBar}>
      <div className={styles.group}>
        <div className={styles.label}>
          <Calendar size={16} /> <span>Year</span>
        </div>
        <select 
          value={filters.year} 
          onChange={(e) => setFilters({ ...filters, year: e.target.value })}
          className={styles.select}
        >
          <option value="">All Years</option>
          {years.map(y => <option key={y} value={y}>{y}</option>)}
        </select>
      </div>

      <div className={styles.group}>
        <div className={styles.label}>
          <Star size={16} /> <span>Rating</span>
        </div>
        <select 
          value={filters.minRating} 
          onChange={(e) => setFilters({ ...filters, minRating: e.target.value.replace('+', '') })}
          className={styles.select}
        >
          <option value="0">Any Rating</option>
          {ratings.map(r => <option key={r} value={r.replace('+', '')}>{r}</option>)}
        </select>
      </div>

      <div className={styles.group}>
        <div className={styles.label}>
          <Languages size={16} /> <span>Language</span>
        </div>
        <select 
          value={filters.language} 
          onChange={(e) => setFilters({ ...filters, language: e.target.value })}
          className={styles.select}
        >
          {languages.map(l => <option key={l.code} value={l.code}>{l.name}</option>)}
        </select>
      </div>

      {hasFilters && (
        <button className={styles.clearBtn} onClick={onClear}>
          <X size={16} /> Clear Filters
        </button>
      )}
    </div>
  );
};

export default FilterBar;
