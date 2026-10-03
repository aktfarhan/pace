import { useEffect, useRef, useState } from 'react';

// How long a failure line stays up
export const FAILED_MS = 5000;

// A value shown only for a while
export function useMoment<T>(rest: T, ms: number) {
    const [value, setValue] = useState(rest);
    const timer = useRef(0);

    useEffect(() => () => window.clearTimeout(timer.current), []);

    // A new one restarts the wait
    const show = (next: T) => {
        window.clearTimeout(timer.current);
        setValue(next);
        if (next !== rest) timer.current = window.setTimeout(() => setValue(rest), ms);
    };

    return [value, show] as const;
}
