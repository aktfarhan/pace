import clsx from 'clsx';
import Toggle from './Toggle';
import Expanded from './Expanded';
import { useEffect, useState } from 'react';
import { onWide, wide } from '@/lib/device';
import { setDrawer, useDrawer } from '@/hooks/useDrawer';
import { ShowLine, useShowLine } from '@/hooks/useShowLine';
import type { PaneProps } from './tints';

type DrawerProps = Omit<PaneProps, 'toggle'>;

function Drawer({ status, page, select }: DrawerProps) {
    const open = useDrawer();
    const show = useShowLine();
    const [built, setBuilt] = useState(false);

    if (open && !built) setBuilt(true);

    const close = () => setDrawer(false);

    // Widening past the drawer puts it away
    useEffect(() => onWide(() => wide() && setDrawer(false)), []);

    return (
        <>
            <header className="flex shrink-0 items-center border-b border-line bg-rail py-1 pl-2 sm:hidden">
                <Toggle toggle={() => setDrawer(true)} expanded={open} />
            </header>
            <div
                aria-hidden="true"
                onClick={close}
                className={clsx(
                    'fixed inset-0 z-40 bg-ink/60 transition-opacity ease-drawer lg:hidden',
                    open
                        ? 'opacity-100 duration-300'
                        : 'pointer-events-none opacity-0 duration-200',
                )}
            />
            <div
                inert={!open}
                className={clsx(
                    'fixed inset-y-0 left-0 z-50 w-[min(var(--spacing-expanded),88vw)] border-r border-line bg-rail shadow-float transition-[translate,opacity,visibility] ease-drawer motion-reduce:duration-200 lg:hidden',
                    open
                        ? 'translate-x-0 duration-300'
                        : 'invisible -translate-x-full duration-200 motion-reduce:translate-x-0 motion-reduce:opacity-0',
                )}
            >
                {built && (
                    <ShowLine
                        value={(lineId) => {
                            show(lineId);
                            close();
                        }}
                    >
                        <Expanded
                            status={status}
                            page={page}
                            select={(next) => {
                                close();
                                select(next);
                            }}
                        />
                    </ShowLine>
                )}
            </div>
        </>
    );
}

export default Drawer;
