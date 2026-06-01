import React, { useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell, X, CheckCheck, Trash2,
  TrendingUp, Sparkles, Film, Bookmark, Clapperboard,
} from 'lucide-react';
import { useNotifications, Notification, NotificationType } from '../context/NotificationContext';
import styles from './NotificationPanel.module.css';

// ─── Per-type config ───────────────────────────────────────────────────────────
// Each notification type gets its own circular app-icon style badge
// with a gradient background + white SVG icon (like iOS app icons)

const TYPE_CFG: Record<
  NotificationType,
  { icon: React.ReactNode; gradient: string; label: string; accent: string }
> = {
  trending: {
    icon: <TrendingUp size={18} strokeWidth={2.2} />,
    gradient: 'linear-gradient(145deg, #f97316 0%, #ef4444 100%)',
    accent: '#f97316',
    label: 'Trending',
  },
  recommendation: {
    icon: <Sparkles size={18} strokeWidth={2.2} />,
    gradient: 'linear-gradient(145deg, #8b5cf6 0%, #6366f1 100%)',
    accent: '#8b5cf6',
    label: 'AI Pick',
  },
  new_release: {
    icon: <Film size={18} strokeWidth={2.2} />,
    gradient: 'linear-gradient(145deg, #3b82f6 0%, #2563eb 100%)',
    accent: '#3b82f6',
    label: 'New',
  },
  watchlist: {
    icon: <Bookmark size={18} strokeWidth={2.2} />,
    gradient: 'linear-gradient(145deg, #22c55e 0%, #16a34a 100%)',
    accent: '#22c55e',
    label: 'Watchlist',
  },
  system: {
    icon: <Clapperboard size={18} strokeWidth={2.2} />,
    gradient: 'linear-gradient(145deg, #e50914 0%, #b91c1c 100%)',
    accent: '#e50914',
    label: 'MovieMind',
  },
};

// ─── Relative time ─────────────────────────────────────────────────────────────
function relativeTime(ts: number): string {
  const diff = Date.now() - ts;
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'Just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

// ─── Circular App-Icon (left side, like iOS/Spotify/Netflix) ──────────────────
const AppIcon: React.FC<{ type: NotificationType; size?: number }> = ({ type, size = 46 }) => {
  const cfg = TYPE_CFG[type];
  return (
    <div
      className={styles.appIcon}
      style={{
        width: size,
        height: size,
        background: cfg.gradient,
        // iOS-style inner shadow
        boxShadow: `0 3px 10px ${cfg.accent}55, inset 0 1px 0 rgba(255,255,255,0.25)`,
      }}
    >
      <span style={{ color: '#fff', display: 'flex', alignItems: 'center' }}>
        {cfg.icon}
      </span>
    </div>
  );
};

// ─── Single notification row ───────────────────────────────────────────────────
const NotifRow: React.FC<{ notif: Notification; onClose: () => void }> = ({ notif, onClose }) => {
  const { markAsRead, clearNotification } = useNotifications();
  const navigate = useNavigate();
  const cfg = TYPE_CFG[notif.type];

  const handleClick = () => {
    markAsRead(notif.id);
    if (notif.movieId) { navigate(`/movie/${notif.movieId}`); onClose(); }
  };

  // Strip leading label from title for cleaner display (e.g. "Trending Now: X" → keep it)
  const titleText = notif.title;
  const msgText   = notif.message;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, height: 0, overflow: 'hidden' }}
      transition={{ duration: 0.22, ease: 'easeOut' }}
      className={`${styles.row} ${!notif.isRead ? styles.rowUnread : ''}`}
      onClick={handleClick}
      role="button"
      tabIndex={0}
    >
      {/* ── Left: circular app icon OR poster with icon overlay ── */}
      <div className={styles.leftCol}>
        {notif.posterPath ? (
          <div className={styles.posterWrap}>
            {/* Movie thumbnail */}
            <img
              src={`https://image.tmdb.org/t/p/w92${notif.posterPath}`}
              alt=""
              className={styles.posterImg}
              onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
            />
            {/* Small circular app-icon overlapping bottom-right of poster */}
            <div
              className={styles.miniAppIcon}
              style={{ background: cfg.gradient, boxShadow: `0 2px 6px ${cfg.accent}88` }}
            >
              <span style={{ color: '#fff', display: 'flex' }}>
                {/* Smaller version of icon */}
                {React.cloneElement(cfg.icon as React.ReactElement, { size: 10, strokeWidth: 2.5 })}
              </span>
            </div>
          </div>
        ) : (
          <AppIcon type={notif.type} />
        )}
      </div>

      {/* ── Middle: text content ── */}
      <div className={styles.middleCol}>
        {/* Label + time row */}
        <div className={styles.topRow}>
          <span className={styles.label} style={{ color: cfg.accent }}>
            {cfg.label}
          </span>
          <span className={styles.time}>{relativeTime(notif.timestamp)}</span>
        </div>

        <p className={styles.title}>{titleText}</p>
        <p className={styles.msg}>{msgText}</p>
      </div>

      {/* ── Right: unread dot + dismiss ── */}
      <div className={styles.rightCol}>
        {!notif.isRead && (
          <span
            className={styles.unreadDot}
            style={{ background: cfg.accent, boxShadow: `0 0 5px ${cfg.accent}` }}
          />
        )}
        <button
          className={styles.dismissBtn}
          onClick={(e) => { e.stopPropagation(); clearNotification(notif.id); }}
          title="Dismiss"
          tabIndex={-1}
        >
          <X size={12} strokeWidth={2.5} />
        </button>
      </div>
    </motion.div>
  );
};

