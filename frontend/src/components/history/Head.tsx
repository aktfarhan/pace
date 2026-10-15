import Paused from './Paused';
import Find from '@/components/layout/Find';
import type { RefObject } from 'react';
import type { Entry } from '@/types/history';

const EMPTY = 'No questions asked yet';

interface HeadProps {
    titleRef: RefObject<HTMLHeadingElement | null>;
    entries: Entry[];
    asked: string;
    search: (asked: string) => void;
}

function Head({ titleRef, entries, asked, search }: HeadProps) {
    const empty = entries.length === 0;
    const refused = entries.filter((entry) => entry.refused).length;
    const answered = entries.length - refused;

    const kept = empty
        ? EMPTY
        : `${answered} answered${refused > 0 ? ` · ${refused} refused` : ''}`;

    return (
        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-3">
            <div className="min-w-0">
                <h1 ref={titleRef} tabIndex={-1} className="text-board text-bright">
                    History
                </h1>
                <div className="mt-0.5 text-row text-faint">
                    {kept}
                    <Paused />
                </div>
            </div>
            {!empty && <Find asked={asked} search={search} label="Search questions" />}
        </div>
    );
}

export default Head;
