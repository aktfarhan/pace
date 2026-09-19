import { curveMonotoneX, line } from 'd3-shape';
import type { Drawn } from '@/lib/lines';
import type { Reading } from '@/types/transit';

// The share the axis tops out at
export const TOP = 100;

// How much of the day one reading covers
export const BUCKET_MS = 15 * 60000;

// How long the axis counts by
export const HOUR_MS = 60 * 60000;

// How close two readouts may sit
const LABEL_GAP = 11;

// How far a readout drops to centre on its dot
const LABEL_DROP = 3.5;

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

// One line's reading under the pointer
interface Mark {
    id: string;
    code: string;
    mark: string;
    stroke: string;
    spot: Spot;
}

// One line and the spots drawn for it
interface Sheet {
    line: Drawn;
    spots: (Spot | null)[];
}

// A mark with its readout placed
export interface Label extends Mark {
    y: number;
}

// Draws a line of spots
const draw = line<Spot | null>()
    .defined((spot) => spot !== null)
    .x((spot) => (spot === null ? 0 : spot.x))
    .y((spot) => (spot === null ? 0 : spot.y))
    // Monotone, so the line never bends past 0 or 100
    .curve(curveMonotoneX);

// How wide the window is
export function spanOf(start: number, end: number) {
    return Math.max(end - start, BUCKET_MS);
}

// Where a moment sits across the plot
export function xOf(at: number, start: number, end: number, box: Box) {
    return box.left + ((at - start) / spanOf(start, end)) * (box.right - box.left);
}

// Where a share sits between the floor and the ceiling
export function yOf(share: number, box: Box) {
    return box.floor - (share / TOP) * (box.floor - box.ceil);
}

// Every line's reading at that slot
export function marksOf(sheets: Sheet[], reading: number | null) {
    const marks: Mark[] = [];
    if (reading === null) return marks;

    for (const sheet of sheets) {
        const spot = sheet.spots[reading];
        if (spot === null) continue;

        marks.push({
            id: sheet.line.id,
            code: sheet.line.code,
            mark: sheet.line.mark,
            stroke: sheet.line.stroke,
            spot,
        });
    }

    marks.sort((a, b) => a.spot.y - b.spot.y);
    return marks;
}

// Lifts each readout clear of the one above
export function stackOf(marks: Mark[], floor: number) {
    const labels: Label[] = [];
    let taken = -Infinity;
    for (const mark of marks) {
        const y = Math.max(mark.spot.y + LABEL_DROP, taken + LABEL_GAP);
        taken = y;
        labels.push({ ...mark, y });
    }

    // A stack past the floor is pushed back up
    let under = floor;
    for (let index = labels.length - 1; index >= 0; index -= 1) {
        const lifted = Math.min(labels[index].y, under);
        labels[index] = { ...labels[index], y: lifted };
        under = lifted - LABEL_GAP;
    }

    return labels;
}

// The slot a point along the plot falls in
export function slotAt(x: number, start: number, end: number, box: Box) {
    const span = spanOf(start, end);
    const slots = Math.floor((end - start) / BUCKET_MS);
    const across = (x - box.left) / Math.max(box.right - box.left, 1);
    const slot = Math.round((across * span) / BUCKET_MS);
    return Math.min(Math.max(slot, 0), slots);
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
