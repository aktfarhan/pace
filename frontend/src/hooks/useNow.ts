import { useEffect, useState } from 'react';

// A clock that ticks every second
export function useNow() {
    const [now, setNow] = useState(0);

    // Read on mount, not in render
    useEffect(() => {
        setNow(Date.now());
        const timer = setInterval(() => setNow(Date.now()), 1000);
        return () => clearInterval(timer);
    }, []);

    return now;
}
