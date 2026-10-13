import { useMemo } from 'react';
import { LINES, branchLook } from '@/lib/lines';
import { feedOf, lookOf, nameOf } from '@/components/transit/standing';
import type { Line } from '@/lib/lines';
import type { Transit } from '@/types/transit';

// Where each line, or each branch of the picked one stands
export function useStandings(transit: Transit | null, focused: Line | undefined) {
    return useMemo(() => {
        if (transit === null) return { standing: [], running: [], shares: {} };

        // Every line, on the All tab
        if (focused === undefined) {
            const standing = LINES.map((line) => ({
                ...feedOf(transit, line.id),
                ...lookOf(line),
                name: nameOf(transit, line),
            }));
            return { standing, running: [], shares: {} };
        }

        // The picked line's branches
        const running = (transit.branches[focused.id] ?? []).map(({ id, name }) => ({
            ...feedOf(transit, id),
            ...lookOf(focused),
            ...branchLook(name),
        }));

        // The line's own share leads its branches'
        const shares: Record<string, number | null> = {
            [focused.id]: feedOf(transit, focused.id).share,
        };
        for (const one of running) shares[one.id] = one.share;

        return { standing: [], running, shares };
    }, [transit, focused]);
}
