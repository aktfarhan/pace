import { curveMonotoneX, line } from 'd3-shape';
import type { Reading } from '@/types/transit';

// The share the axis tops out at
const TOP = 100;

// How much of the day one reading covers
const BUCKET_MS = 15 * 60000;

// The edges a chart draws between
export interface Box {
    left: number;
    right: number;
    floor: number;
    ceil: number;
}

// One reading placed on the plot
export interface Spot {
    x: number;
    y: number;
    at: number;
    share: number;
    seen: number;
    reach: number;
}

// Draws a line of spots
const draw = line<Spot | null>()
    .defined((spot) => spot !== null)
    .x((spot) => (spot === null ? 0 : spot.x))
    .y((spot) => (spot === null ? 0 : spot.y))
    // Monotone, so the line never bends past 0 or 100
    .curve(curveMonotoneX);

// How wide the window is
function spanOf(start: number, end: number) {
    return Math.max(end - start, BUCKET_MS);
}

// Where a share sits across the plot
function xOf(at: number, start: number, end: number, box: Box) {
    return box.left + ((at - start) / spanOf(start, end)) * (box.right - box.left);
}

// Where a share sits between the floor and the ceiling
function yOf(share: number, box: Box) {
    return box.floor - (share / TOP) * (box.floor - box.ceil);
}

// One line's readings
export function seriesOf(readings: Reading[], start: number, end: number, box: Box) {
    // The window measured in buckets
    const slots = Math.floor((end - start) / BUCKET_MS);

    // Each reading under the slot it covers
    const taken = new Map<number, Reading>();
    for (const reading of readings) {
        const slot = Math.round((Date.parse(reading.at) - start) / BUCKET_MS);
        if (slot < 0 || slot > slots) continue;

        taken.set(slot, reading);
    }

    // One spot for every slot
    const spots: (Spot | null)[] = [];
    for (let slot = 0; slot <= slots; slot += 1) {
        const reading = taken.get(slot);
        if (reading === undefined) {
            spots.push(null);
            continue;
        }

        const at = start + slot * BUCKET_MS;
        spots.push({
            x: xOf(at, start, end, box),
            y: yOf(reading.share, box),
            at,
            share: reading.share,
            seen: reading.seen,
            reach: reading.reach,
        });
    }

    // An empty series draws nothing
    return { path: draw(spots) ?? '', spots };
}
