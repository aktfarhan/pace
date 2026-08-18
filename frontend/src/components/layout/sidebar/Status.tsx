import clsx from 'clsx';
import Subline from './Subline';
import { Fragment } from 'react';
import Branches from './Branches';
import LineCard from './LineCard';
import SectionHeading from './SectionHeading';
import { useStatus } from '@/hooks/useStatus';
import { BRANCHED, headlineOf, running, runningCount, sectionsOf } from '@/lib/status';

function Status() {
    const status = useStatus();

    if (status === null) {
        return null;
    }

    const calm = status.ok && runningCount(status.lines) === status.lines.length;

    return (
        <div className="mt-4.5">
            <div className="flex flex-col gap-1.25 px-1.5">
                <div className="flex items-center gap-2.5">
                    <span
                        className={clsx(
                            'size-2 shrink-0 rounded-full',
                            calm ? 'bg-good shadow-glow' : 'animate-beacon bg-amber shadow-pulse',
                        )}
                        aria-hidden="true"
                    />
                    <span className="min-w-0 flex-1 truncate text-headline text-bright">
                        {headlineOf(status)}
                    </span>
                </div>
                <Subline status={status} />
            </div>

            {status.ok &&
                sectionsOf(status.lines).map((section) => {
                    const branched = section.lines.find((line) => line.line_id === BRANCHED);
                    return (
                        <Fragment key={section.heading}>
                            <div className="px-1">
                                <SectionHeading label={section.heading} />
                                <div className="flex flex-col gap-2">
                                    {section.lines.map((line) => (
                                        <LineCard key={line.line_id} line={line} />
                                    ))}
                                </div>
                            </div>

                            {branched !== undefined &&
                                branched.state !== 'clear' &&
                                !running(branched) && (
                                    <div className="px-1">
                                        <SectionHeading label="Branches" />
                                        <Branches line={branched} />
                                    </div>
                                )}
                        </Fragment>
                    );
                })}
        </div>
    );
}

export default Status;
