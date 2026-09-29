import { useEffect, useState } from 'react';

// A clock that ticks every second
export function useNow() {
    const [now, setNow] = useState(Date.now);

    useEffect(() => {
        const timer = setInterval(() => setNow(Date.now()), 1000);
        return () => clearInterval(timer);
    }, []);

    return now;
}
