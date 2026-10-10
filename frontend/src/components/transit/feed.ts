import { HOUR_MS } from './plot';
import { clockOf } from './frame';
import { LINES } from '@/lib/lines';
import {
    Ban,
    Bus,
    Info,
    Clock,
    Signpost,
    Construction,
    Accessibility,
    TriangleAlert,
} from 'lucide-react';
import type { Line } from '@/lib/lines';
import type { Notice, Transit } from '@/types/transit';

// A day, and how far back the data is stale
const DAY_MS = 24 * HOUR_MS;
const STALE_DAYS = 30;

const MONTH = new Intl.DateTimeFormat('en-US', { month: 'short', year: 'numeric' });
const MONTH_DAY = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' });

// The icon with each kind of effect
const KINDS = [
    { match: /ELEVATOR|ESCALATOR|ACCESS/, Icon: Accessibility, name: 'Access' },
    { match: /SUSPENSION|NO_SERVICE|CANCEL/, Icon: Ban, name: 'Suspended' },
    { match: /SHUTTLE/, Icon: Bus, name: 'Shuttle' },
    { match: /DELAY/, Icon: Clock, name: 'Delay' },
    { match: /TRACK|MAINTENANCE|CONSTRUCTION/, Icon: Construction, name: 'Track work' },
    { match: /DETOUR|STOP|STATION_CLOSURE/, Icon: Signpost, name: 'Detour' },
    { match: /ISSUE|SAFETY|POLICE|WEATHER/, Icon: TriangleAlert, name: 'Station issue' },
];
const OTHER = { Icon: Info, name: 'Notice' };

export function kindOf(effect: string) {
    return KINDS.find((kind) => kind.match.test(effect)) ?? OTHER;
}

// An alert's time, or NaN when it has none
function momentOf(at: string | null) {
    return at === null ? NaN : Date.parse(at);
}

// When an alert runs
export function datesOf(since: string | null, until: string | null) {
    const begin = momentOf(since);
    const end = momentOf(until);
    if (!Number.isFinite(begin) || !Number.isFinite(end)) return null;

    // A one-day alert shows its times
    const day = MONTH_DAY.format(begin);
    if (new Date(begin).toDateString() === new Date(end).toDateString()) {
        return `${day}, ${clockOf(begin)} → ${clockOf(end)}`;
    }
    return `${day} → ${MONTH_DAY.format(end)}`;
}

// How far along an alert is
export function stretchOf(since: string | null, until: string | null) {
    const now = Date.now();
    const end = momentOf(until);
    // If there is no end, or already over
    if (!Number.isFinite(end) || end < now) return null;

    const begin = momentOf(since);

    // There is no start, or not started yet
    if (!Number.isFinite(begin) || begin > now) {
        return { label: `until ${MONTH_DAY.format(end)}`, progress: null };
    }

    // Progress through the run
    const progress = (now - begin) / Math.max(end - begin, 1);
    const days = Math.ceil((end - begin) / DAY_MS);

    // A one-day alert shows its end time
    if (days <= 1) return { label: `ends ${clockOf(end)}`, progress };

    // Which day of the run today is
    const day = Math.min(Math.floor((now - begin) / DAY_MS) + 1, days);
    return { label: `day ${day} of ${days}`, progress };
}

// When an alert came into effect
export function sinceOf(at: string | null) {
    const when = momentOf(at);
    if (!Number.isFinite(when)) return 'in effect';

    // Only a moment today reads as a clock time
    const today = new Date(when).toDateString() === new Date().toDateString();
    const date = today ? clockOf(when) : MONTH_DAY.format(when);

    const days = Math.floor((Date.now() - when) / DAY_MS);
    if (days < 0) return `starts ${date}`;
    if (days >= STALE_DAYS) return `since ${MONTH.format(when)}`;

    return `since ${date}`;
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

// Every word a notice carries, for a search to look through
export function wordsOf({ lines, alert }: Notice) {
    const said = [
        ...lines.map((one) => one.label),
        alert.where,
        alert.effect,
        alert.headline,
        alert.detail,
    ];

    return said.join(' ').toLowerCase();
}
