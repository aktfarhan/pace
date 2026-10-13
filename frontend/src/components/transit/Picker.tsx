import clsx from 'clsx';
import { rowsOf } from './standing';
import { percentOf } from './figures';
import { useMenu } from '@/hooks/useMenu';
import { ChevronDown } from 'lucide-react';
import { MENU, OPTION, RAISED, TRACK, UNPICKED } from '@/components/layout/tints';
import type { Branching } from '@/types/transit';

interface PickerProps {
    branching: Branching;
}

function Picker({ branching }: PickerProps) {
    const { line, pick, shares } = branching;
    const { open, setOpen, openerRef, listRef, close } = useMenu();
    const { rows, shown } = rowsOf(branching);

    // Picking a branch puts the list away
    const choose = (id: string | null) => {
        pick(id);
        close();
    };

    return (
        <div className="relative min-w-0">
            <button
                ref={openerRef}
                type="button"
                aria-expanded={open}
                aria-label={`${line.label} branch, ${shown.name}`}
                onClick={() => setOpen(!open)}
                className={clsx(
                    TRACK,
                    'flex max-w-full cursor-pointer items-center gap-1.5 py-1.5 pr-2.5 pl-3.25 font-mono text-tag uppercase transition ease-out hover:text-soft hover:inset-ring-white/12 active:scale-97',
                    shown.id === null ? 'text-dim' : line.text,
                )}
            >
                <span className="truncate">{shown.name}</span>
                <ChevronDown
                    size={12}
                    strokeWidth={2.2}
                    className={clsx(
                        'shrink-0 transition-transform duration-200 ease-out',
                        open && 'rotate-180',
                    )}
                />
            </button>
            {open && (
                <div
                    ref={listRef}
                    className={`${MENU} absolute top-full right-0 z-10 mt-1.5 w-52 origin-top-right`}
                >
                    <div className="flex max-h-108 flex-col overflow-y-auto overscroll-contain p-1">
                        {rows.map((row) => (
                            <button
                                key={row.name}
                                type="button"
                                aria-pressed={row.id === shown.id}
                                onClick={() => choose(row.id)}
                                className={clsx(
                                    OPTION,
                                    row.id === shown.id ? [RAISED, line.text] : UNPICKED,
                                )}
                            >
                                <span className="flex-1 text-left">{row.name}</span>
                                <span className="text-hush tabular-nums">
                                    {percentOf(shares[row.id ?? line.id])}
                                </span>
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

export default Picker;
