import axios from 'axios';

const baseURL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api` 
  : '/api';

console.log(`API Base URL: ${baseURL}`);

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json'
  }
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers = config.headers || {};
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const getTrendingTV = (page = 1) => api.get(`/tv/trending?page=${page}`);
export const searchTV = (query: string, page = 1) => api.get(`/tv/search?q=${query}&page=${page}`);
export const getTVDetails = (id: number) => api.get(`/tv/${id}`);
export const getTVSeason = (id: number, season: number) => api.get(`/tv/${id}/season/${season}`);
export const getTVByLanguage = (code: string, page = 1) => api.get(`/tv/language/${code}?page=${page}`);

export default api;
