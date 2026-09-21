import Find from './Find';
import Alert from './Alert';
import { wordsOf } from './feed';
import { useMemo, useState } from 'react';
import type { Notice } from '@/types/transit';

interface NoticesProps {
    notices: Notice[];
    bare: boolean;
}

function Notices({ notices, bare }: NoticesProps) {
    const [asked, setAsked] = useState('');

    // Every word a notice carries
    const found = useMemo(() => {
        const words = asked.trim().toLowerCase();
        if (words === '') return notices;

        return notices.filter((one) => wordsOf(one).includes(words));
    }, [notices, asked]);

    if (notices.length === 0 && bare) return null;

    const empty = notices.length === 0 ? 'Nothing reported on this line.' : 'No results.';

    return (
        <section>
            <div className="flex flex-wrap items-baseline gap-2.5 px-0.5 pt-5 pb-3">
                <span aria-live="polite" className="flex items-baseline gap-2.5">
                    <span className="text-headline whitespace-nowrap text-bright">Alerts</span>
                    <span className="text-title text-ghost tabular-nums">{found.length}</span>
                </span>
                <span className="flex-1" />
                {notices.length > 0 && <Find asked={asked} ask={setAsked} />}
            </div>
            {found.length === 0 ? (
                <p className="text-branch text-ghost">{empty}</p>
            ) : (
                <div className="grid gap-2 xl:grid-cols-2">
                    {found.map(({ lines, alert }) => (
                        <Alert key={alert.alert_id} lines={lines} alert={alert} />
                    ))}
                </div>
            )}
        </section>
    );
}

export default Notices;
