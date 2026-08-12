import clsx from 'clsx';
import { Bookmark, Clock, Lock, MapPin, MessageSquare, Settings } from 'lucide-react';

const ROW = 'flex items-center gap-3.25 rounded-row px-3 py-2.5 text-sm';

const CURRENT = 'Ask';

const NAV = [
    { label: 'Ask', Icon: MessageSquare },
    { label: 'Map', Icon: MapPin },
    { label: 'History', Icon: Clock },
    { label: 'Saved', Icon: Bookmark },
];

function Sidebar() {
    return (
        <aside className="hidden w-88 shrink-0 flex-col border-r border-line bg-rail px-4.25 pt-5 pb-4.5 lg:flex">
            <div className="flex items-center gap-3 px-3">
                <span className="relative grid size-7 shrink-0 place-items-center rounded-mark bg-accent">
                    <span className="text-mark text-onaccent">p</span>
                    <span className="absolute right-hair bottom-hair size-1.25 rounded-full bg-ember" />
                </span>
                <span className="text-brand text-bright uppercase">Pace</span>
                <span className="ml-auto font-mono text-coverage text-ghost uppercase">
                    Boston · MBTA
                </span>
            </div>

            <nav className="mt-4 flex flex-col gap-0.5">
                {NAV.map(({ label, Icon }) => {
                    const current = label === CURRENT;
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
                                size={18}
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

            <div className="mt-auto flex flex-col gap-2.25 pt-3.5">
                <div className="-mx-4.25 h-px bg-seam" />
                <div className={clsx(ROW, 'font-medium text-quiet')}>
                    <Settings
                        size={18}
                        strokeWidth={1.8}
                        className="text-hush"
                        aria-hidden="true"
                    />
                    Settings
                </div>
                <div className="flex items-center gap-2.75 px-3 pb-0.5 text-faint">
                    <Lock size={13} strokeWidth={1.8} aria-hidden="true" />
                    <span className="font-mono text-device uppercase">No account</span>
                </div>
            </div>
        </aside>
    );
}

export default Sidebar;
