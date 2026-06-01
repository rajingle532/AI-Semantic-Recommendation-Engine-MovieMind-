import React, { createContext, useState, useContext, useEffect, useCallback, useRef } from 'react';
import api from '../services/api';

// ─── Types ────────────────────────────────────────────────────────────────────

export type NotificationType = 'new_release' | 'recommendation' | 'trending' | 'watchlist' | 'system';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  movieId?: number;
  posterPath?: string;
  timestamp: number;
  isRead: boolean;
}

interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearNotification: (id: string) => void;
  clearAll: () => void;
  addNotification: (notif: Omit<Notification, 'id' | 'timestamp' | 'isRead'>) => void;
  isLoading: boolean;
}

// ─── Context ──────────────────────────────────────────────────────────────────

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

const STORAGE_KEY = 'moviemind_notifications';
const MAX_NOTIFS   = 20;
const REFRESH_MS   = 10 * 60 * 1000; // 10 min

const genId = () => `n_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;

// ─── Provider ────────────────────────────────────────────────────────────────

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading]         = useState(false);
  const intervalRef  = useRef<ReturnType<typeof setInterval> | null>(null);
  const fetchedOnce  = useRef(false);

  // ── Restore from localStorage (filter out >48h old) ─────────────────────
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed: Notification[] = JSON.parse(raw);
        const cutoff = Date.now() - 48 * 60 * 60 * 1000;
        setNotifications(parsed.filter(n => n.timestamp > cutoff));
      }
    } catch { /* ignore */ }
  }, []);

  // ── Persist whenever notifications change ────────────────────────────────
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(notifications));
  }, [notifications]);

  // ── Core add helper (deduplicates within 30 min) ─────────────────────────
  const addNotification = useCallback(
    (notif: Omit<Notification, 'id' | 'timestamp' | 'isRead'>) => {
      setNotifications(prev => {
        const cutoff = Date.now() - 30 * 60 * 1000;
        const dup = prev.some(
          n => n.title === notif.title && n.type === notif.type && n.timestamp > cutoff
        );
        if (dup) return prev;
        const fresh: Notification = {
          ...notif,
          id: genId(),
          timestamp: Date.now(),
          isRead: false,
        };
        return [fresh, ...prev].slice(0, MAX_NOTIFS);
      });
    },
    []
  );

  // ── Main fetch — uses CORRECT backend endpoints ──────────────────────────
  const fetchNotifications = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      console.log('[Notif] No token — skipping fetch');
      return;
    }

    setIsLoading(true);
    console.log('[Notif] Fetching smart notifications…');

    try {
      // ── 1. Trending movies (public endpoint, always works) ────────────
      const trendRes = await api.get('/movies/trending', { params: { page: 1 } });
      const trending: any[] = Array.isArray(trendRes.data)
        ? trendRes.data
        : (trendRes.data?.results ?? []);

      trending.slice(0, 3).forEach((m: any) => {
        addNotification({
          type: 'trending',
          title: `Trending Now: ${m.title}`,
          message: `Rating ${m.vote_average?.toFixed(1) ?? 'N/A'} · Currently trending worldwide`,
          movieId: m.id,
          posterPath: m.poster_path || m.backdrop_path || undefined,
        });
      });
      console.log('[Notif] ✅ Trending:', trending.slice(0, 3).map((m:any) => m.title));

      // ── 2. Smart AI recommendations (/recommend/smart/me) ────────────
      try {
        const recRes = await api.get('/recommend/smart/me');
        const recs: any[] = recRes.data?.recommendations ?? [];
        if (recs.length > 0) {
          const pick = recs[0];
          addNotification({
            type: 'recommendation',
            title: `AI Pick for You: ${pick.title}`,
            message: 'Handpicked by MovieMind AI based on your taste profile',
            movieId: pick.id ?? pick.movie_id,
            posterPath: pick.poster_path || undefined,
          });
          console.log('[Notif] ✅ AI Pick:', pick.title);
        }
      } catch (e) {
        console.warn('[Notif] AI recommendations skipped:', e);
      }

      // ── 3. Watchlist update (/watchlist/my) ───────────────────────────
      try {
        const wlRes = await api.get('/watchlist/my');
        const items: any[] = wlRes.data?.watchlist ?? [];
        if (items.length > 0) {
          const pick = items[Math.floor(Math.random() * Math.min(items.length, 5))];
          const title = pick.title || pick.movie_title || 'A movie';
          addNotification({
            type: 'watchlist',
            title: `Watchlist: ${title}`,
            message: 'One of your saved movies is trending — great time to watch!',
            movieId: pick.movie_id || pick.id,
            posterPath: pick.poster_path || undefined,
          });
          console.log('[Notif] ✅ Watchlist pick:', title);
        }
      } catch (e) {
        console.warn('[Notif] Watchlist skipped:', e);
      }

      // ── 4. System welcome (one-time only) ────────────────────────────
      setNotifications(prev => {
        if (prev.some(n => n.type === 'system')) return prev;
        const welcome: Notification = {
          id: genId(),
          type: 'system',
          title: 'Welcome to MovieMind AI!',
          message: 'Your personalized cinema hub is ready — explore, rate, and discover!',
          timestamp: Date.now() - 500,
          isRead: false,
        };
        return [welcome, ...prev].slice(0, MAX_NOTIFS);
      });

    } catch (err) {
      console.error('[Notif] Fetch failed:', err);
    } finally {
      setIsLoading(false);
    }
  }, [addNotification]);

  // ── Watch for token changes (login/logout) and re-trigger fetch ──────────
  useEffect(() => {
    const checkAndFetch = () => {
      const token = localStorage.getItem('token');

      // Clear old interval
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }

      if (token && !fetchedOnce.current) {
        fetchedOnce.current = true;
        // Small delay so auth state settles
        setTimeout(fetchNotifications, 1500);
        // Periodic refresh
        intervalRef.current = setInterval(fetchNotifications, REFRESH_MS);
      } else if (!token) {
        // User logged out — reset so next login fetches fresh
        fetchedOnce.current = false;
      }
    };

    // Run on mount
    checkAndFetch();

    // Also listen for storage events (token added after login)
    const onStorage = (e: StorageEvent) => {
      if (e.key === 'token') {
        fetchedOnce.current = false;
        checkAndFetch();
      }
    };
    window.addEventListener('storage', onStorage);

    // Poll every 3s briefly in case storage event doesn't fire (same-tab login)
    const pollId = setInterval(() => {
      const token = localStorage.getItem('token');
      if (token && !fetchedOnce.current) {
        fetchedOnce.current = false;
        checkAndFetch();
      }
    }, 3000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      window.removeEventListener('storage', onStorage);
      clearInterval(pollId);
    };
  }, [fetchNotifications]);

  // ── Actions ───────────────────────────────────────────────────────────────

  const markAsRead = useCallback((id: string) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, isRead: true } : n));
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, isRead: true })));
  }, []);

  const clearNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  const unreadCount = notifications.filter(n => !n.isRead).length;

  return (
    <NotificationContext.Provider value={{
      notifications, unreadCount,
      markAsRead, markAllAsRead,
      clearNotification, clearAll,
      addNotification, isLoading,
    }}>
      {children}
    </NotificationContext.Provider>
  );
};

// ─── Hook ─────────────────────────────────────────────────────────────────────

export const useNotifications = () => {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error('useNotifications must be used within NotificationProvider');
  return ctx;
};
