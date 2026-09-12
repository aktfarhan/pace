import { curveCardinal, line } from 'd3-shape';
import type { Reading } from '@/types/transit';

// Where the plot sits
export const LEFT = 48;
export const RIGHT = 852;
export const FLOOR = 246;
export const CEIL = 16;

// The share the axis tops out at
const TOP = 100;

// How much of the day one reading covers
const BUCKET_MS = 15 * 60000;

// The hour the service day rolls over
const ROLLOVER_HOUR = 3;

// The hour the first trains report
const FIRST_HOUR = 4;

// One point on the grid, or null
type Point = { x: number; y: number } | null;

// Draws a line of points
const draw = line<Point>()
    .defined((point) => point !== null)
    .x((point) => (point === null ? 0 : point.x))
    .y((point) => (point === null ? 0 : point.y))
    .curve(curveCardinal.tension(0));

// The stretch of the service day the chart covers
export function windowOf(now: number) {
    const start = new Date(now);
    if (start.getHours() < ROLLOVER_HOUR) {
        start.setDate(start.getDate() - 1);
    }
    start.setHours(FIRST_HOUR, 0, 0, 0);
    return { start: start.getTime(), end: now };
}

// Where a share sits between the floor and the ceiling
export function yOf(share: number) {
    return FLOOR - (share / TOP) * (FLOOR - CEIL);
}

// The path for one line
export function pathOf(readings: Reading[], start: number, end: number) {
    // The window measured in buckets
    const span = Math.max(end - start, BUCKET_MS);
    const slots = Math.floor((end - start) / BUCKET_MS);

    // Each reading under the slot it covers
    const shares = new Map<number, number>();
    for (const reading of readings) {
        const slot = Math.round((Date.parse(reading.at) - start) / BUCKET_MS);
        if (slot < 0 || slot > slots) continue;
        shares.set(slot, reading.share);
    }

    // One point for every slot
    const points: Point[] = [];
    for (let slot = 0; slot <= slots; slot += 1) {
        const share = shares.get(slot);
        if (share === undefined) {
            points.push(null);
            continue;
        }
        points.push({ x: LEFT + ((slot * BUCKET_MS) / span) * (RIGHT - LEFT), y: yOf(share) });
    }

    // An empty series draws nothing
    return draw(points) ?? '';
}
