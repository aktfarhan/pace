import clsx from 'clsx';
import Expanded from './Expanded';
import Collapsed from './Collapsed';
import { useState, type TransitionEvent } from 'react';
import { useStatus } from '@/hooks/useStatus';
import type { Page } from './tints';

// One layer per state, stacked
const LAYER = 'absolute inset-y-0 left-0 transition-opacity duration-150';

// The outgoing layer clears before the incoming one arrives
const SHOWN = 'opacity-100 delay-150 starting:opacity-0';
const HIDDEN = 'pointer-events-none opacity-0';

interface SidebarProps {
    open: boolean;
    toggle: () => void;
    page: Page;
    select: (page: Page) => void;
}

function Sidebar({ open, toggle, page, select }: SidebarProps) {
    const status = useStatus();
    const [settling, setSettling] = useState(false);
    const [wasOpen, setWasOpen] = useState(open);

    // Both layers are mounted only while the width is on its way
    if (wasOpen !== open) {
        setWasOpen(open);
        setSettling(true);
    }

    const settle = (event: TransitionEvent<HTMLElement>) => {
        if (event.target === event.currentTarget && event.propertyName === 'width') {
            setSettling(false);
        }
    };

    return (
        <aside
            onTransitionEnd={settle}
            className={clsx(
                'relative hidden shrink-0 overflow-hidden border-r border-line bg-rail transition-[width] duration-300 lg:block',
                open ? 'w-expanded' : 'w-collapsed',
            )}
        >
            {(open || settling) && (
                <div className={clsx(LAYER, open ? SHOWN : HIDDEN)} inert={!open}>
                    <Expanded status={status} toggle={toggle} page={page} select={select} />
                </div>
            )}
            {(!open || settling) && (
                <div className={clsx(LAYER, open ? HIDDEN : SHOWN)} inert={open}>
                    <Collapsed status={status} toggle={toggle} page={page} select={select} />
                </div>
            )}
        </aside>
    );
}

export default Sidebar;
