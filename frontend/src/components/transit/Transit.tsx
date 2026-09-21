import Tabs from './Tabs';
import Cards from './Cards';
import Chart from './Chart';
import Stamp from './Stamp';
import Notices from './Notices';
import Waiting from './Waiting';
import { noticesOf } from './feed';
import { LINES } from '@/lib/lines';
import { SHORT_CODE } from './tints';
import { useMemo, useState } from 'react';
import { useTransit } from '@/hooks/useTransit';
import { feedOf, lookOf, nameOf } from './standing';
import type { Tab } from './tints';
import type { Branching } from '@/types/transit';

function Transit() {
    const [tab, setTab] = useState<Tab>('All');
    const [branch, setBranch] = useState<string | null>(null);
    const { transit, failed, retry } = useTransit();

    const focused = LINES.find((line) => line.label === tab);

    // A new tab drops the branch
    const choose = (next: Tab) => {
        setTab(next);
        setBranch(null);
    };

    // No picker unless the line has branches
    const branching: Branching | null =
        focused === undefined || transit === null || transit.branches[focused.id] === undefined
            ? null
            : { line: focused, branches: transit.branches[focused.id], branch, pick: setBranch };

    // Which lines the chart draws
    const lines = useMemo(() => {
        if (focused === undefined) return LINES;
        if (branch === null) return [focused];

        // The branch under its line's colours
        const name = transit?.branches[focused.id]?.find((one) => one.id === branch)?.name;
        if (name === undefined) return [focused];

        const code = name.length > SHORT_CODE ? focused.code : name;
        return [{ ...focused, id: branch, label: `${focused.label} ${name}`, code }];
    }, [focused, branch, transit]);

    // Where every line stands right now
    const standing = useMemo(() => {
        if (transit === null || focused !== undefined) return [];

        return LINES.map((line) => ({
            ...feedOf(transit, line.id),
            ...lookOf(line),
            name: nameOf(transit, line),
        }));
    }, [transit, focused]);

    // Where each branch of a selected line stands
    const running = useMemo(() => {
        if (transit === null || focused === undefined) return [];

        return (transit.branches[focused.id] ?? []).map(({ id, name }) => ({
            ...feedOf(transit, id),
            ...lookOf(focused),
            name,
        }));
    }, [transit, focused]);

    // Everything the feed is saying about notices
    const notices = useMemo(
        () => (transit === null ? [] : noticesOf(transit, focused)),
        [transit, focused],
    );

    return (
        <div className="flex min-w-0 flex-col gap-4.5">
            <div className="flex items-end justify-between gap-6 pb-1">
                <span className="text-board text-bright">Transit</span>
                {transit !== null && transit.status.ok && (
                    <Stamp retrievedAt={transit.status.retrieved_at} />
                )}
            </div>
            <Tabs tab={tab} select={choose} />
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
                    typical={transit.typical}
                    read={Date.parse(transit.status.retrieved_at)}
                    late={transit.late_minutes}
                    rolling={transit.rolling_minutes}
                    branching={branching}
                />
            )}
            <Cards name="Right now" standing={standing} />
            <Cards name="Branches" standing={running} />
            <Notices key={tab} notices={notices} bare={focused === undefined} />
        </div>
    );
}

export default Transit;
