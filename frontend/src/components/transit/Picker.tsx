import clsx from 'clsx';
import { ChevronDown } from 'lucide-react';
import { EVERY, OPENER, OPTION } from './tints';
import { useEffect, useRef, useState } from 'react';
import type { Branching } from '@/types/transit';

interface PickerProps {
    branching: Branching;
}

function Picker({ branching }: PickerProps) {
    const { line, branches, branch, pick } = branching;
    const [open, setOpen] = useState(false);
    const wrapRef = useRef<HTMLDivElement>(null);

    // The line itself labels the list
    const rows = [{ id: null, name: EVERY }, ...branches];
    const shown = rows.find((row) => row.id === branch) ?? rows[0];

    // A press anywhere else puts the list away
    useEffect(() => {
        if (!open) return;

        const away = ({ target }: PointerEvent) => {
            const inside = target instanceof Node && wrapRef.current?.contains(target);
            if (!inside) setOpen(false);
        };

        document.addEventListener('pointerdown', away);
        return () => document.removeEventListener('pointerdown', away);
    }, [open]);

    // Picking a branch puts the list away
    const choose = (id: string | null) => {
        pick(id);
        setOpen(false);
    };

    return (
        <div ref={wrapRef} className="relative shrink-0">
            <button
                type="button"
                aria-expanded={open}
                aria-label={`${line.label} branch, ${shown.name}`}
                onClick={() => setOpen(!open)}
                className={clsx(OPENER, shown.id === null ? 'text-dim' : line.text)}
            >
                {shown.name}
                <ChevronDown
                    size={13}
                    strokeWidth={2.1}
                    className={clsx('shrink-0 transition-transform', open && 'rotate-180')}
                />
            </button>

            {open && (
                <div className="absolute top-full right-0 z-10 mt-1.5 flex max-h-64 w-44 flex-col overflow-y-auto rounded-row border border-edge bg-bubble p-1">
                    {rows.map((row) => (
                        <button
                            key={row.id ?? EVERY}
                            type="button"
                            aria-pressed={row.id === shown.id}
                            onClick={() => choose(row.id)}
                            className={clsx(OPTION, row.id === shown.id ? line.text : 'text-soft')}
                        >
                            {row.name}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}

export default Picker;
