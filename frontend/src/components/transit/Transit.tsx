import Tabs from './Tabs';
import Cards from './Cards';
import Chart from './Chart';
import Stamp from './Stamp';
import Notices from './Notices';
import Waiting from './Waiting';
import { noticesOf } from './feed';
import { troubleOf } from './standing';
import { useMemo, useState } from 'react';
import { useTransit } from '@/hooks/useTransit';
import { useStandings } from '@/hooks/useStandings';
import { LINES, LINE_BY_ID, branchLook } from '@/lib/lines';
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
            <div className="flex items-center justify-between gap-4 pb-1">
                <h1 className="text-board text-bright">Transit</h1>
                {transit !== null && <Stamp status={transit.status} refresh={retry} />}
            </div>
            <Tabs tab={tab} select={choose} troubled={troubleOf(transit)} />
            <div className="-mx-2 flex min-h-0 flex-1 scroll-edges flex-col gap-4.5 overflow-y-auto overscroll-contain px-2 pb-3">
                {transit === null && (
                    <Waiting
                        lines={lines}
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
                <Cards
                    name="Right now"
                    standing={standing}
                    pick={(id) => choose(LINE_BY_ID[id].label)}
                />
                <Cards
                    name="Branches"
                    standing={running}
                    pick={(id) => setBranch(id === branch ? null : id)}
                    picked={branch}
                />
                <Notices
                    key={tab}
                    notices={notices}
                    bare={focused === undefined || !transit?.status.ok}
                />
            </div>
        </div>
    );
}

export default Transit;
