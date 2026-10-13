import { EVERY } from './tints';
import { clockOf } from './frame';
import { running } from '@/lib/status';
import { standingOf } from './figures';
import { LINE_BY_ID } from '@/lib/lines';
import type { Line } from '@/lib/lines';
import type { Branching, Standing, Transit } from '@/types/transit';

const NARROW = 132;
const GAP = 12;

// How many columns fill the width
export function columnsFor(count: number, width: number) {
    const fits = Math.max(Math.min(Math.floor((width + GAP) / (NARROW + GAP)), count), 1);

    let best = fits;
    let fullest = -1;

    // The fullest last row wins
    for (let columns = 2; columns <= fits; columns += 1) {
        const last = count % columns === 0 ? columns : count % columns;
        if (last >= fullest) {
            fullest = last;
            best = columns;
        }
    }

    return best;
}

// How often a line runs, or when service starts
export function whenOf({ every, next, started }: Standing) {
    if (every !== null) return `every ${every} min`;
    if (next !== null) return `${started ? 'left at' : 'next at'} ${clockOf(Date.parse(next))}`;

    return 'not running today';
}

// What the feed says about one line or branch
export function feedOf(transit: Transit, id: string) {
    const next = transit.resumes[id] ?? null;
    return {
        id,
        every: transit.headways[id] ?? null,
        next,
        started: next !== null && Date.parse(next) <= Date.parse(transit.status.retrieved_at),
        trend: transit.series[id].map(({ at, share }) => ({ at: Date.parse(at), share })),
        ...standingOf(transit.series[id]),
    };
}

// The feed names every line in full
export function nameOf(transit: Transit, line: Line) {
    return transit.status.lines.find((one) => one.line_id === line.id)?.line_name ?? line.label;
}

// The code and colours a line's cards wear
export function lookOf({ code, chip, text }: Line) {
    return { code, chip, text };
}

// The tabs whose line isn't running normally
export function troubleOf(transit: Transit | null) {
    const lines = transit?.status.lines ?? [];
    return new Set(
        lines.filter((line) => !running(line)).map((line) => LINE_BY_ID[line.line_id].label),
    );
}

// A line's branch choices
export function rowsOf({ branches, branch }: Branching) {
    const rows = [{ id: null, name: EVERY }, ...branches];
    return { rows, shown: rows.find((row) => row.id === branch) ?? rows[0] };
}
