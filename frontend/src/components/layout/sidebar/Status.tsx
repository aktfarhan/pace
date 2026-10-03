import clsx from 'clsx';
import Subline from './Subline';
import LineCard from './LineCard';
import { BEHIND, LIVE } from '@/components/layout/tints';
import SectionHeading from '@/components/layout/SectionHeading';
import { headlineOf, runningCount, sectionsOf } from '@/lib/status';
import type { SystemStatus } from '@/types/status';

interface StatusProps {
    status: SystemStatus | null;
}

function Status({ status }: StatusProps) {
    if (status === null) {
        return null;
    }

    const calm = status.ok && runningCount(status.lines) === status.lines.length;

    return (
        <div className="mt-4.5">
            <div className="flex flex-col gap-1.25 px-1.5">
                <div className="flex items-center gap-2.5">
                    <span
                        className={clsx('size-2 shrink-0 rounded-full', calm ? LIVE : BEHIND)}
                        aria-hidden="true"
                    />
                    <span className="min-w-0 flex-1 truncate text-headline text-bright">
                        {headlineOf(status)}
                    </span>
                </div>
                <Subline status={status} />
            </div>

            {status.ok &&
                sectionsOf(status.lines).map((section) => (
                    <div key={section.heading} className="px-1">
                        <SectionHeading label={section.heading} />
                        <div className="flex flex-col gap-2">
                            {section.lines.map((line) => (
                                <LineCard key={line.line_id} line={line} />
                            ))}
                        </div>
                    </div>
                ))}
        </div>
    );
}

export default Status;
