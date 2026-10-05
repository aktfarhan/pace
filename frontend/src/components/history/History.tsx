import Row from './Row';
import Head from './Head';
import Filtered from './Filtered';
import Insights from './Insights';
import { still } from '@/lib/device';
import { flushSync } from 'react-dom';
import { useRef, useState } from 'react';
import Empty from '@/components/layout/Empty';
import { dayKey, entryKind } from '@/lib/insights';
import { Clock, MessageSquare } from 'lucide-react';
import SectionHeading from '@/components/layout/SectionHeading';
import { clearHistory, daysOf, readHistory } from '@/lib/history';
import type { Kind } from '@/lib/insights';

interface HistoryProps {
    ask: (query: string) => void;
    start: () => void;
}

function History({ ask, start }: HistoryProps) {
    const [entries, setEntries] = useState(readHistory);
    const [asked, setAsked] = useState('');
    const [kind, setKind] = useState<Kind | null>(null);
    const titleRef = useRef<HTMLHeadingElement>(null);

    // Filter by kind and search
    const words = asked.trim().toLowerCase();
    const days = daysOf(
        entries.filter(
            (entry) =>
                (kind === null || entryKind(entry) === kind) &&
                entry.query.toLowerCase().includes(words),
        ),
    );

    const clear = () => {
        clearHistory();
        setEntries([]);
    };

    // A bar picked on the chart scrolls its day into view
    const jump = (key: string) => {
        flushSync(() => {
            setKind(null);
            setAsked('');
        });
        document.getElementById(key)?.scrollIntoView({ behavior: still() ? 'auto' : 'smooth' });
    };

    // A picked kind filters the list
    const filter = (next: Kind | null) => {
        setKind(next);
        titleRef.current?.scrollIntoView({
            block: 'nearest',
            behavior: still() ? 'auto' : 'smooth',
        });
    };

    const unfilter = () => {
        setKind(null);
        titleRef.current?.focus({ preventScroll: true });
    };

    return (
        <div className="@container flex min-w-0 flex-col gap-3.5">
            <Head
                titleRef={titleRef}
                entries={entries}
                asked={asked}
                search={setAsked}
                clear={clear}
            />

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
                        {kind !== null && <Filtered kind={kind} clear={unfilter} />}
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
                                <div className="divide-y divide-seam overflow-hidden rounded-tile border border-seam bg-panel shadow-card">
                                    {day.entries.map((entry) => (
                                        <Row key={entry.at} entry={entry} ask={ask} />
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                    <Insights entries={entries} picked={kind} pick={filter} jump={jump} />
                </div>
            )}
        </div>
    );
}

export default History;
