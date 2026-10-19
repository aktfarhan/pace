import { still } from '@/lib/device';
import { useId, useLayoutEffect, useRef } from 'react';
import type { ReactNode } from 'react';

// Room for the first point's cap
const PAD = 6;

// How the lines sweep in, first and on a switch
const EASE = 'cubic-bezier(0.16, 1, 0.3, 1)';
const FIRST = { duration: 900, easing: EASE };
const AGAIN = { duration: 160, easing: EASE };

interface SweepProps {
    shown: string;
    left: number;
    width: number;
    height: number;
    children: ReactNode;
}

function Sweep({ shown, left, width, height, children }: SweepProps) {
    const clip = useId();
    const rectRef = useRef<SVGRectElement>(null);
    const swept = useRef<string | null>(null);

    // Sweeps in only for new lines
    useLayoutEffect(() => {
        const rect = rectRef.current;
        if (rect === null || swept.current === shown) return;

        // Slow the first time
        const first = swept.current === null;
        swept.current = shown;
        if (still()) return;
        rect.animate(
            [{ transform: 'scaleX(0)' }, { transform: 'scaleX(1)' }],
            first ? FIRST : AGAIN,
        );
    }, [shown]);

    return (
        <>
            <defs>
                <clipPath id={clip}>
                    <rect
                        ref={rectRef}
                        x={left - PAD}
                        width={Math.max(width - left + PAD, 0)}
                        height={height}
                        style={{ transformBox: 'fill-box', transformOrigin: 'left' }}
                    />
                </clipPath>
            </defs>
            <g clipPath={`url(#${clip})`}>{children}</g>
        </>
    );
}

export default Sweep;
