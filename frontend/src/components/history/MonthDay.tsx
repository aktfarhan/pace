import clsx from 'clsx';
import { ariaLabelOf } from './tints';
import type { Tally } from '@/lib/insights';
import type { FocusEvent, PointerEvent } from 'react';

// Tints from a quiet day to the busiest
const LEVELS = ['bg-accent/12', 'bg-accent/24', 'bg-accent/42', 'bg-accent/72'];

const CELL =
    'flex items-center justify-center rounded-sm font-mono text-axis tabular-nums transition ease-out starting:opacity-0';
const RING = 'ring-1 ring-accent/55 ring-inset';

interface MonthDayProps {
    day: Tally;
    most: number;
    start?: number;
    faded: boolean;
    pick: () => void;
    unpick: () => void;
    jump: () => void;
}

function MonthDay({ day, most, start, faded, pick, unpick, jump }: MonthDayProps) {
    // Future or dropped days stay dim
    const quiet = day.later || day.lost;
    const dim = faded ? 'opacity-35' : quiet && 'opacity-45';

    // Only a mouse picks by hovering
    const hover = (event: PointerEvent) => {
        if (event.pointerType === 'mouse' && !quiet) pick();
    };

    // Only the keyboard picks by focusing
    const focus = (event: FocusEvent<HTMLButtonElement>) => {
        if (event.currentTarget.matches(':focus-visible')) pick();
    };

    // A day with no questions just shows its number
    if (day.total === 0) {
        return (
            <div
                onPointerEnter={hover}
                style={{ gridColumnStart: start }}
                className={clsx(
                    CELL,
                    'text-faint',
                    !quiet && 'bg-white/3 contrast-more:bg-white/10',
                    day.current && RING,
                    dim,
                )}
            >
                {day.label}
            </div>
        );
    }

    const level = Math.ceil((day.total / most) * LEVELS.length) - 1;

    return (
        <button
            type="button"
            onPointerEnter={hover}
            onFocus={focus}
            onBlur={unpick}
            onClick={jump}
            aria-label={ariaLabelOf(day)}
            style={{ gridColumnStart: start }}
            className={clsx(
                CELL,
                LEVELS[level],
                level === LEVELS.length - 1 ? 'text-ink' : 'text-cream',
                day.current && RING,
                dim,
                'cursor-pointer active:scale-96',
            )}
        >
            {day.label}
        </button>
    );
}

export default MonthDay;
