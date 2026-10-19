import { memo } from 'react';
import { clockOf } from './frame';
import { CalendarX, Hourglass, MoonStar } from 'lucide-react';
import type { Box } from './plot';
import type { Drawn } from '@/lib/lines';
import type { Transit } from '@/types/transit';

interface QuietProps {
    box: Box;
    lines: readonly Drawn[];
    resumes: Transit['resumes'];
    read: number;
    timetable: boolean;
}

// What the empty chart says
function noteOf(next: number | null, timetable: boolean) {
    if (!timetable) {
        return {
            Icon: CalendarX,
            title: 'Timetable unavailable',
            detail: "Train times can't be read right now.",
        };
    }
    if (next === null) {
        return {
            Icon: Hourglass,
            title: 'No readings yet',
            detail: 'The chart fills in as trains arrive.',
        };
    }
    return {
        Icon: MoonStar,
        title: 'No trains running',
        detail: `Trains start again at ${clockOf(next)}.`,
    };
}

function Quiet({ box, lines, resumes, read, timetable }: QuietProps) {
    const times = lines.map((line) => Date.parse(resumes[line.id] ?? ''));

    // Nothing due once any line is already running
    const due = times.some((at) => at <= read) ? [] : times.filter((at) => at > read);
    const next = due.length === 0 ? null : Math.min(...due);
    const { Icon, title, detail } = noteOf(next, timetable);

    return (
        <div
            style={{
                left: box.left,
                top: box.ceil,
                width: box.right - box.left,
                height: box.floor - box.ceil,
            }}
            className="absolute grid place-items-center"
        >
            <div className="flex max-w-72 flex-col items-center rounded-tile bg-panel px-6 py-3.5 text-center transition-opacity duration-200 ease-out starting:opacity-0">
                <span className="mb-2.5 grid size-8 place-items-center rounded-full border border-seam bg-field text-hush">
                    <Icon size={14} strokeWidth={2} />
                </span>
                <span className="text-row font-medium text-soft">{title}</span>
                <span className="mt-1 text-xs/relaxed text-faint">{detail}</span>
            </div>
        </div>
    );
}

export default memo(Quiet);
