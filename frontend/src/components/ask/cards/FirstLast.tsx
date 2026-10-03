import { tintOf } from '@/lib/lines';
import { useNow } from '@/hooks/useNow';
import { clockParts } from '@/lib/trip';
import { SURFACE } from '@/components/ask/tints';
import type { EdgeCard } from '@/types/answer';

// Each column's rule sits mid-gap
const COLUMN =
    'relative pt-4 pb-4.5 before:absolute before:inset-y-0 before:-left-6 before:w-px before:bg-seam';

interface FirstLastProps {
    card: EdgeCard;
}

function FirstLast({ card }: FirstLastProps) {
    const now = useNow();

    const tint = tintOf(card.route_id);
    const title = card.edge === 'first' ? 'First' : 'Last';

    return (
        <div className={`${SURFACE} py-3`}>
            <div className="flex flex-wrap items-end justify-between gap-x-4 gap-y-1.5 border-b border-seam pt-3.5 pb-3.25">
                <div className="text-title text-bright">
                    {title}{' '}
                    <span className={tint === null ? undefined : tint.text}>{card.label}</span> from{' '}
                    {card.station}
                </div>
                <span className="flex shrink-0 items-center gap-1.75 pb-0.5 whitespace-nowrap">
                    <span className="size-1.5 rounded-full border border-dim" />
                    <span className="font-mono text-timetable text-ghost uppercase">
                        {card.day} timetable
                    </span>
                </span>
            </div>

            <div className="grid grid-cols-directions gap-x-12 overflow-hidden">
                {card.directions.map((direction, index) => {
                    const { time, meridiem } = clockParts(direction.time);
                    const passed = Date.parse(direction.time) < now;
                    return (
                        <div key={index} className={COLUMN}>
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
