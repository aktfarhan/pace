import clsx from 'clsx';
import Bars from './Bars';
import { useState } from 'react';
import { SPANS } from '@/lib/prefs';
import { CARD, FILLS, lookOf } from './tints';
import Segmented from '@/components/layout/Segmented';
import { dayKey, todayOf, versusBefore, weekOf } from '@/lib/insights';
import type { Span } from '@/lib/prefs';
import type { Entry } from '@/types/history';

interface WeekProps {
    entries: Entry[];
    jump: (key: string) => void;
}

function Week({ entries, jump }: WeekProps) {
    const [span, setSpan] = useState<Span>('Week');
    const [picked, setPicked] = useState<number | null>(null);

    const daily = span === 'Day';
    const bars = daily ? todayOf(entries) : weekOf(entries);
    const asked = bars.reduce((sum, one) => sum + one.total, 0);
    const bar = picked === null ? null : bars[picked];
    const shown = bar === null ? asked : bar.total;

    // A new span starts with nothing picked
    const choose = (next: Span) => {
        setSpan(next);
        setPicked(null);
    };

    // Any hour opens today
    const open = (key: string) => jump(daily ? dayKey(Date.now()) : key);

    return (
        <section className={CARD}>
            <div className="flex items-center justify-between gap-3">
                <h2 className="text-title text-bright">{daily ? 'Today' : 'Last 7 days'}</h2>
                <Segmented label="Span of the chart" options={SPANS} value={span} pick={choose} />
            </div>
            <div className="mt-1.5 flex items-baseline gap-1.5">
                <span className="text-headline text-bright tabular-nums">{shown}</span>
                <span className="text-row text-dim">{shown === 1 ? 'question' : 'questions'}</span>
            </div>
            <div className="mt-0.5 flex h-4.5 min-w-0 items-center gap-2.5 overflow-hidden text-xs whitespace-nowrap text-hush">
                {bar === null ? (
                    versusBefore(span, entries, asked)
                ) : (
                    <>
                        <span className="text-soft">
                            {bar.current && !daily ? 'Today' : bar.name}
                        </span>
                        {bar.parts.map(([kind, count]) => (
                            <span key={kind} className="flex items-center gap-1">
                                <span className={clsx('size-1.5 rounded-full', FILLS[kind])} />
                                {count}
                                {bar.parts.length <= 2 && ` ${lookOf(kind).label}`}
                            </span>
                        ))}
                    </>
                )}
            </div>
            <Bars
                key={span}
                bars={bars}
                dense={daily}
                picked={picked}
                pick={setPicked}
                jump={open}
            />
        </section>
    );
}

export default Week;
