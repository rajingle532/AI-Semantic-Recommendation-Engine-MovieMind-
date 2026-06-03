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
  isPinned?: boolean;
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
  // New: bell shake state
  isBellShaking: boolean;
  // New: browser push permission
  pushPermission: NotificationPermission | 'unsupported';
  requestPushPermission: () => Promise<void>;
  // New: scheduler — next scheduled fetch time
  nextScheduledTime: Date | null;
}

// ─── Context ──────────────────────────────────────────────────────────────────

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

const STORAGE_KEY    = 'moviemind_notifications';
const PERM_KEY       = 'moviemind_push_perm_asked';
const SCHED_KEY      = 'moviemind_notif_last_sched';
const MAX_NOTIFS     = 20;
const REFRESH_MS     = 10 * 60 * 1000; // 10 min regular refresh
const MORNING_HOUR   = 9;              // 9 AM daily scheduler
const EVENING_HOUR   = 20;            // 8 PM daily scheduler

const genId = () => `n_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;

// ─── Browser Push helper ──────────────────────────────────────────────────────

function sendBrowserPush(title: string, body: string, icon?: string) {
  if (!('Notification' in window) || Notification.permission !== 'granted') return;
  try {
    new Notification(title, {
      body,
      icon: icon || '/logo.png',
      badge: '/logo.png',
      silent: false,
    });
  } catch { /* some browsers block programmatic push */ }
}

// ─── Provider ────────────────────────────────────────────────────────────────

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading]         = useState(false);
  const [isBellShaking, setIsBellShaking] = useState(false);
  const [nextScheduledTime, setNextScheduledTime] = useState<Date | null>(null);
  const [pushPermission, setPushPermission] = useState<NotificationPermission | 'unsupported'>(
    'Notification' in window ? Notification.permission : 'unsupported'
  );

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const schedRef    = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fetchedOnce = useRef(false);
  const prevCount   = useRef(0);

  // ── Restore from localStorage ─────────────────────────────────────────────
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed: Notification[] = JSON.parse(raw);
        const cutoff = Date.now() - 48 * 60 * 60 * 1000;
        const valid = parsed.filter(n => n.timestamp > cutoff);
        setNotifications(valid);
        prevCount.current = valid.filter(n => !n.isRead).length;
      }
    } catch { /* ignore */ }
  }, []);

  // ── Persist on change ─────────────────────────────────────────────────────
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(notifications));
  }, [notifications]);

  // ── Bell shake + browser push when new notifications arrive ──────────────
  useEffect(() => {
    const unread = notifications.filter(n => !n.isRead).length;
    if (unread > prevCount.current) {
      // Shake the bell
      setIsBellShaking(true);
      setTimeout(() => setIsBellShaking(false), 820);

      // Browser push for the newest notification
      const newest = notifications[0];
      if (newest && !newest.isRead) {
        const posterUrl = newest.posterPath
          ? `https://image.tmdb.org/t/p/w92${newest.posterPath}`
          : undefined;
        sendBrowserPush(newest.title, newest.message, posterUrl);
      }
    }
    prevCount.current = unread;
  }, [notifications]);

  // ── Add helper (deduplicates within 30 min) ───────────────────────────────
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

  // ── Main fetch ────────────────────────────────────────────────────────────
  const fetchNotifications = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (!token) return;

    setIsLoading(true);
    console.log('[Notif] Fetching smart notifications…');

    try {
      // 1. Trending
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

      // 2. AI Recommendations
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
        }
      } catch { /* skip */ }

      // 3. Watchlist
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
        }
      } catch { /* skip */ }

      // 4. System welcome (once only)
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

      // Record last scheduled fetch time
      localStorage.setItem(SCHED_KEY, String(Date.now()));

    } catch (err) {
      console.error('[Notif] Fetch failed:', err);
    } finally {
      setIsLoading(false);
    }
  }, [addNotification]);

  // ── Daily Scheduler — fetch at 9AM and 8PM ───────────────────────────────
  const scheduleNextFetch = useCallback(() => {
    if (schedRef.current) clearTimeout(schedRef.current);

    const now = new Date();
    const candidates = [MORNING_HOUR, EVENING_HOUR].map(h => {
      const d = new Date();
      d.setHours(h, 0, 0, 0);
      if (d <= now) d.setDate(d.getDate() + 1); // push to tomorrow if past
      return d;
    });

    // Pick the soonest upcoming slot
    const next = candidates.reduce((a, b) => (a < b ? a : b));
    const msUntil = next.getTime() - now.getTime();

    setNextScheduledTime(next);
    console.log(`[Notif] Next scheduled fetch at ${next.toLocaleTimeString()} (in ${Math.round(msUntil / 60000)} min)`);

    schedRef.current = setTimeout(() => {
      fetchNotifications();
      scheduleNextFetch(); // re-schedule after firing
    }, msUntil);
  }, [fetchNotifications]);

  // ── Token watcher + initial fetch + scheduler setup ───────────────────────
  useEffect(() => {
    const checkAndFetch = () => {
      const token = localStorage.getItem('token');
      if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }

      if (token && !fetchedOnce.current) {
        fetchedOnce.current = true;
        setTimeout(fetchNotifications, 1500);
        intervalRef.current = setInterval(fetchNotifications, REFRESH_MS);
        scheduleNextFetch();
      } else if (!token) {
        fetchedOnce.current = false;
        if (schedRef.current) clearTimeout(schedRef.current);
        setNextScheduledTime(null);
      }
    };

    checkAndFetch();

    const onStorage = (e: StorageEvent) => {
      if (e.key === 'token') { fetchedOnce.current = false; checkAndFetch(); }
    };
    window.addEventListener('storage', onStorage);

    const pollId = setInterval(() => {
      const token = localStorage.getItem('token');
      if (token && !fetchedOnce.current) { fetchedOnce.current = false; checkAndFetch(); }
    }, 3000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (schedRef.current) clearTimeout(schedRef.current);
      window.removeEventListener('storage', onStorage);
      clearInterval(pollId);
    };
  }, [fetchNotifications, scheduleNextFetch]);

  // ── Request browser push permission ──────────────────────────────────────
  const requestPushPermission = useCallback(async () => {
    if (!('Notification' in window)) return;
    try {
      const result = await Notification.requestPermission();
      setPushPermission(result);
      localStorage.setItem(PERM_KEY, 'asked');
      if (result === 'granted') {
        sendBrowserPush('MovieMind Notifications Enabled!', 'You\'ll now get movie alerts from MovieMind AI.');
      }
    } catch { /* ignore */ }
  }, []);

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
      isBellShaking,
      pushPermission,
      requestPushPermission,
      nextScheduledTime,
    }}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error('useNotifications must be used within NotificationProvider');
  return ctx;
};
