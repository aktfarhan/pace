import clsx from 'clsx';
import Drift from './Drift';
import { columnsFor, whenOf } from './standing';
import { useLayoutEffect, useRef, useState } from 'react';
import SectionHeading from '@/components/layout/sidebar/SectionHeading';
import type { Standing } from '@/types/transit';

interface CardsProps {
    name: string;
    standing: Standing[];
}

function Cards({ name, standing }: CardsProps) {
    const gridRef = useRef<HTMLDivElement>(null);
    const [width, setWidth] = useState(0);

    // The columns depend on the room the grid has
    const shown = standing.length > 0;
    useLayoutEffect(() => {
        const grid = gridRef.current;
        if (grid === null) return;

        setWidth(grid.getBoundingClientRect().width);
        const watch = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
        watch.observe(grid);
        return () => watch.disconnect();
    }, [shown]);

    if (!shown) return null;

    return (
        <section>
            <SectionHeading label={name} />
            <div
                ref={gridRef}
                className="grid gap-3"
                style={{
                    gridTemplateColumns: `repeat(${columnsFor(standing.length, width)}, minmax(0, 1fr))`,
                }}
            >
                {standing.map((one) => (
                    <div
                        key={one.id}
                        className="flex flex-col gap-2 rounded-tile border border-seam bg-panel px-3.5 py-3"
                    >
                        <div className="flex items-center gap-2.5">
                            <span
                                className={clsx(
                                    'shrink-0 rounded-chip border px-1.75 py-0.75 font-mono text-chip uppercase',
                                    one.chip,
                                )}
                            >
                                {one.code}
                            </span>
                            <span className="min-w-0 flex-1 truncate text-branch leading-tight text-bright">
                                {one.name}
                            </span>
                        </div>
                        <div className="flex items-baseline gap-x-1.5 overflow-hidden">
                            <span
                                className={clsx(
                                    'text-headline tabular-nums',
                                    one.share === null ? 'text-ghost' : one.text,
                                )}
                            >
                                {one.share === null ? '—' : `${one.share}%`}
                            </span>
                            <span className="font-mono text-label text-faint uppercase">late</span>
                            <Drift points={one.drift} />
                        </div>
                        <span className="font-mono text-label text-faint uppercase tabular-nums">
                            {whenOf(one)}
                        </span>
                    </div>
                ))}
            </div>
        </section>
    );
}

export default Cards;
