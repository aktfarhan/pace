import { useState } from 'react';

// Whether each value has changed since it was first drawn
export function useTicks(pairs: [string, string][]) {
    // The value each id was first drawn with
    const [firsts] = useState(() => new Map(pairs));

    // Ids that have changed once always get changed status
    const [moved, setMoved] = useState(() => new Set<string>());
    const shifted = pairs.filter(([id, value]) => !moved.has(id) && firsts.get(id) !== value);
    if (shifted.length > 0) setMoved(new Set([...moved, ...shifted.map(([id]) => id)]));

    return (id: string) => moved.has(id);
}
