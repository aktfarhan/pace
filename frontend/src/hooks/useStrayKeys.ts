import { claimed, keyedPage } from '@/lib/keys';
import { useEffect, useEffectEvent } from 'react';
import type { RefObject } from 'react';

// Keys typed outside the ask input box are still registered
export function useStrayKeys(
    boxRef: RefObject<HTMLInputElement | null>,
    add: (key: string) => void,
) {
    const press = useEffectEvent((event: KeyboardEvent) => {
        const box = boxRef.current;
        if (box === null || claimed(event)) return;

        // Only one character; page keys are shortcuts
        const { key } = event;
        if (key.length !== 1 || keyedPage(key) !== undefined) return;

        // Space still presses a focused button
        if (key === ' ' && event.target instanceof HTMLButtonElement) return;

        event.preventDefault();
        add(key);

        // The box takes the focus
        box.focus();
    });

    useEffect(() => {
        window.addEventListener('keydown', press);
        return () => window.removeEventListener('keydown', press);
    }, []);
}