// ─── Main Panel ────────────────────────────────────────────────────────────────
interface Props { isOpen: boolean; onClose: () => void; }

const NotificationPanel: React.FC<Props> = ({ isOpen, onClose }) => {
  const { notifications, unreadCount, markAllAsRead, clearAll, isLoading } = useNotifications();
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) onClose();
    };
    if (isOpen) document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [isOpen, onClose]);

  return (
    <div className={styles.wrapper} ref={wrapRef}>

      {/* ── Bell trigger button ── */}
      <button
        className={`${styles.bellBtn} ${isOpen ? styles.bellOpen : ''}`}
        onClick={onClose}
        aria-label="Notifications"
        id="notification-bell-btn"
      >
        <Bell size={18} strokeWidth={2} />
        <AnimatePresence>
          {unreadCount > 0 && (
            <motion.span
              key="badge"
              className={styles.badge}
              initial={{ scale: 0, rotate: -20 }}
              animate={{ scale: 1, rotate: 0 }}
              exit={{ scale: 0 }}
              transition={{ type: 'spring', stiffness: 500, damping: 22 }}
            >
              {unreadCount > 9 ? '9+' : unreadCount}
            </motion.span>
          )}
        </AnimatePresence>
      </button>

      {/* ── Dropdown ── */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className={styles.panel}
            initial={{ opacity: 0, y: -8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            transition={{ type: 'spring', stiffness: 380, damping: 32 }}
          >

            {/* Header — Netflix / Spotify style */}
            <div className={styles.panelHeader}>
              <h3 className={styles.panelTitle}>Notifications</h3>
              <div className={styles.panelActions}>
                {unreadCount > 0 && (
                  <button className={styles.actionBtn} onClick={markAllAsRead} title="Mark all as read">
                    <CheckCheck size={14} strokeWidth={2.5} />
                    <span>Mark all read</span>
                  </button>
                )}
                {notifications.length > 0 && (
                  <button className={`${styles.actionBtn} ${styles.actionBtnDanger}`} onClick={clearAll} title="Clear all">
                    <Trash2 size={14} strokeWidth={2.5} />
                  </button>
                )}
              </div>
            </div>

            {/* Unread count pill */}
            {unreadCount > 0 && (
              <div className={styles.unreadBanner}>
                <span
                  className={styles.unreadPill}
                  style={{ background: 'rgba(229,9,20,0.12)', color: '#e50914', border: '1px solid rgba(229,9,20,0.25)' }}
                >
                  {unreadCount} unread
                </span>
              </div>
            )}

            {/* Body */}
            <div className={styles.body}>
              {/* Loading */}
              {isLoading && notifications.length === 0 && (
                <div className={styles.centerState}>
                  <div className={styles.spinner} />
                  <p>Fetching updates…</p>
                </div>
              )}

              {/* Empty */}
              {!isLoading && notifications.length === 0 && (
                <div className={styles.centerState}>
                  <div className={styles.emptyBell}>
                    <Bell size={28} strokeWidth={1.5} />
                  </div>
                  <p className={styles.emptyTitle}>All caught up!</p>
                  <span className={styles.emptySubtitle}>No new notifications right now</span>
                </div>
              )}

              {/* Rows */}
              <AnimatePresence initial={false}>
                {notifications.map(n => (
                  <NotifRow key={n.id} notif={n} onClose={onClose} />
                ))}
              </AnimatePresence>
            </div>

            {/* Footer */}
            {notifications.length > 0 && (
              <div className={styles.panelFooter}>
                <span>{notifications.length} notification{notifications.length !== 1 ? 's' : ''} total</span>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default NotificationPanel;
