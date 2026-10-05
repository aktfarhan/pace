import clsx from 'clsx';
import Expanded from './Expanded';
import Collapsed from './Collapsed';
import { onWide, wide } from '@/lib/device';
import { setDrawer } from '@/hooks/useDrawer';
import { useState, useSyncExternalStore } from 'react';
import type { PaneProps } from './tints';
import type { TransitionEvent } from 'react';

// One layer per state, stacked
const LAYER = 'absolute inset-y-0 left-0 transition-opacity duration-150 ease-out';

// The outgoing layer clears before the incoming one arrives
const SHOWN = 'opacity-100 delay-150 starting:opacity-0';
const HIDDEN = 'pointer-events-none opacity-0';

interface SidebarProps extends PaneProps {
    open: boolean;
}

function Sidebar({ status, open: wanted, toggle, page, select }: SidebarProps) {
    const fits = useSyncExternalStore(onWide, wide);
    const open = wanted && fits;
    const [settling, setSettling] = useState(false);
    const [snap, setSnap] = useState(false);
    const [was, setWas] = useState({ open, fits });

    // A toggle glides between the two
    if (was.open !== open || was.fits !== fits) {
        const resized = was.fits !== fits;
        setWas({ open, fits });
        setSnap(resized);
        setSettling(!resized && was.open !== open);
    }
    const shown = snap ? 'opacity-100' : SHOWN;

    const settle = (event: TransitionEvent<HTMLElement>) => {
        if (event.target === event.currentTarget && event.propertyName === 'width') {
            setSettling(false);
        }
    };

    return (
        <aside
            onTransitionEnd={settle}
            className={clsx(
                'relative hidden shrink-0 overflow-hidden border-r border-line bg-rail sm:block',
                !snap && 'transition-[width] duration-300 ease-drawer motion-reduce:duration-1',
                open ? 'w-expanded' : 'w-collapsed',
            )}
        >
            {(open || settling) && (
                <div className={clsx(LAYER, 'w-expanded', open ? shown : HIDDEN)} inert={!open}>
                    <Expanded status={status} toggle={toggle} page={page} select={select} />
                </div>
            )}
            {(!open || settling) && (
                <div className={clsx(LAYER, open ? HIDDEN : shown)} inert={open}>
                    <Collapsed
                        status={status}
                        toggle={fits ? toggle : () => setDrawer(true)}
                        page={page}
                        select={select}
                    />
                </div>
            )}
        </aside>
    );
}

export default Sidebar;
