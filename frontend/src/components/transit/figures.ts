import { HOUR_MS } from './plot';
import { clockOf } from './frame';
import type { Mark } from './plot';
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

// What a line typically runs at
export interface Typically {
    share: number;
    days: number;
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

// Where one set of readings stands right now
export function standingOf(readings: Reading[]) {
    return {
        share: readings.length === 0 ? null : readings[readings.length - 1].share,
        drift: driftOf(readings),
    };
}

// What every line is running at now, and which way its moving
export function figuresOf(lines: readonly Drawn[], series: Record<string, Reading[]>) {
    const figures: Figure[] = [];
    for (const line of lines) {
        figures.push({ line, ...standingOf(series[line.id]) });
    }
    return figures;
}

// Where a line typically is by now
export function typicalOf(
    typical: Record<string, Reading[]>,
    lines: readonly Drawn[],
): Typically | null {
    if (lines.length !== 1) return null;

    const readings = typical[lines[0].id];
    if (readings.length === 0) return null;

    const last = readings[readings.length - 1];
    return { share: last.share, days: last.days ?? 0 };
}

// How far back a reading reached
function reachOf(minutes: number) {
    const hours = minutes / 60;
    return `${Number.isInteger(hours) ? hours : hours.toFixed(1)}h`;
}

// What the chart is saying when hovered
export function readoutOf(marks: Mark[], usual: number | null, rolling: number, alone: boolean) {
    if (marks.length === 0) return null;

    const { at, seen, reach } = marks[0].spot;
    const said = [clockOf(at)];

    // Arrivals that belong to one line
    if (alone) {
        const over = reach > rolling ? ` over ${reachOf(reach)}` : '';
        said.push(`${seen} arrivals${over}`);
    }
    if (usual !== null) said.push(`usually ${usual}%`);

    return said.join(' · ');
}
