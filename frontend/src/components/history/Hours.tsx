import clsx from 'clsx';
import { useState } from 'react';
import { CARD, questionsOf } from './tints';
import { hourName, hoursOf } from '@/lib/insights';
import type { PointerEvent } from 'react';
import type { Entry } from '@/types/history';

// The hours named under the bars
const MARKS = [0, 6, 12, 18];

const BAR = 'w-full max-w-3 transition-colors ease-out';

interface HoursProps {
    entries: Entry[];
}

function Hours({ entries }: HoursProps) {
    const [picked, setPicked] = useState<number | null>(null);

    const hours = hoursOf(entries);
    const most = Math.max(...hours);
    const peak = hours.indexOf(most);
    const shown = picked ?? peak;
    const count = hours[shown];

    // The busiest hour
    const said = picked === null ? 'your busiest hour' : questionsOf(count);
    const share =
        picked === null
            ? `${most} of ${questionsOf(entries.length)} came in that hour`
            : `${Math.round((count / entries.length) * 100)}% of your questions`;

    // A mouse leaving the bars goes back to the busiest
    const leave = (event: PointerEvent) => {
        if (event.pointerType === 'mouse') setPicked(null);
    };

    return (
        <section className={CARD}>
            <h2 className="text-title text-bright">When you ask</h2>
            <div className="mt-1.5 flex items-baseline gap-1.5">
                <span className="text-headline text-bright tabular-nums">{hourName(shown)}</span>
                <span className="text-row text-dim">{said}</span>
            </div>
            <p className="mt-0.5 text-xs text-hush">{share}</p>
            <div
                role="img"
                aria-label={`Questions by hour of day; the busiest is ${hourName(peak)}, with ${most}`}
                onPointerLeave={leave}
                className="mt-4 flex h-14 items-end gap-0.5"
            >
                {hours.map((total, hour) => (
                    <div
                        key={hour}
                        onPointerEnter={(event) => event.pointerType === 'mouse' && setPicked(hour)}
                        className="flex h-full flex-1 items-end justify-center"
                    >
                        {total === 0 ? (
                            <div className={`${BAR} h-0.75 rounded-full bg-line`} />
                        ) : (
                            <div
                                className={clsx(
                                    BAR,
                                    'min-h-1.5 rounded-chip',
                                    hour === shown ? 'bg-soft' : 'bg-edge',
                                )}
                                style={{ height: `${(total / most) * 100}%` }}
                            />
                        )}
                    </div>
                ))}
            </div>
            <div className="mt-1.5 grid grid-cols-4 select-none" aria-hidden="true">
                {MARKS.map((hour) => (
                    <span key={hour} className="font-mono text-axis text-faint">
                        {hourName(hour)}
                    </span>
                ))}
            </div>
        </section>
    );
}

export default Hours;
