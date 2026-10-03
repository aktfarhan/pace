import clsx from 'clsx';
import Bar from './Bar';
import type { PointerEvent } from 'react';
import type { Tally } from '@/lib/insights';

const LABEL =
    'flex min-w-0 flex-1 justify-center font-mono text-axis whitespace-nowrap transition-colors';

interface BarsProps {
    bars: Tally[];
    picked: number | null;
    pick: (index: number | null) => void;
    jump: () => void;
}

function Bars({ bars, picked, pick, jump }: BarsProps) {
    const most = Math.max(...bars.map((bar) => bar.total));

    // A mouse leaving the chart lets go of its hour
    const leave = (event: PointerEvent) => {
        if (event.pointerType === 'mouse') pick(null);
    };

    // The picked hour's label is highlighted
    const lit = (index: number) => picked === index || (picked === null && bars[index].current);

    return (
        <div
            role="group"
            aria-label="Questions each hour"
            onPointerLeave={leave}
            className="mt-4 select-none"
        >
            <div className="flex h-24 items-end gap-0.5">
                {bars.map((bar, index) => (
                    <Bar
                        key={bar.key}
                        bar={bar}
                        most={most}
                        delay={(index * 120) / bars.length}
                        faded={picked !== null && picked !== index}
                        pick={() => pick(index)}
                        unpick={() => pick(null)}
                        jump={jump}
                    />
                ))}
            </div>
            <div className="mt-1.5 flex gap-0.5" aria-hidden="true">
                {bars.map((bar, index) => (
                    <span
                        key={bar.key}
                        className={clsx(LABEL, lit(index) ? 'text-soft' : 'text-faint')}
                    >
                        {bar.label}
                    </span>
                ))}
            </div>
        </div>
    );
}

export default Bars;
