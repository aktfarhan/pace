import clsx from 'clsx';
import { useTip } from '@/hooks/useTip';
import type { ReactNode } from 'react';

interface TipProps {
    label: string;
    keycap?: string;
    children: ReactNode;
}

function Tip({ label, keycap, children }: TipProps) {
    const { spot, handlers } = useTip();

    return (
        <div {...handlers}>
            {children}
            {spot !== null && (
                <span
                    aria-hidden="true"
                    style={{ left: spot.x, top: spot.y }}
                    className={clsx(
                        'pointer-events-none fixed z-50 flex origin-left -translate-y-1/2 items-center gap-2 rounded-chip border border-edge bg-bubble px-2.5 py-1.25 text-row font-medium whitespace-nowrap text-cream shadow-float',
                        !spot.instant &&
                            'transition-[opacity,scale] duration-125 ease-out starting:scale-97 starting:opacity-0 motion-reduce:starting:scale-100',
                    )}
                >
                    {label}
                    {keycap !== undefined && (
                        <kbd className="grid h-5 min-w-5 place-items-center rounded-mark border border-edge bg-line px-1 font-mono text-tag text-soft shadow-card">
                            {keycap}
                        </kbd>
                    )}
                </span>
            )}
        </div>
    );
}

export default Tip;
