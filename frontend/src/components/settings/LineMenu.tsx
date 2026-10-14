import clsx from 'clsx';
import { useState } from 'react';
import { useMenu } from '@/hooks/useMenu';
import { ChevronDown } from 'lucide-react';
import { TABS } from '@/components/transit/tints';
import { MENU, OPTION, RAISED, TRACK, UNPICKED } from '@/components/layout/tints';
import type { MouseEvent } from 'react';
import type { Tab } from '@/components/transit/tints';

// Each tab
const ROWS = TABS.map((tab) => ({ ...tab, name: tab.label === 'All' ? 'All lines' : tab.label }));

interface LineMenuProps {
    value: Tab;
    pick: (line: Tab) => void;
}

function LineMenu({ value, pick }: LineMenuProps) {
    const { open, setOpen, openerRef, listRef, close } = useMenu();
    const [left, setLeft] = useState(false);
    const shown = ROWS[TABS.findIndex((tab) => tab.label === value)];

    // Opens toward the side with room
    const toggle = ({ currentTarget }: MouseEvent<HTMLButtonElement>) => {
        const box = currentTarget.getBoundingClientRect();
        setLeft(box.left + box.width / 2 < window.innerWidth / 2);
        setOpen(!open);
    };

    // Picking a line puts the list away
    const choose = (line: Tab) => {
        pick(line);
        close();
    };

    return (
        <div className="relative">
            <button
                ref={openerRef}
                type="button"
                aria-expanded={open}
                aria-label={`Transit opens on ${shown.name}`}
                onClick={toggle}
                className={clsx(
                    TRACK,
                    'flex cursor-pointer items-center gap-2 py-1.5 pr-2.5 pl-3.25 font-mono text-tag text-cream uppercase transition ease-out hover:inset-ring-white/12 active:scale-97',
                )}
            >
                {shown.dot !== null && (
                    <span className={clsx('size-1.5 rounded-full', shown.dot)} />
                )}
                {shown.name}
                <ChevronDown
                    size={12}
                    strokeWidth={2.2}
                    className={clsx(
                        'text-hush transition-transform duration-200 ease-out',
                        open && 'rotate-180',
                    )}
                />
            </button>
            {open && (
                <div
                    ref={listRef}
                    className={clsx(
                        `${MENU} absolute top-full z-10 mt-1.5 flex w-48 flex-col p-1`,
                        left ? 'left-0 origin-top-left' : 'right-0 origin-top-right',
                    )}
                >
                    {ROWS.map((row) => (
                        <button
                            key={row.label}
                            type="button"
                            aria-pressed={row.label === value}
                            onClick={() => choose(row.label)}
                            className={clsx(
                                OPTION,
                                'items-center gap-2',
                                row.label === value ? [RAISED, 'text-cream'] : UNPICKED,
                            )}
                        >
                            <span className={clsx('size-1.5 rounded-full', row.dot)} />
                            {row.name}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}

export default LineMenu;
