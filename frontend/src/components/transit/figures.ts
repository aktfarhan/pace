import { HOUR_MS } from './plot';
import type { Drawn } from '@/lib/lines';
import type { Reading } from '@/types/transit';

// Minimum required points
const DRIFT = 2;

// Where a line stands right now
export interface Figure {
    line: Drawn;
    share: number | null;
    drift: number | null;
}

// How far one line has moved in the last hour
function driftOf(readings: Reading[]) {
    if (readings.length === 0) return null;

    const last = readings[readings.length - 1];
    const now = Date.parse(last.at);
    const want = now - HOUR_MS;

    // The reading nearest an hour back
    let before: Reading | null = null;
    let away = Infinity;
    for (const reading of readings) {
        const at = Date.parse(reading.at);
        if (at >= now) continue;

        const gap = Math.abs(at - want);
        if (gap >= away) continue;

        away = gap;
        before = reading;
    }

    // Too far off the hour to compare against
    if (before === null || away > HOUR_MS / 2) return null;

    const moved = last.share - before.share;
    return Math.abs(moved) < DRIFT ? null : moved;
}

// What every line is running at now, and which way its moving
export function figuresOf(lines: readonly Drawn[], series: Record<string, Reading[]>) {
    const figures: Figure[] = [];
    for (const line of lines) {
        const readings = series[line.id];
        figures.push({
            line,
            share: readings.length === 0 ? null : readings[readings.length - 1].share,
            drift: driftOf(readings),
        });
    }
    return figures;
}
