import { useState } from 'react';

// Whether each value still sharpens in after a change
export function useTicks<T>(pairs: [string, T][]) {
    // The value each id last sharpened in with
    const [settled, setSettled] = useState(() => new Map(pairs));

    // New ids count as drawn
    const fresh = pairs.filter(([id]) => !settled.has(id));
    if (fresh.length > 0) setSettled(new Map([...settled, ...fresh]));

    return {
        ticking: (id: string, value: T) => settled.get(id) !== value,
        settle: (id: string, value: T) =>
            setSettled((all) => (all.get(id) === value ? all : new Map(all).set(id, value))),
    };
}
