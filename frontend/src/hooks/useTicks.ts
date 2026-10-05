import { useState } from 'react';

// Whether each value still sharpens in after a change
export function useTicks(pairs: [string, string][]) {
    // The value each id last sharpened in with
    const [settled, setSettled] = useState(() => new Map(pairs));

    return {
        ticking: (id: string, value: string) => settled.get(id) !== value,
        settle: (id: string, value: string) =>
            setSettled((all) => (all.get(id) === value ? all : new Map(all).set(id, value))),
    };
}
