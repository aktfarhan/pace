import { poll } from '@/lib/poll';
import { readStatus } from '@/lib/pace';
import { useEffect, useState } from 'react';
import type { SystemStatus } from '@/types/status';

// Hands over a status the Transit tab already read
let fed: ((status: SystemStatus) => void) | null = null;

// Shares the Transit tab's status with the rest of the app
export function feedStatus(status: SystemStatus) {
    fed?.(status);
}

// The line status
export function useStatus(paused: boolean) {
    const [status, setStatus] = useState<SystemStatus | null>(null);

    // Takes the Transit tab's reads
    useEffect(() => {
        fed = setStatus;
        return () => {
            fed = null;
        };
    }, []);

    useEffect(() => {
        if (paused) return;
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
    }, [paused]);

    return status;
}
