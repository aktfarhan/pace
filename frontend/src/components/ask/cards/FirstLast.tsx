import clsx from 'clsx';
import { useNow } from '@/hooks/useNow';
import { LINE_TEXT, lineOf, clockParts } from '@/lib/trip';
import type { EdgeCard } from '@/types/answer';

interface FirstLastProps {
    card: EdgeCard;
}

function FirstLast({ card }: FirstLastProps) {
    const now = useNow();
    const moment = now === 0 ? Date.now() : now;

    const line = lineOf(card.route_id);
    const title = card.edge === 'first' ? 'First' : 'Last';
    const last = card.directions.length - 1;

    return (
        <div className="rounded-card border border-edge bg-field px-7 py-3 text-cream">
            <div className="flex items-end justify-between border-b border-seam pt-3.5 pb-3.25">
                <div className="text-title text-bright">
                    {title}{' '}
                    <span className={line === null ? undefined : LINE_TEXT[line]}>
                        {card.label}
                    </span>{' '}
                    from {card.station}
                </div>
                <span className="flex items-center gap-1.75 pb-0.5">
                    <span className="size-1.5 rounded-full border border-dim" />
                    <span className="font-mono text-timetable text-ghost uppercase">
                        {card.day} timetable
                    </span>
                </span>
            </div>

            <div className="grid grid-cols-3">
                {card.directions.map((direction, index) => {
                    const { time, meridiem } = clockParts(direction.time);
                    const passed = Date.parse(direction.time) < moment;
                    return (
                        <div
                            key={index}
                            className={clsx(
                                'pt-4 pb-4.5',
                                index > 0 && 'border-l border-seam pl-6',
                                index < last && 'pr-6',
                            )}
                        >
                            <div className="flex items-baseline justify-between">
                                <span className="font-mono text-toward text-ghost uppercase">
                                    Toward
                                </span>
                                {passed && (
                                    <span className="font-mono text-passed text-amber uppercase">
                                        Passed
                                    </span>
                                )}
                            </div>
                            <div className="mt-1.25 text-row font-medium text-cream">
                                {direction.destination}
                            </div>
                            <div className="mt-2.25 whitespace-nowrap">
                                <span className="font-mono text-board text-accent tabular-nums">
                                    {time}
                                </span>
                                <span className="ml-1.5 text-row font-semibold text-soft">
                                    {meridiem}
                                </span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

export default FirstLast;
