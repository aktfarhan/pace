import Drift from '@/components/transit/lines/Drift';
import { memo } from 'react';
import Picker from '@/components/transit/lines/Picker';
import Typical from './Typical';
import type { Branching } from '@/types/transit';
import type { Figure, Typically } from './figures';

const BOX =
    'flex w-fit items-center gap-1.5 rounded-chip border border-seam px-2 py-1 font-mono text-state uppercase';

interface FocusProps {
    figure: Figure;
    typically: Typically | null;
    branching: Branching | null;
}

function Focus({ figure, typically, branching }: FocusProps) {
    const { line, share, drift } = figure;

    return (
        <div className="flex flex-wrap items-center gap-1.5">
            {branching !== null && (
                <div className="hidden @max-md/card:block">
                    <Picker branching={branching} align="left" />
                </div>
            )}
            <span className={BOX}>
                <span className={`${line.fill} h-0.5 w-3.5 shrink-0 rounded-full`} />
                <span className="text-ghost">today</span>
                {share === null ? (
                    <span className="text-ghost">
                        <span aria-hidden="true">—</span>
                        <span className="sr-only">no readings</span>
                    </span>
                ) : (
                    <span className="text-soft tabular-nums">{share}%</span>
                )}
                <Drift points={drift} />
            </span>

            {typically !== null && (
                <span className={BOX}>
                    <svg viewBox="0 0 14 2" className="w-3.5 shrink-0" aria-hidden="true">
                        <Typical path="M1 1H13" stroke={line.stroke} />
                    </svg>
                    <span className="text-ghost">typically</span>
                    <span className="text-soft tabular-nums">{typically.share}%</span>
                    <span className="text-ghost tabular-nums">{typically.days} days</span>
                </span>
            )}
        </div>
    );
}

export default memo(Focus);
