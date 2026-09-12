import clsx from 'clsx';
import { tintOf } from '@/lib/lines';
import { clock, minutesBetween } from '@/lib/trip';
import { Bus, Clock, SportShoe, TrainFront } from 'lucide-react';
import type { Wait, WalkLeg, RideLeg } from '@/types/answer';

interface LegRowProps {
    leg: WalkLeg | RideLeg | Wait;
    bright: boolean;
}

function LegRow({ leg, bright }: LegRowProps) {
    const tint = leg.kind === 'ride' ? tintOf(leg.route_id) : null;

    // The icon for this leg
    let Icon = TrainFront;
    if (leg.kind === 'wait') {
        Icon = Clock;
    } else if (leg.kind !== 'ride') {
        Icon = SportShoe;
    } else if (tint?.id === 'Bus') {
        Icon = Bus;
    }

    // Rendering each leg
    let label;
    if (leg.kind === 'wait') {
        label = `Wait at ${leg.station}`;
    } else if (leg.kind !== 'ride') {
        label = leg.transfer ? `Transfer at ${leg.destination}` : `Walk to ${leg.destination}`;
    } else {
        label = (
            <>
                <span className={clsx('font-semibold', tint === null ? 'text-cream' : tint.text)}>
                    {leg.label}
                </span>
                <span className="font-normal text-dim"> to </span>
                {leg.destination}
            </>
        );
    }

    return (
        <div className="flex items-center gap-3 border-t border-seam px-0.5 py-2.75 first:border-t-0">
            <span
                className={clsx(
                    'w-11 shrink-0 font-mono text-clock tabular-nums',
                    bright ? 'font-strong text-accent' : 'font-medium text-hush',
                )}
            >
                {clock(leg.depart)}
            </span>
            <span
                className={clsx(
                    'grid size-7 shrink-0 place-items-center rounded-mark border',
                    tint === null ? 'border-line bg-bubble text-muted' : tint.tile,
                )}
            >
                <Icon size={14} strokeWidth={1.9} aria-hidden="true" />
            </span>
            <span className="min-w-0 flex-1 truncate text-row font-medium text-cream">{label}</span>
            <span className="w-19 shrink-0 text-right font-mono text-clock font-semibold text-cream tabular-nums">
                {minutesBetween(leg.depart, leg.arrive)} MIN
            </span>
        </div>
    );
}

export default LegRow;
