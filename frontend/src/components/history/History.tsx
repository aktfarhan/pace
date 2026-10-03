import Row from './Row';
import Head from './Head';
import Week from './Week';
import { useState } from 'react';
import { still } from '@/lib/device';
import { flushSync } from 'react-dom';
import { dayKey } from '@/lib/insights';
import Empty from '@/components/layout/Empty';
import { Clock, MessageSquare } from 'lucide-react';
import SectionHeading from '@/components/layout/SectionHeading';
import { clearHistory, daysOf, readHistory } from '@/lib/history';

interface HistoryProps {
    ask: (query: string) => void;
    start: () => void;
}

function History({ ask, start }: HistoryProps) {
    const [entries, setEntries] = useState(readHistory);
    const [asked, setAsked] = useState('');

    // Filter by search
    const words = asked.trim().toLowerCase();
    const days = daysOf(entries.filter((entry) => entry.query.toLowerCase().includes(words)));

    const clear = () => {
        clearHistory();
        setEntries([]);
    };

    // A bar picked on the chart scrolls its day into view
    const jump = (key: string) => {
        flushSync(() => setAsked(''));
        document.getElementById(key)?.scrollIntoView({ behavior: still() ? 'auto' : 'smooth' });
    };

    return (
        <div className="@container flex min-w-0 flex-col gap-3.5">
            <Head entries={entries} asked={asked} search={setAsked} clear={clear} />

            {entries.length === 0 && (
                <Empty
                    Icon={Clock}
                    title="Questions you ask show up here"
                    note="Kept on this device only. Ask again by tapping on the question."
                    action="Ask a question"
                    ActionIcon={MessageSquare}
                    run={start}
                />
            )}

            {entries.length > 0 && (
                <div className="flex flex-col gap-6 @4xl:flex-row @4xl:items-start">
                    <div className="flex min-w-0 flex-1 flex-col gap-3.5">
                        {days.length === 0 && (
                            <p className="px-0.5 text-row text-faint">
                                No questions match “{asked.trim()}”.
                            </p>
                        )}

                        {days.map((day) => (
                            <div
                                key={day.heading}
                                id={dayKey(day.entries[0].at)}
                                className="min-w-0 scroll-mt-2"
                            >
                                <SectionHeading label={day.heading} count={day.entries.length} />
                                <div className="divide-y divide-seam overflow-hidden rounded-tile border border-seam bg-panel">
                                    {day.entries.map((entry) => (
                                        <Row key={entry.at} entry={entry} ask={ask} />
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                    <aside className="@4xl:sticky @4xl:top-0 @4xl:mt-9 @4xl:w-76 @4xl:shrink-0">
                        <Week entries={entries} jump={jump} />
                    </aside>
                </div>
            )}
        </div>
    );
}

export default History;
