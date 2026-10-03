import clsx from 'clsx';
import { FILLS, ariaLabelOf } from './tints';
import type { Tally } from '@/lib/insights';
import type { FocusEvent, PointerEvent } from 'react';

const COLUMN =
    'flex h-full flex-1 flex-col items-center justify-end rounded-chip transition-opacity ease-out';
const STACK =
    'flex min-h-1.5 w-full max-w-6 origin-bottom flex-col-reverse gap-px overflow-hidden rounded-chip transition-transform duration-250 ease-out motion-reduce:transition-none starting:scale-y-0';

interface BarProps {
    bar: Tally;
    most: number;
    delay: number;
    faded: boolean;
    pick: () => void;
    unpick: () => void;
    jump: () => void;
}

function Bar({ bar, most, delay, faded, pick, unpick, jump }: BarProps) {
    // A future hour shows nothing
    if (bar.later) return <div className="flex-1" />;

    // Only a mouse picks by hovering
    const hover = (event: PointerEvent) => {
        if (event.pointerType === 'mouse') pick();
    };

    // Only the keyboard picks by focusing
    const focus = (event: FocusEvent<HTMLButtonElement>) => {
        if (event.currentTarget.matches(':focus-visible')) pick();
    };

    const column = clsx(COLUMN, faded && 'opacity-35');

    if (bar.total === 0) {
        return (
            <div onPointerEnter={hover} className={column}>
                <div className="h-0.75 w-full max-w-6 rounded-full bg-line" />
            </div>
        );
    }

    const grow = { height: `${(bar.total / most) * 100}%`, transitionDelay: `${delay}ms` };

    return (
        <button
            type="button"
            onPointerEnter={hover}
            onFocus={focus}
            onBlur={unpick}
            onClick={jump}
            aria-label={ariaLabelOf(bar)}
            className={clsx(column, 'cursor-pointer active:opacity-70')}
        >
            <div className={STACK} style={grow}>
                {bar.parts.map(([kind, count]) => (
                    <div key={kind} className={FILLS[kind]} style={{ flex: count }} />
                ))}
            </div>
        </button>
    );
}

export default Bar;
