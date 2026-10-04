import MonthDay from './MonthDay';
import type { PointerEvent } from 'react';
import type { Tally } from '@/lib/insights';

const WEEKDAYS = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

interface MonthProps {
    days: Tally[];
    picked: number | null;
    pick: (index: number | null) => void;
    jump: (key: string) => void;
}

function Month({ days, picked, pick, jump }: MonthProps) {
    const most = Math.max(...days.map((day) => day.total));

    // Lines the 1st up under its weekday
    const now = new Date();
    const lead = new Date(now.getFullYear(), now.getMonth(), 1).getDay();
    const weeks = Math.ceil((lead + days.length) / 7);

    // A mouse leaving the calendar lets go of its day
    const leave = (event: PointerEvent) => {
        if (event.pointerType === 'mouse') pick(null);
    };

    return (
        <div
            role="group"
            aria-label="Questions each day this month"
            onPointerLeave={leave}
            className="mt-4 max-w-80 cursor-default select-none"
        >
            <div aria-hidden="true" className="grid grid-cols-7 gap-x-0.75">
                {WEEKDAYS.map((letter, index) => (
                    <span key={index} className="text-center font-mono text-axis text-faint">
                        {letter}
                    </span>
                ))}
            </div>
            <div
                className="mt-1.5 grid h-24 grid-cols-7 gap-0.75"
                style={{ gridTemplateRows: `repeat(${weeks}, minmax(0, 1fr))` }}
            >
                {days.map((day, index) => (
                    <MonthDay
                        key={day.key}
                        day={day}
                        most={most}
                        start={index === 0 ? lead + 1 : undefined}
                        faded={picked !== null && picked !== index}
                        pick={() => pick(index)}
                        unpick={() => pick(null)}
                        jump={() => jump(day.key)}
                    />
                ))}
            </div>
        </div>
    );
}

export default Month;
