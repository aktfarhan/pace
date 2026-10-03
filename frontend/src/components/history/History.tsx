import Row from './Row';
import Head from './Head';
import { useState } from 'react';
import { clearHistory, daysOf, readHistory } from '@/lib/history';
import SectionHeading from '@/components/layout/sidebar/SectionHeading';

interface HistoryProps {
    ask: (query: string) => void;
}

function History({ ask }: HistoryProps) {
    const [entries, setEntries] = useState(readHistory);
    const [asked, setAsked] = useState('');

    // Filter by search
    const words = asked.trim().toLowerCase();
    const days = daysOf(entries.filter((entry) => entry.query.toLowerCase().includes(words)));

    const clear = () => {
        clearHistory();
        setEntries([]);
    };

    return (
        <div className="flex min-w-0 flex-col gap-3.5">
            <Head entries={entries} asked={asked} search={setAsked} clear={clear} />

            {entries.length > 0 && days.length === 0 && (
                <p className="px-0.5 text-row text-faint">No questions match “{asked.trim()}”.</p>
            )}

            {days.map((day) => (
                <div key={day.heading} className="min-w-0">
                    <SectionHeading label={day.heading} />
                    <div className="divide-y divide-seam overflow-hidden rounded-tile border border-seam bg-panel">
                        {day.entries.map((entry) => (
                            <Row key={entry.at} entry={entry} ask={ask} />
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}

export default History;
