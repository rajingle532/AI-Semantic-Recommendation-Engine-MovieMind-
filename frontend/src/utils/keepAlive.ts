/**
 * Keep-alive utility.
 * Pings the configured backend every 10 minutes when explicitly enabled.
 */

const ENABLE_KEEP_ALIVE = import.meta.env.VITE_ENABLE_KEEP_ALIVE === 'true';
const BACKEND_HEALTH_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/health`
  : '/api/health';

const PING_INTERVAL_MS = 10 * 60 * 1000;

let intervalId: ReturnType<typeof setInterval> | null = null;

async function pingBackend(): Promise<void> {
  try {
    const response = await fetch(BACKEND_HEALTH_URL, {
      method: 'GET',
      mode: 'cors',
    });

    if (response.ok) {
      console.log('[KeepAlive] Backend ping successful');
    } else {
      console.warn(`[KeepAlive] Backend responded with status ${response.status}`);
    }
  } catch (error) {
    console.warn('[KeepAlive] Backend ping failed:', error);
  }
}

export function startKeepAlive(): void {
  if (!ENABLE_KEEP_ALIVE || intervalId) return;

  pingBackend();
  intervalId = setInterval(pingBackend, PING_INTERVAL_MS);
  console.log('[KeepAlive] Started - pinging backend every 10 minutes');
}

export function stopKeepAlive(): void {
  if (!intervalId) return;

  clearInterval(intervalId);
  intervalId = null;
  console.log('[KeepAlive] Stopped');
}
