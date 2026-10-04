// How often a feed is read again
export const POLL_MS = 30000;

// Two and a half missed reads means stale feed
export const STALE_MS = POLL_MS * 2.5;

// Reads right away, then every 30 seconds while the tab is visible
export function poll(read: () => void) {
    // Skips the read while the tab is hidden
    const wake = () => {
        if (document.visibilityState === 'visible') read();
    };

    // The first read happens right away
    read();

    // Every 30 seconds, and whenever the tab comes back into view
    const timer = setInterval(wake, POLL_MS);
    document.addEventListener('visibilitychange', wake);

    // Stops both the timer and the listener
    return () => {
        clearInterval(timer);
        document.removeEventListener('visibilitychange', wake);
    };
}
