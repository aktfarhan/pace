import { useEffect, useEffectEvent } from 'react';
import type { RefObject } from 'react';

// Keeps focus inside the open drawer and locks the page behind
export function useModal(
    panelRef: RefObject<HTMLElement | null>,
    scrimRef: RefObject<HTMLElement | null>,
    open: boolean,
    close: () => void,
) {
    const dismiss = useEffectEvent(close);

    useEffect(() => {
        const panel = panelRef.current;
        if (!open || panel === null || panel.parentElement === null) return;

        // Remembers the button that opened it
        const opener = document.activeElement;
        panel.querySelector<HTMLElement>('[aria-current="page"]')?.focus();

        // Locks everything behind except the dimmed layer
        const behind = [...panel.parentElement.children].filter(
            (one): one is HTMLElement =>
                one instanceof HTMLElement && one !== panel && one !== scrimRef.current,
        );
        behind.forEach((one) => (one.inert = true));

        // Escape closes
        const escape = (event: KeyboardEvent) => event.key === 'Escape' && dismiss();
        document.addEventListener('keydown', escape);
        return () => {
            document.removeEventListener('keydown', escape);
            behind.forEach((one) => (one.inert = false));

            // Focus goes back to whichever button opened it
            if (opener instanceof HTMLElement && opener !== document.body) {
                opener.focus();
                return;
            }
            // Safari's clicks focus nothing
            behind
                .map((one) => one.querySelector('button'))
                .find((one) => one?.checkVisibility())
                ?.focus();
        };
    }, [panelRef, scrimRef, open]);
}
