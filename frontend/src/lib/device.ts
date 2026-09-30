// Room for the full sidebar
const WIDE = '(min-width: 64rem)';

// Whether there's room for the full sidebar
export const wide = () => matchMedia(WIDE).matches;

// Tells a listener when the width crosses that line
export function onWide(change: () => void) {
    const query = matchMedia(WIDE);
    query.addEventListener('change', change);
    return () => query.removeEventListener('change', change);
}
