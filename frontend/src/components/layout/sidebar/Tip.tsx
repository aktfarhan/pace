import clsx from 'clsx';
import { useTip } from '@/hooks/useTip';
import type { ReactNode } from 'react';

interface TipProps {
    label: string;
    children: ReactNode;
}

function Tip({ label, children }: TipProps) {
    const { spot, handlers } = useTip();

    return (
        <div {...handlers}>
            {children}
            {spot !== null && (
                <span
                    aria-hidden="true"
                    style={{ left: spot.x, top: spot.y }}
                    className={clsx(
                        'pointer-events-none fixed z-50 origin-left -translate-y-1/2 rounded-chip border border-edge bg-bubble px-2.5 py-1.25 text-row font-medium whitespace-nowrap text-cream shadow-float',
                        !spot.instant &&
                            'transition-[opacity,scale] duration-125 ease-out starting:scale-97 starting:opacity-0 motion-reduce:starting:scale-100',
                    )}
                >
                    {label}
                </span>
            )}
        </div>
    );
}

export default Tip;
