import clsx from 'clsx';
import Status from './Status';
import Toggle from './Toggle';
import { NAV } from './tints';
import Collapsed from './Collapsed';
import { Settings } from 'lucide-react';
import { useStatus } from '@/hooks/useStatus';

const ROW = 'flex h-11 items-center gap-3.25 rounded-row px-3 text-sm';

interface SidebarProps {
    open: boolean;
    toggle: () => void;
}

function Sidebar({ open, toggle }: SidebarProps) {
    const status = useStatus();

    if (!open) {
        return <Collapsed status={status} toggle={toggle} />;
    }

    return (
        <aside className="hidden w-90 shrink-0 flex-col overflow-y-auto border-r border-line bg-rail px-3 lg:flex">
            <div className="sticky top-0 z-10 flex items-center gap-3 bg-rail px-1.5 pt-5 pb-1">
                <span className="relative grid size-7 shrink-0 place-items-center rounded-mark bg-accent">
                    <span className="text-mark text-onaccent">p</span>
                    <span className="absolute right-hair bottom-hair size-1.25 rounded-full bg-ember" />
                </span>
                <span className="text-brand text-bright uppercase">Pace</span>
                <div className="ml-auto">
                    <Toggle toggle={toggle} />
                </div>
            </div>

            <nav className="mt-3.5 flex flex-col gap-0.5 px-1.5">
                {NAV.map(({ label, Icon }) => {
                    const current = label === 'Ask';
                    return (
                        <div
                            key={label}
                            className={clsx(
                                ROW,
                                current
                                    ? 'bg-accent/11 font-strong text-accent'
                                    : 'font-medium text-quiet',
                            )}
                        >
                            <Icon
                                size={20}
                                strokeWidth={1.8}
                                fill={current ? 'currentColor' : 'none'}
                                stroke={current ? 'none' : 'currentColor'}
                                className={current ? undefined : 'text-hush'}
                                aria-hidden="true"
                            />
                            {label}
                        </div>
                    );
                })}
            </nav>

            <Status status={status} />

            <div className="sticky bottom-0 mt-auto flex flex-col gap-3 bg-rail px-1.5 pt-3 pb-3">
                <div className="-mx-1.5 h-px bg-seam" />
                <div className={clsx(ROW, 'font-medium text-quiet')}>
                    <Settings
                        size={20}
                        strokeWidth={1.8}
                        className="text-hush"
                        aria-hidden="true"
                    />
                    Settings
                </div>
            </div>
        </aside>
    );
}

export default Sidebar;
