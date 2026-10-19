import clsx from 'clsx';
import Alert from './Alert';
import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { kindOf, threadsOf } from './feed';
import SectionHeading from '@/components/layout/SectionHeading';
import type { Notice } from '@/types/transit';

const FOLD = 5;
const MARKS = 4;

interface AlertGroupProps {
    name: string;
    notices: Notice[];
    panel: string;
    folds: boolean;
    searching: boolean;
}

function AlertGroup({ name, notices, panel, folds, searching }: AlertGroupProps) {
    const [all, setAll] = useState(false);

    // Searching shows every match
    const threads = threadsOf(notices);
    const foldable = folds && !searching && threads.length - FOLD > 1;
    const head = foldable ? threads.slice(0, FOLD) : threads;
    const tail = foldable ? threads.slice(FOLD) : [];
    const hidden = [...new Set(tail.map(({ lead }) => kindOf(lead.alert.effect)))].slice(0, MARKS);

    return (
        <div>
            <SectionHeading label={name} count={notices.length} level={3} />
            <div
                className={clsx(
                    'divide-y divide-seam overflow-hidden rounded-tile border shadow-card',
                    panel,
                )}
            >
                {head.map((thread) => (
                    <Alert key={thread.lead.alert.alert_id} thread={thread} searching={searching} />
                ))}
                {all && tail.length > 0 && (
                    <div className="divide-y divide-seam transition-opacity duration-200 ease-out starting:opacity-0">
                        {tail.map((thread) => (
                            <Alert
                                key={thread.lead.alert.alert_id}
                                thread={thread}
                                searching={searching}
                            />
                        ))}
                    </div>
                )}
                {foldable && (
                    <div className="flex justify-center px-4 py-2.5">
                        <button
                            type="button"
                            aria-expanded={all}
                            onClick={() => setAll(!all)}
                            className="flex cursor-pointer items-center gap-2.5 rounded-full border border-edge bg-bubble py-1.25 pr-3 pl-1.5 font-mono text-chip text-soft uppercase transition ease-out hover:border-ghost hover:text-cream active:scale-97 aria-expanded:pl-3"
                        >
                            {!all && (
                                <span className="flex">
                                    {hidden.map((kind) => (
                                        <span
                                            key={kind.name}
                                            className="-ml-1.5 grid size-5 place-items-center rounded-full bg-field text-hush ring-2 ring-bubble first:ml-0"
                                        >
                                            <kind.Icon size={11} strokeWidth={2} />
                                        </span>
                                    ))}
                                </span>
                            )}
                            {all ? 'Show fewer' : `Show ${tail.length} more`}
                            <ChevronDown
                                size={13}
                                strokeWidth={2.2}
                                className={clsx(
                                    'transition-transform duration-200 ease-out',
                                    all && 'rotate-180',
                                )}
                            />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

export default AlertGroup;
