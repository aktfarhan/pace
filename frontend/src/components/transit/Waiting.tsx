import clsx from 'clsx';
import { DROP } from './plot';
import { rulesOf } from './frame';
import { CARD, CHIP } from './tints';
import { TICK } from '@/components/layout/tints';
import { useChartBox } from '@/hooks/useChartBox';
import TryAgain from '@/components/layout/TryAgain';

interface WaitingProps {
    note: string;
    retry: (() => void) | null;
}

function Waiting({ note, retry }: WaitingProps) {
    const { cardRef, box, height } = useChartBox();

    // The gridlines
    const rules = rulesOf(box).map(({ share, y }) => ({
        share,
        floor: share === 0,
        top: share === 0 ? y + DROP : y,
    }));

    return (
        <div ref={cardRef} className={CARD}>
            <span className={`${CHIP} w-fit text-hush`}>Arrivals behind schedule</span>
            <div className="h-6" />
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
