import { readTransit } from '@/lib/pace';
import { useEffect, useState } from 'react';
import type { Transit } from '@/types/transit';

// How long a reading is held
const POLL_MS = 30000;

// The transit page's data, re-read on a timer
export function useTransit() {
    const [transit, setTransit] = useState<Transit | null>(null);

    useEffect(() => {
        const control = new AbortController();

        async function read() {
            try {
                setTransit(await readTransit(control.signal));
            } catch (error) {
                if (!control.signal.aborted) {
                    console.error(error);
                }
            }
        }

        read();
        const timer = setInterval(read, POLL_MS);
        return () => {
            control.abort();
            clearInterval(timer);
        };
    }, []);

    return transit;
}
