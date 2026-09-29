import { useState } from 'react';
import { LINE_BY_ID } from '@/lib/lines';
import type { Tab } from '@/components/transit/tints';
import type { Page } from '@/components/layout/sidebar/tints';

// The Transit tab, and a way to open a line on it
export function useLineTab(setPage: (page: Page) => void) {
    const [tab, setTab] = useState<Tab>('All');

    // Opens a line on Transit page from the sidebar
    const show = (lineId: string) => {
        setTab(LINE_BY_ID[lineId].label);
        setPage('Transit');
    };

    return { tab, setTab, show };
}
