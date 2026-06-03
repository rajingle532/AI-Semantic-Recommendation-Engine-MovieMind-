import React, { useRef, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence, useMotionValue, useTransform, useAnimation } from 'framer-motion';
import {
  Bell, X, CheckCheck, Trash2,
  TrendingUp, Sparkles, Film, Bookmark, Clapperboard,
  BellRing, Clock, Shield,
} from 'lucide-react';
import { useNotifications, Notification, NotificationType } from '../context/NotificationContext';
import styles from './NotificationPanel.module.css';

// ─── Per-type config ──────────────────────────────────────────────────────────

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

// ─── Helpers ──────────────────────────────────────────────────────────────────

function relativeTime(ts: number): string {
  const diff = Date.now() - ts;
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'Just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

// ─── App Icon ─────────────────────────────────────────────────────────────────

const AppIcon: React.FC<{ type: NotificationType; size?: number }> = ({ type, size = 46 }) => {
  const cfg = TYPE_CFG[type];
  return (
    <div
      className={styles.appIcon}
      style={{
        width: size, height: size,
        background: cfg.gradient,
        boxShadow: `0 3px 10px ${cfg.accent}55, inset 0 1px 0 rgba(255,255,255,0.25)`,
      }}
    >
      <span style={{ color: '#fff', display: 'flex', alignItems: 'center' }}>{cfg.icon}</span>
    </div>
  );
};

// ─── Swipeable Notification Row ───────────────────────────────────────────────
// Swipe left → delete, like iOS notifications

const NotifRow: React.FC<{ notif: Notification; onClose: () => void }> = ({ notif, onClose }) => {
  const { markAsRead, clearNotification } = useNotifications();
  const navigate = useNavigate();
  const cfg = TYPE_CFG[notif.type];

  // Framer Motion drag values
  const x = useMotionValue(0);
  const bgOpacity = useTransform(x, [-120, -60, 0], [1, 0.6, 0]);
  const rowOpacity = useTransform(x, [-140, -80, 0], [0, 0.5, 1]);
  const controls = useAnimation();

  const handleDragEnd = (_: any, info: { offset: { x: number } }) => {
    if (info.offset.x < -80) {
      // Swipe far enough → delete
      controls.start({ x: -400, opacity: 0, transition: { duration: 0.25 } })
        .then(() => clearNotification(notif.id));
    } else {
      // Snap back
      controls.start({ x: 0, transition: { type: 'spring', stiffness: 300, damping: 28 } });
    }
  };

  const handleClick = () => {
    markAsRead(notif.id);
    if (notif.movieId) { navigate(`/movie/${notif.movieId}`); onClose(); }
  };

  return (
    <div className={styles.rowOuter}>
      {/* Red delete background revealed on swipe */}
      <motion.div className={styles.swipeBg} style={{ opacity: bgOpacity }}>
        <X size={18} strokeWidth={2.5} color="#fff" />
        <span>Delete</span>
      </motion.div>

      {/* The actual row — draggable */}
      <motion.div
        className={`${styles.row} ${!notif.isRead ? styles.rowUnread : ''}`}
        style={{ x, opacity: rowOpacity }}
        animate={controls}
        drag="x"
        dragConstraints={{ left: -200, right: 0 }}
        dragElastic={{ left: 0.3, right: 0 }}
        onDragEnd={handleDragEnd}
        onClick={handleClick}
        role="button"
        tabIndex={0}
        whileTap={{ scale: 0.995 }}
      >
        {/* Left: poster or icon */}
        <div className={styles.leftCol}>
          {notif.posterPath ? (
            <div className={styles.posterWrap}>
              <img
                src={`https://image.tmdb.org/t/p/w92${notif.posterPath}`}
                alt=""
                className={styles.posterImg}
                onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
              />
              <div
                className={styles.miniAppIcon}
                style={{ background: cfg.gradient, boxShadow: `0 2px 6px ${cfg.accent}88` }}
              >
                <span style={{ color: '#fff', display: 'flex' }}>
                  {React.cloneElement(cfg.icon as React.ReactElement, { size: 10, strokeWidth: 2.5 })}
                </span>
              </div>
            </div>
          ) : (
            <AppIcon type={notif.type} />
          )}
        </div>

        {/* Middle: text */}
        <div className={styles.middleCol}>
          <div className={styles.topRow}>
            <span className={styles.label} style={{ color: cfg.accent }}>{cfg.label}</span>
            <span className={styles.time}>{relativeTime(notif.timestamp)}</span>
          </div>
          <p className={styles.title}>{notif.title}</p>
          <p className={styles.msg}>{notif.message}</p>
        </div>

        {/* Right: dot + dismiss */}
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
    </div>
  );
};

// ─── Push Permission Banner ───────────────────────────────────────────────────

const PushBanner: React.FC = () => {
  const { pushPermission, requestPushPermission } = useNotifications();
  const [dismissed, setDismissed] = useState(
    () => localStorage.getItem('moviemind_push_perm_asked') === 'asked'
  );

  if (dismissed || pushPermission === 'granted' || pushPermission === 'denied' || pushPermission === 'unsupported') {
    return null;
  }

  return (
    <motion.div
      className={styles.pushBanner}
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: 'auto', opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className={styles.pushBannerInner}>
        <div className={styles.pushBannerLeft}>
          <div className={styles.pushIconWrap}>
            <BellRing size={15} strokeWidth={2.2} />
          </div>
          <div>
            <p className={styles.pushTitle}>Enable Notifications</p>
            <p className={styles.pushSub}>Get movie alerts even when tab is closed</p>
          </div>
        </div>
        <div className={styles.pushBannerActions}>
          <button
            className={styles.pushAllowBtn}
            onClick={async () => {
              await requestPushPermission();
              setDismissed(true);
            }}
          >
            Allow
          </button>
          <button
            className={styles.pushDenyBtn}
            onClick={() => {
              localStorage.setItem('moviemind_push_perm_asked', 'asked');
              setDismissed(true);
            }}
          >
            <X size={12} />
          </button>
        </div>
      </div>
    </motion.div>
  );
};

// ─── Scheduler Info Footer ────────────────────────────────────────────────────

const SchedulerInfo: React.FC = () => {
  const { nextScheduledTime } = useNotifications();
  if (!nextScheduledTime) return null;

  const fmt = nextScheduledTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const isToday = nextScheduledTime.toDateString() === new Date().toDateString();

  return (
    <div className={styles.schedulerRow}>
      <Clock size={11} style={{ opacity: 0.5, flexShrink: 0 }} />
      <span>Next update {isToday ? 'today' : 'tomorrow'} at {fmt}</span>
    </div>
  );
};

// ─── Main Panel ───────────────────────────────────────────────────────────────

interface Props { isOpen: boolean; onClose: () => void; }

const NotificationPanel: React.FC<Props> = ({ isOpen, onClose }) => {
  const {
    notifications, unreadCount,
    markAllAsRead, clearAll, isLoading,
    isBellShaking, pushPermission,
  } = useNotifications();

  const wrapRef  = useRef<HTMLDivElement>(null);
  const bellCtrl = useAnimation();

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) onClose();
    };
    if (isOpen) document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [isOpen, onClose]);

  // Bell shake animation when isBellShaking is true
  useEffect(() => {
    if (isBellShaking) {
      bellCtrl.start({
        rotate: [0, -18, 18, -14, 14, -8, 8, -4, 4, 0],
        transition: { duration: 0.82, ease: 'easeInOut' },
      });
    }
  }, [isBellShaking, bellCtrl]);

  const showPushBtn = pushPermission === 'default';

  return (
    <div className={styles.wrapper} ref={wrapRef}>

      {/* ── Animated Bell Button ── */}
      <motion.button
        className={`${styles.bellBtn} ${isOpen ? styles.bellOpen : ''} ${isBellShaking ? styles.bellShake : ''}`}
        onClick={onClose}
        animate={bellCtrl}
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
      </motion.button>

      {/* ── Panel ── */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className={styles.panel}
            initial={{ opacity: 0, y: -8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            transition={{ type: 'spring', stiffness: 380, damping: 32 }}
          >
            {/* Header */}
            <div className={styles.panelHeader}>
              <div className={styles.panelHeaderLeft}>
                <h3 className={styles.panelTitle}>Notifications</h3>
                {pushPermission === 'granted' && (
                  <span className={styles.livePill}>
                    <span className={styles.liveDot} />
                    Live
                  </span>
                )}
              </div>
              <div className={styles.panelActions}>
                {unreadCount > 0 && (
                  <button className={styles.actionBtn} onClick={markAllAsRead} title="Mark all as read">
                    <CheckCheck size={14} strokeWidth={2.5} />
                    <span>Read all</span>
                  </button>
                )}
                {notifications.length > 0 && (
                  <button className={`${styles.actionBtn} ${styles.actionBtnDanger}`} onClick={clearAll} title="Clear all">
                    <Trash2 size={14} strokeWidth={2.5} />
                  </button>
                )}
              </div>
            </div>

            {/* Push Permission Banner */}
            <AnimatePresence>
              {showPushBtn && <PushBanner key="push-banner" />}
            </AnimatePresence>

            {/* Unread pill */}
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

            {/* Hint for swipe */}
            {notifications.length > 0 && (
              <div className={styles.swipeHint}>
                <span>← Swipe left to dismiss</span>
              </div>
            )}

            {/* Body */}
            <div className={styles.body}>
              {isLoading && notifications.length === 0 && (
                <div className={styles.centerState}>
                  <div className={styles.spinner} />
                  <p>Fetching updates…</p>
                </div>
              )}

              {!isLoading && notifications.length === 0 && (
                <div className={styles.centerState}>
                  <div className={styles.emptyBell}><Bell size={28} strokeWidth={1.5} /></div>
                  <p className={styles.emptyTitle}>All caught up!</p>
                  <span className={styles.emptySubtitle}>No new notifications right now</span>
                </div>
              )}

              <AnimatePresence initial={false}>
                {notifications.map(n => (
                  <NotifRow key={n.id} notif={n} onClose={onClose} />
                ))}
              </AnimatePresence>
            </div>

            {/* Footer with scheduler */}
            <div className={styles.panelFooter}>
              {notifications.length > 0 && (
                <span>{notifications.length} notification{notifications.length !== 1 ? 's' : ''}</span>
              )}
              <SchedulerInfo />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default NotificationPanel;
