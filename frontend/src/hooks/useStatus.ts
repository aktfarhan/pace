import { readStatus } from '@/lib/pace';
import { useEffect, useState } from 'react';
import type { SystemStatus } from '@/types/status';

// How long a reading is held
const POLL_MS = 30000;

// The line status, re-read on a timer
export function useStatus() {
    const [status, setStatus] = useState<SystemStatus | null>(null);

    useEffect(() => {
        const control = new AbortController();

        async function read() {
            try {
                setStatus(await readStatus(control.signal));
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

    return status;
}
