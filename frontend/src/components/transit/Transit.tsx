import Tabs from './Tabs';
import Cards from './Cards';
import Chart from './Chart';
import Stamp from './Stamp';
import Notices from './Notices';
import Waiting from './Waiting';
import { noticesOf } from './feed';
import { useMemo, useState } from 'react';
import { useTransit } from '@/hooks/useTransit';
import { LINES, branchLook } from '@/lib/lines';
import { useStandings } from '@/hooks/useStandings';
import type { Tab } from './tints';
import type { Branching } from '@/types/transit';

interface TransitProps {
    tab: Tab;
    choose: (tab: Tab) => void;
}

function Transit({ tab, choose }: TransitProps) {
    const [picked, setPicked] = useState<{ tab: Tab; branch: string | null }>({
        tab,
        branch: null,
    });
    const { transit, failed, retry } = useTransit();

    const focused = LINES.find((line) => line.label === tab);

    // A new tab clears the branch
    if (picked.tab !== tab) setPicked({ tab, branch: null });
    const branch = picked.branch;
    const setBranch = (next: string | null) => setPicked({ tab, branch: next });

    const { standing, running, shares } = useStandings(transit, focused);

    // No picker unless the line has branches
    const branches = focused === undefined ? undefined : transit?.branches[focused.id];
    const branching: Branching | null =
        focused === undefined || branches === undefined
            ? null
            : { line: focused, branches, branch, pick: setBranch, shares };

    // Which lines the chart draws
    const lines = useMemo(() => {
        if (focused === undefined) return LINES;
        if (branch === null) return [focused];

        // The branch under its line's colours
        const name = branches?.find((one) => one.id === branch)?.name;
        if (name === undefined) return [focused];

        const code = branchLook(name).code ?? focused.code;
        return [{ ...focused, id: branch, label: `${focused.label} ${name}`, code }];
    }, [focused, branch, branches]);

    const notices = useMemo(
        () => (transit === null ? [] : noticesOf(transit, focused)),
        [transit, focused],
    );

    return (
        <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-4.5">
            <div className="flex items-end justify-between gap-6 pb-1">
                <span className="text-board text-bright">Transit</span>
                {transit !== null && transit.status.ok && (
                    <Stamp retrievedAt={transit.status.retrieved_at} />
                )}
            </div>
            <Tabs tab={tab} select={choose} />
            <div className="flex min-h-0 flex-1 flex-col gap-4.5 overflow-y-auto">
                {transit === null && (
                    <Waiting
                        note={failed ? "Couldn't reach today's readings" : 'Reading the day'}
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
                        resumes={transit.resumes}
                    />
                )}
                <Cards name="Right now" standing={standing} />
                <Cards name="Branches" standing={running} />
                <Notices key={tab} notices={notices} bare={focused === undefined} />
            </div>
        </div>
    );
}

export default Transit;
