import clsx from 'clsx';
import Legend from './Legend';
import { DROP } from './plot';
import { CARD } from './tints';
import { rulesOf } from './frame';
import { TICK } from '@/components/layout/tints';
import { useChartBox } from '@/hooks/useChartBox';
import { useEmphasis } from '@/hooks/useEmphasis';
import TryAgain from '@/components/layout/TryAgain';
import type { Drawn } from '@/lib/lines';

interface WaitingProps {
    lines: readonly Drawn[];
    note: string;
    retry: (() => void) | null;
}

function Waiting({ lines, note, retry }: WaitingProps) {
    const { cardRef, box, height } = useChartBox();
    const { picked, strengthOf, light, toggle } = useEmphasis(
        lines.map((line) => line.id).join(),
        null,
    );

    // The legend's own chips
    const figures = lines.map((line) => ({ line, share: null, drift: null }));

    // The gridlines
    const rules = rulesOf(box).map(({ share, y }) => ({
        share,
        floor: share === 0,
        top: share === 0 ? y + DROP : y,
    }));

    return (
        <div ref={cardRef} className={CARD}>
            <div className="flex min-h-6.75 items-center">
                <h2 className="text-title text-bright">Late arrivals</h2>
            </div>
            <Legend
                figures={figures}
                picked={picked}
                strengthOf={strengthOf}
                light={light}
                toggle={toggle}
            />
            <div className="relative" style={{ height }}>
                {rules.map(({ share, floor, top }) => (
                    <span
                        key={share}
                        className={clsx('absolute border-t', floor ? 'border-edge' : 'border-rule')}
                        style={{ top, left: box.left, width: box.right - box.left }}
                    />
                ))}
                <div
                    role="status"
                    className="absolute inset-0 flex flex-col items-center justify-center gap-3"
                >
                    <span
                        key={note}
                        className={clsx(
                            'flex items-center gap-2 font-mono text-chip text-hush uppercase',
                            TICK,
                        )}
                    >
                        {retry === null ? (
                            <span className="size-1.25 shrink-0 animate-blink rounded-full bg-accent" />
                        ) : (
                            <span className="size-1.25 shrink-0 rounded-full bg-red" />
                        )}
                        {note}
                    </span>
                    {retry !== null && <TryAgain retry={retry} />}
                </div>
            </div>
        </div>
    );
}

export default Waiting;
