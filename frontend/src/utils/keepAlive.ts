/**
 * Keep-Alive Utility
 * Pings the backend every 10 minutes to prevent Render free tier from sleeping.
 * The free tier sleeps after 15 minutes of inactivity, causing 30-60s cold starts.
 */

const BACKEND_HEALTH_URL =
  import.meta.env.VITE_API_URL
    ? `${import.meta.env.VITE_API_URL}/api/health`
    : 'https://moviemind-api.onrender.com/api/health';

const PING_INTERVAL_MS = 10 * 60 * 1000; // 10 minutes

let intervalId: ReturnType<typeof setInterval> | null = null;

async function pingBackend(): Promise<void> {
  try {
    const response = await fetch(BACKEND_HEALTH_URL, {
      method: 'GET',
      mode: 'cors',
    });
    if (response.ok) {
      console.log('[KeepAlive] Backend ping successful ✓');
    } else {
      console.warn(`[KeepAlive] Backend responded with status ${response.status}`);
    }
  } catch (error) {
    console.warn('[KeepAlive] Backend ping failed (may be waking up):', error);
  }
}

/**
 * Starts the keep-alive ping loop.
 * - Sends an immediate ping on start
 * - Repeats every 10 minutes
 */
export function startKeepAlive(): void {
  if (intervalId) return; // Already running

  // Initial ping to wake up backend immediately
  pingBackend();

  intervalId = setInterval(pingBackend, PING_INTERVAL_MS);
  console.log('[KeepAlive] Started — pinging backend every 10 minutes');
}

/**
 * Stops the keep-alive ping loop.
 */
export function stopKeepAlive(): void {
  if (intervalId) {
    clearInterval(intervalId);
    intervalId = null;
    console.log('[KeepAlive] Stopped');
  }
}
