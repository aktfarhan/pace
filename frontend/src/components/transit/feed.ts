import { HOUR_MS } from './plot';
import { clockOf } from './frame';
import { LINES } from '@/lib/lines';
import type { Line } from '@/lib/lines';
import type { Notice, Transit } from '@/types/transit';

// A day, and how far back the data is stale
const DAY_MS = 24 * HOUR_MS;
const STALE_DAYS = 30;

const MONTH = new Intl.DateTimeFormat('en-US', { month: 'short', year: 'numeric' });

// When an alert came into effect
export function sinceOf(at: string | null) {
    const when = at === null ? NaN : Date.parse(at);
    if (!Number.isFinite(when)) return 'in effect';

    const days = Math.floor((Date.now() - when) / DAY_MS);
    if (days < 0) return 'not yet in effect';
    if (days >= STALE_DAYS) return `since ${MONTH.format(when)}`;
    if (days >= 1) return `since ${days} ${days === 1 ? 'day' : 'days'} ago`;

    return `since ${clockOf(when)}`;
}

// Everything the feed is reporting
export function noticesOf(transit: Transit, focused: Line | undefined) {
    const said: Notice[] = [];
    const at = new Map<string, number>();

    for (const line of LINES) {
        if (focused !== undefined && line.id !== focused.id) continue;

        const status = transit.status.lines.find((one) => one.line_id === line.id);

        // Every alert the feed lists under this line
        for (const alert of status?.alerts ?? []) {
            const seen = at.get(alert.alert_id);

            // Map the line to all its alerts
            if (seen === undefined) {
                at.set(alert.alert_id, said.length);
                said.push({ lines: [line], alert });
            } else {
                said[seen].lines.push(line);
            }
        }
    }

    // An alert with no start counts as the oldest
    const began = (one: Notice) => (one.alert.since === null ? 0 : Date.parse(one.alert.since));

    // What delays service is listed first
    return said.sort(
        (a, b) => Number(b.alert.slowing) - Number(a.alert.slowing) || began(b) - began(a),
    );
}
