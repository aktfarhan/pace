import { BUCKET_MS, HOUR_MS, TOP, landOf, spanOf, xOf, yOf } from './plot';
import { ZONE, bostonHour, bostonMoment } from '@/lib/boston';
import type { Box } from './plot';
import type { Reading } from '@/types/transit';

// The hour the service day rolls over
const ROLLOVER_HOUR = 3;

// The hour the first trains report
const FIRST_HOUR = 4;

// How much width an hour label needs to itself
const HOUR_ROOM = 70;

// How often a gridline is drawn
const RULED = 25;

// How often one of them is named
const NAMED = 50;

const HOUR = new Intl.DateTimeFormat('en-US', { timeZone: ZONE, hour: 'numeric', hour12: true });

const CLOCK = new Intl.DateTimeFormat('en-US', {
    timeZone: ZONE,
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
});

// The hour and minute of a time
export function clockOf(at: number) {
    return CLOCK.format(at);
}

// The stretch of the day the chart covers
export function windowOf(now: number, shown: Reading[][], hours: number | null) {
    let first = Infinity;
    for (const readings of shown) {
        const at = readings.length === 0 ? NaN : landOf(readings[0]);
        if (at < first) first = at;
    }

    // Nothing has reported, so open where the trains do
    if (!Number.isFinite(first)) {
        const back = bostonHour(now) < ROLLOVER_HOUR ? -1 : 0;
        first = bostonMoment(now, back, FIRST_HOUR);
    }

    // Readings land on the quarter hour
    if (hours !== null) {
        const back = Math.floor((now - hours * HOUR_MS) / BUCKET_MS) * BUCKET_MS;
        first = Math.max(back, first);
    }

    // At least a bucket wide
    const quarter = Math.floor((now - BUCKET_MS) / BUCKET_MS) * BUCKET_MS;
    return { start: Math.min(first, quarter), end: now };
}

// The gridlines across the plot
export function rulesOf(box: Box) {
    const rules = [];
    for (let share = 0; share <= TOP; share += RULED) {
        rules.push({
            share,
            y: yOf(share, box),
            label: share % NAMED === 0 ? `${share}%` : null,
        });
    }
    return rules;
}

// The hours marked along the axis
export function ticksOf(start: number, end: number, box: Box) {
    const hours = spanOf(start, end) / HOUR_MS;
    const across = Math.max(box.right - box.left, 1);
    const every = Math.max(Math.ceil(HOUR_ROOM / (across / hours)), 1);

    // Marks land on the hour
    let first = Math.ceil(start / HOUR_MS) * HOUR_MS;

    // Start on a Boston hour the step divides
    while (bostonHour(first) % every !== 0) {
        first += HOUR_MS;
    }

    // One mark every step
    const ticks = [];
    for (let at = first; at <= end; at += every * HOUR_MS) {
        ticks.push({ at, x: xOf(at, start, end, box), label: HOUR.format(at) });
    }

    // Before a whole hour lands, mark the start
    if (ticks.length === 0) {
        ticks.push({ at: start, x: box.left, label: CLOCK.format(start) });
    }

    return ticks;
}
