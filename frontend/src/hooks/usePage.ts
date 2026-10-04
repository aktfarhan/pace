import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import type { Page } from '@/components/layout/sidebar/tints';

// The open page: its title and its scroll place
export function usePage() {
    const [page, setPage] = useState<Page>('Ask');
    const mainRef = useRef<HTMLElement>(null);
    const scrolls = useRef(new Map<Page, number>());

    // Each page keeps its own place in the shared scroll area
    useLayoutEffect(() => {
        if (mainRef.current !== null) mainRef.current.scrollTop = scrolls.current.get(page) ?? 0;
    }, [page]);

    // The tab names the page it shows
    useEffect(() => {
        document.title = page === 'Ask' ? 'Pace' : `${page} · Pace`;
    }, [page]);

    const remember = (top: number) => scrolls.current.set(page, top);
    return { page, setPage, mainRef, remember };
}
