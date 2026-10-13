import { useCallback, useEffect, useRef, useState } from 'react';

// An open menu and what closes it
export function useMenu() {
    const [open, setOpen] = useState(false);
    const openerRef = useRef<HTMLButtonElement>(null);
    const listRef = useRef<HTMLDivElement>(null);

    // Puts the list away
    const close = useCallback(() => {
        setOpen(false);
        openerRef.current?.focus();
    }, []);

    useEffect(() => {
        const list = listRef.current;
        if (!open || list === null) return;
        const row = list.querySelector<HTMLElement>('[aria-pressed="true"]');
        row?.focus({ preventScroll: true });

        // A long list opens scrolled to the current pick
        const scroller = row?.parentElement ?? null;
        if (row !== null && scroller !== null && scroller.scrollHeight > scroller.clientHeight) {
            scroller.scrollTop = row.offsetTop - (scroller.clientHeight - row.offsetHeight) / 2;
        }

        // A press outside the list or its opener closes it
        const away = ({ target }: Event) => {
            const node = target instanceof Node ? target : null;
            if (!list.contains(node) && !openerRef.current?.contains(node)) setOpen(false);
        };

        // Escape closes and arrows walk the list
        const keys = (event: KeyboardEvent) => {
            if (event.key === 'Escape') close();
            if (!list.contains(document.activeElement)) return;

            // Tab leaves from the opener
            if (event.key === 'Tab') {
                close();
                if (event.shiftKey) event.preventDefault();
            }

            // Up and down move between rows
            if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                const rows = [...list.querySelectorAll('button')];
                const now = rows.findIndex((row) => row === document.activeElement);
                rows[now + (event.key === 'ArrowDown' ? 1 : -1)]?.focus();
                event.preventDefault();
            }
        };

        // A scroll inside the list itself keeps it open
        const drop = ({ target }: Event) => {
            if (!(target instanceof Node && list.contains(target))) setOpen(false);
        };

        document.addEventListener('pointerdown', away);
        document.addEventListener('keydown', keys);
        document.addEventListener('scroll', drop, true);
        window.addEventListener('resize', drop);

        return () => {
            document.removeEventListener('pointerdown', away);
            document.removeEventListener('keydown', keys);
            document.removeEventListener('scroll', drop, true);
            window.removeEventListener('resize', drop);
        };
    }, [open, close]);

    return { open, setOpen, openerRef, listRef, close };
}
