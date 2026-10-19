import { useLayoutEffect, useRef } from 'react';
import type { Box, Mark } from './plot';

// A reading this close to the flag's end is under it
const NEAR = 12;

// Further than this, the top is clear again
const CLEAR = 28;

// The flag's gap from the plot's top or floor
const INSET = 4;

interface CalloutProps {
    said: string[];
    x: number;
    box: Box;
    marks: Mark[];
}

function Callout({ said, x, box, marks }: CalloutProps) {
    const flagRef = useRef<HTMLDivElement>(null);
    const footRef = useRef(false);
    const [clock, ...rest] = said;

    // Centred on the line
    useLayoutEffect(() => {
        const flag = flagRef.current;
        if (flag === null) return;

        // Both sizes read before any write
        const [width, height] = [flag.offsetWidth, flag.offsetHeight];
        const left = Math.max(Math.min(x - width / 2, box.right - width), box.left);
        flag.style.left = `${left}px`;

        // The end covering fewer readings wins
        const count = (hit: (y: number) => boolean) =>
            marks.filter(({ spot }) => hit(spot.y)).length;
        const top = count((y) => y < box.ceil + height + NEAR);
        const foot = count((y) => y > box.floor - height - NEAR);
        const clear = count((y) => y < box.ceil + height + CLEAR) === 0;
        footRef.current = footRef.current ? !clear && foot <= top : top > foot;
        flag.style.top = `${footRef.current ? box.floor - height - INSET : box.ceil + INSET}px`;
    });

    return (
        <div
            ref={flagRef}
            aria-hidden="true"
            className="pointer-events-none absolute flex items-center gap-1.5 rounded-chip border border-edge bg-bubble px-2 py-1 font-mono text-tag whitespace-nowrap uppercase shadow-float transition-opacity ease-out select-none starting:opacity-0"
        >
            <span className="text-cream tabular-nums">{clock}</span>
            {rest.length > 0 && <span className="text-hush tabular-nums">{rest.join(' · ')}</span>}
        </div>
    );
}

export default Callout;
