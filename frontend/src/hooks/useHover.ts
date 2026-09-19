import { slotAt } from '@/components/transit/plot';
import { useMemo, useState } from 'react';
import type { PointerEvent } from 'react';
import type { Box, Spot } from '@/components/transit/plot';

// Where the pointer is
interface Held {
    x: number;
    y: number;
}

// Reading a plot at whatever the pointer is over
export function useHover(
    sheets: readonly (Spot | null)[][],
    shown: string,
    start: number,
    end: number,
    box: Box,
) {
    const [held, setHeld] = useState<Held | null>(null);

    // A readout of one set of lines means nothing once another set is drawn
    const [forLines, setForLines] = useState(shown);
    if (forLines !== shown) {
        setForLines(shown);
        setHeld(null);
    }

    // The nearest quarter hour any line reported
    const reading = useMemo(() => {
        if (held === null) return null;

        const slots = sheets.length === 0 ? 0 : sheets[0].length;
        const under = slotAt(held.x, start, end, box);
        for (let away = 0; away < slots; away += 1) {
            for (const slot of [under - away, under + away]) {
                if (slot < 0 || slot >= slots) continue;
                if (sheets.some((spots) => spots[slot] != null)) return slot;
            }
        }
        return null;
    }, [held, sheets, start, end, box]);

    const clear = () => setHeld(null);

    // Read out every line at whichever quarter hour the pointer is over
    const follow = (event: PointerEvent<SVGSVGElement>) => {
        const edge = event.currentTarget.getBoundingClientRect();
        setHeld({ x: event.clientX - edge.left, y: event.clientY - edge.top });
    };

    // A touch leaves nothing behind once it lifts
    const lift = (event: PointerEvent<SVGSVGElement>) => {
        if (event.pointerType === 'touch') clear();
    };

    return { held, reading, follow, lift, clear };
}
