import { useUndo } from './useUndo';
import { flushSync } from 'react-dom';
import { useRef, useState } from 'react';
import { FAILED_MS, useMoment } from './useMoment';
import type { RefObject } from 'react';

// Remove a saved place or trip
export function useRemoval(
    drop: (id: number) => Promise<void>,
    id: number,
    titleRef: RefObject<HTMLHeadingElement | null>,
) {
    const [removing, setRemoving] = useState(false);
    const [failed, setFailed] = useMoment(false, FAILED_MS);
    const { pending, start, undo } = useUndo();
    const cardRef = useRef<HTMLDivElement>(null);
    const removeRef = useRef<HTMLButtonElement>(null);

    const commit = async () => {
        setRemoving(true);
        setFailed(false);
        if (cardRef.current?.contains(document.activeElement)) {
            titleRef.current?.focus({ preventScroll: true });
        }
        try {
            await drop(id);
        } catch (error) {
            console.error(error);
            flushSync(() => {
                setRemoving(false);
                setFailed(true);
            });
            if (document.activeElement === titleRef.current) removeRef.current?.focus();
        }
    };

    // Focus returns to the x on undo
    const back = () => {
        flushSync(undo);
        removeRef.current?.focus();
    };

    return {
        cardRef,
        removeRef,
        going: pending || removing,
        failed,
        remove: () => start(commit),
        undo: pending ? back : null,
    };
}
