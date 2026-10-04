import Find from '@/components/layout/Find';
import type { RefObject } from 'react';
import type { Entry } from '@/types/history';

const EMPTY = 'No questions asked yet.';

const CLEAR =
    'shrink-0 cursor-pointer font-mono text-tag text-faint uppercase transition-colors hover:text-cream';

interface HeadProps {
    titleRef: RefObject<HTMLHeadingElement | null>;
    entries: Entry[];
    asked: string;
    search: (asked: string) => void;
    clear: () => void;
}

function Head({ titleRef, entries, asked, search, clear }: HeadProps) {
    const empty = entries.length === 0;
    const refused = entries.filter((entry) => entry.refused).length;
    const answered = entries.length - refused;

    const kept = empty
        ? EMPTY
        : `${answered} answered · ${refused} refused · stored on this device`;

    return (
        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-3">
            <div className="min-w-0">
                <h1 ref={titleRef} tabIndex={-1} className="text-board text-bright">
                    History
                </h1>
                <div className="mt-0.5 text-row text-faint">{kept}</div>
            </div>
            {!empty && (
                <div className="flex items-center gap-4">
                    <Find asked={asked} search={search} label="Search questions" />
                    <button type="button" onClick={clear} className={CLEAR}>
                        Clear all
                    </button>
                </div>
            )}
        </div>
    );
}

export default Head;
