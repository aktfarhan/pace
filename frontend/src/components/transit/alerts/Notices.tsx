import KindFilter from './KindFilter';
import AlertGroup from './AlertGroup';
import { kindOf, wordsOf } from './feed';
import { useMemo, useState } from 'react';
import { CircleCheck } from 'lucide-react';
import Find from '@/components/layout/Find';
import type { Notice } from '@/types/transit';

// The two alert groups
const GROUPS = [
    { name: 'Disruptions', slowing: true, panel: 'border-amber/16 bg-amber/4' },
    { name: 'Notices', slowing: false, panel: 'border-seam bg-panel' },
];

interface NoticesProps {
    notices: Notice[];
    bare: boolean;
}

function Notices({ notices, bare }: NoticesProps) {
    const [asked, setAsked] = useState('');
    const [kind, setKind] = useState<string | null>(null);
    const typed = asked.trim();

    // Every word a notice carries
    const found = useMemo(() => {
        const words = typed.toLowerCase();
        if (words === '') return notices;

        return notices.filter((one) => wordsOf(one).includes(words));
    }, [notices, typed]);

    // A picked kind narrows the list
    const live = found.some((one) => kindOf(one.alert.effect).name === kind) ? kind : null;
    if (kind !== null && live === null) setKind(null);
    const shown =
        live === null ? found : found.filter((one) => kindOf(one.alert.effect).name === live);

    // Each group with its alerts
    const groups = GROUPS.map((group) => ({
        ...group,
        alerts: shown.filter((one) => one.alert.slowing === group.slowing),
    })).filter((group) => group.alerts.length > 0);

    if (notices.length === 0 && bare) return null;

    return (
        <section>
            <div className="flex flex-wrap items-baseline gap-2.5 px-1 pt-5 pb-3">
                <div aria-live="polite" className="flex items-baseline gap-2.5">
                    <h2 className="text-title text-bright">Alerts</h2>
                    <span className="text-title text-ghost tabular-nums">{shown.length}</span>
                </div>
                <span className="flex-1" />
                {notices.length > 0 && (
                    <Find asked={asked} search={setAsked} label="Search alerts" />
                )}
            </div>
            <KindFilter notices={found} kind={live} pick={setKind} />

            {notices.length === 0 && (
                <p className="flex items-center gap-2.5 rounded-tile border border-seam bg-panel px-4 py-3.5 text-row text-soft shadow-card">
                    <CircleCheck size={15} strokeWidth={2} className="text-good" />
                    Nothing reported on this line.
                </p>
            )}
            {notices.length > 0 && shown.length === 0 && (
                <p className="px-1 text-row text-faint">No alerts match “{typed}”.</p>
            )}
            {shown.length > 0 && (
                <div className="flex flex-col gap-2">
                    {groups.map(({ name, slowing, panel, alerts }) => (
                        <AlertGroup
                            key={name}
                            name={name}
                            notices={alerts}
                            panel={panel}
                            folds={!slowing}
                            searching={typed !== ''}
                        />
                    ))}
                </div>
            )}
        </section>
    );
}

export default Notices;
