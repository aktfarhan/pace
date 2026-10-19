import clsx from 'clsx';
import Drift from './Drift';
import Trend from './Trend';
import { percentOf } from '@/components/transit/chart/figures';
import { useWidth } from '@/hooks/useWidth';
import { useTicks } from '@/hooks/useTicks';
import { columnsFor, whenOf } from './standing';
import { TICK } from '@/components/layout/tints';
import SectionHeading from '@/components/layout/SectionHeading';
import type { Standing } from '@/types/transit';

interface CardsProps {
    name: string;
    standing: Standing[];
    pick: (id: string) => void;
    picked?: string | null;
}

function Cards({ name, standing, pick, picked }: CardsProps) {
    const [gridRef, width] = useWidth<HTMLDivElement>();
    const { ticking, settle } = useTicks(standing.map((one) => [one.id, one.share]));

    // Columns follow the room
    const count = standing.length;
    const columns = columnsFor(count, width);

    if (count === 0) return null;

    return (
        <section>
            <SectionHeading label={name} />
            <div
                ref={gridRef}
                className="grid gap-3"
                style={{
                    gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
                }}
            >
                {standing.map((one) => (
                    <button
                        key={one.id}
                        type="button"
                        aria-pressed={picked === undefined ? undefined : one.id === picked}
                        onClick={() => pick(one.id)}
                        className={clsx(
                            '@container flex cursor-pointer flex-col gap-2 rounded-tile border px-3.5 py-3 text-left shadow-card transition ease-out hover:border-edge hover:bg-field active:scale-98',
                            one.id === picked ? 'border-edge bg-field' : 'border-seam bg-panel',
                        )}
                    >
                        <span className="flex items-center gap-2.5">
                            <span
                                className={clsx(
                                    'shrink-0 rounded-chip border px-1.75 py-0.75 font-mono text-chip uppercase',
                                    one.chip,
                                )}
                            >
                                {one.code}
                            </span>
                            <span className="line-clamp-2 min-w-0 flex-1 text-branch leading-tight text-bright">
                                {one.name}
                            </span>
                        </span>
                        <span className="flex items-baseline gap-x-1.5 overflow-hidden">
                            <span
                                key={one.share ?? 'none'}
                                onTransitionEnd={() => settle(one.id, one.share)}
                                className={clsx(
                                    'text-headline tabular-nums',
                                    ticking(one.id, one.share) && TICK,
                                    one.share === null ? 'text-ghost' : one.text,
                                )}
                            >
                                {percentOf(one.share)}
                            </span>
                            <span className="font-mono text-label text-faint uppercase">late</span>
                            <Drift points={one.drift} />
                            <span
                                className={`ml-auto hidden max-w-11 min-w-8 flex-1 self-center opacity-80 @trend:block ${one.text}`}
                            >
                                <Trend points={one.trend} />
                            </span>
                        </span>
                        <span className="font-mono text-label text-faint uppercase tabular-nums">
                            {whenOf(one)}
                        </span>
                    </button>
                ))}
            </div>
        </section>
    );
}

export default Cards;
