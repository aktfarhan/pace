import Tabs from './Tabs';
import Chart from './Chart';
import Stamp from './Stamp';
import Waiting from './Waiting';
import { LINES } from '@/lib/lines';
import { useMemo, useState } from 'react';
import { useTransit } from '@/hooks/useTransit';
import type { Tab } from './tints';

function Transit() {
    const [tab, setTab] = useState<Tab>('All');

    const { transit, failed, retry } = useTransit();

    // The All tab draws every line, any other draws its own
    const lines = useMemo(() => {
        const focused = LINES.find((line) => line.label === tab);
        return focused === undefined ? LINES : [focused];
    }, [tab]);

    return (
        <div className="flex min-w-0 flex-col gap-4.5">
            <div className="flex items-end justify-between gap-6 pb-1">
                <span className="text-board text-bright">Transit</span>
                {transit !== null && transit.status.ok && (
                    <Stamp retrievedAt={transit.status.retrieved_at} />
                )}
            </div>
            <Tabs tab={tab} select={setTab} />
            {transit === null && (
                <Waiting
                    note={failed ? 'Readings could not be reached' : 'Reading the day'}
                    retry={failed ? retry : null}
                />
            )}
            {transit !== null && (
                <Chart
                    lines={lines}
                    series={transit.series}
                    read={Date.parse(transit.status.retrieved_at)}
                    late={transit.late_minutes}
                    rolling={transit.rolling_minutes}
                />
            )}
        </div>
    );
}

export default Transit;
