import clsx from 'clsx';
import Bar from './Bar';
import Guides from './Guides';
import type { PointerEvent } from 'react';
import type { Tally } from '@/lib/insights';

const LABEL =
    'flex min-w-0 flex-1 justify-center font-mono text-axis whitespace-nowrap transition-colors';

interface BarsProps {
    bars: Tally[];
    dense: boolean;
    picked: number | null;
    pick: (index: number | null) => void;
    jump: (key: string) => void;
}

function Bars({ bars, dense, picked, pick, jump }: BarsProps) {
    const totals = bars.map((bar) => bar.total);
    const most = Math.max(1, ...totals);
    const average = dense ? null : totals.reduce((sum, total) => sum + total, 0) / bars.length;
    const gap = dense ? 'gap-0.5' : 'gap-1.5';

    // A mouse leaving the chart lets go of its bar
    const leave = (event: PointerEvent) => {
        if (event.pointerType === 'mouse') pick(null);
    };

    // The picked bar's label is highlighted
    const lit = (index: number) => picked === index || (picked === null && bars[index].current);

    return (
        <div
            role="group"
            aria-label={dense ? 'Questions each hour' : 'Questions each day'}
            onPointerLeave={leave}
            className="mt-4 select-none"
        >
            <div className={clsx('relative flex h-24 items-end pr-7', gap)}>
                {bars.map((bar, index) => (
                    <Bar
                        key={bar.key}
                        bar={bar}
                        most={most}
                        delay={(index * 120) / bars.length}
                        faded={picked !== null && picked !== index}
                        pick={() => pick(index)}
                        unpick={() => pick(null)}
                        jump={() => jump(bar.key)}
                    />
                ))}
                <Guides most={most} average={average} />
            </div>
            <div className={clsx('mt-1.5 flex pr-7', gap)} aria-hidden="true">
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
