import Tabs from './Tabs';
import Chart from './Chart';
import { useState } from 'react';
import { ageOf } from '@/lib/status';
import { useNow } from '@/hooks/useNow';
import { useTransit } from '@/hooks/useTransit';
import type { Tab } from './tints';

function Transit() {
    const [tab, setTab] = useState<Tab>('All');

    const now = useNow();
    const transit = useTransit();

    return (
        <div className="flex min-w-0 flex-col gap-4.5">
            <div className="flex items-end justify-between gap-6 pb-1">
                <span className="text-board text-bright">Transit</span>
                {transit !== null && transit.status.ok && (
                    <span className="flex shrink-0 items-center gap-2 rounded-full border border-edge bg-bubble px-3.25 py-1.75">
                        <span className="size-1.25 rounded-full bg-good shadow-glow" />
                        <span className="font-mono text-stamp text-hush uppercase">
                            Live · {ageOf(transit.status.retrieved_at, now)}
                        </span>
                    </span>
                )}
            </div>
            <Tabs tab={tab} select={setTab} />
            {transit !== null && (
                <Chart series={transit.series} read={Date.parse(transit.status.retrieved_at)} />
            )}
        </div>
    );
}

export default Transit;
