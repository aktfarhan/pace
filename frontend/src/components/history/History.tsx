import Row from './Row';
import { useState } from 'react';
import { clearHistory, daysOf, readHistory } from '@/lib/history';
import SectionHeading from '@/components/layout/sidebar/SectionHeading';

const EMPTY = 'No questions asked yet.';

const CLEAR =
    'shrink-0 cursor-pointer font-mono text-tag text-faint uppercase transition-colors hover:text-cream';

function History() {
    const [entries, setEntries] = useState(readHistory);

    const empty = entries.length === 0;
    const refused = entries.filter((entry) => entry.refused).length;
    const answered = entries.length - refused;

    const kept = empty
        ? EMPTY
        : `${answered} answered · ${refused} refused · stored on this device`;

    const days = daysOf(entries);

    const clear = () => {
        clearHistory();
        setEntries([]);
    };

    return (
        <div className="flex min-w-0 flex-col gap-3.5">
            <div className="flex items-center justify-between gap-4">
                <div className="min-w-0">
                    <div className="text-board text-bright">History</div>
                    <div className="mt-0.5 text-row text-faint">{kept}</div>
                </div>
                {!empty && (
                    <button type="button" onClick={clear} className={CLEAR}>
                        Clear all
                    </button>
                )}
            </div>

            {days.map((day) => (
                <div key={day.heading} className="min-w-0">
                    <SectionHeading label={day.heading} />
                    <div className="divide-y divide-seam overflow-hidden rounded-tile border border-seam bg-panel">
                        {day.entries.map((entry) => (
                            <Row key={entry.at} entry={entry} />
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}

export default History;
