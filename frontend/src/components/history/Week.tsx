import clsx from 'clsx';
import Bars from './Bars';
import { useState } from 'react';
import { CARD, FILLS, lookOf } from './tints';
import { dayKey, todayOf } from '@/lib/insights';
import type { Entry } from '@/types/history';

interface WeekProps {
    entries: Entry[];
    jump: (key: string) => void;
}

function Week({ entries, jump }: WeekProps) {
    const [picked, setPicked] = useState<number | null>(null);

    const bars = todayOf(entries);
    const asked = bars.reduce((sum, one) => sum + one.total, 0);
    const bar = picked === null ? null : bars[picked];
    const shown = bar === null ? asked : bar.total;

    return (
        <section className={CARD}>
            <h2 className="text-title text-bright">Today</h2>
            <div className="mt-1.5 flex items-baseline gap-1.5">
                <span className="text-headline text-bright tabular-nums">{shown}</span>
                <span className="text-row text-dim">{shown === 1 ? 'question' : 'questions'}</span>
            </div>
            <div className="mt-0.5 flex h-4.5 min-w-0 items-center gap-2.5 overflow-hidden text-xs whitespace-nowrap text-hush">
                {bar === null ? (
                    'Today so far'
                ) : (
                    <>
                        <span className="text-soft">{bar.name}</span>
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
                bars={bars}
                picked={picked}
                pick={setPicked}
                jump={() => jump(dayKey(Date.now()))}
            />
        </section>
    );
}

export default Week;
