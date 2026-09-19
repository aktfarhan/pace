import { LINES } from '@/lib/lines';
import type { Reading } from '@/types/transit';

// What each line is running at now
export function figuresOf(series: Record<string, Reading[]>) {
    const figures: Record<string, number | null> = {};
    for (const line of LINES) {
        const readings = series[line.id] ?? [];
        figures[line.id] = readings.length === 0 ? null : readings[readings.length - 1].share;
    }
    return figures;
}
