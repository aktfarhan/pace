import { poll } from '@/lib/poll';
import { readStatus } from '@/lib/pace';
import { useEffect, useState } from 'react';
import type { SystemStatus } from '@/types/status';

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

        const stop = poll(read);
        return () => {
            control.abort();
            stop();
        };
    }, []);

    return status;
}
