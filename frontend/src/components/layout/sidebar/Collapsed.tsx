import clsx from 'clsx';
import Toggle from './Toggle';
import { running } from '@/lib/status';
import { Settings } from 'lucide-react';
import { NAV, TAGS, TAGS_HIT } from './tints';
import type { SystemStatus } from '@/types/status';

const CELL = 'grid size-11 shrink-0 place-items-center rounded-row';

const CODES: Record<string, string> = {
    Red: 'RL',
    Orange: 'OL',
    Green: 'GL',
    Blue: 'BL',
    CR: 'CR',
};

interface CollapsedProps {
    status: SystemStatus | null;
    toggle: () => void;
}

function Collapsed({ status, toggle }: CollapsedProps) {
    return (
        <aside className="hidden w-20 shrink-0 flex-col overflow-hidden border-r border-line bg-rail pt-5 pb-3 lg:flex">
            <div className="flex flex-col items-center">
                <Toggle toggle={toggle} />
            </div>

            <nav className="mt-4.5 flex flex-col items-center gap-0.5">
                {NAV.map(({ label, Icon }) => {
                    const current = label === 'Ask';
                    return (
                        <div
                            key={label}
                            title={label}
                            className={clsx(CELL, current && 'bg-accent/11')}
                        >
                            <Icon
                                size={20}
                                strokeWidth={1.8}
                                fill={current ? 'currentColor' : 'none'}
                                stroke={current ? 'none' : 'currentColor'}
                                className={current ? 'text-accent' : 'text-hush'}
                                aria-hidden="true"
                            />
                        </div>
                    );
                })}
            </nav>

            <div className="mx-3.5 mt-4.5 h-px bg-seam" />

            {status !== null && status.ok && (
                <div className="mt-5.5 flex flex-col items-center gap-3">
                    {status.lines.map((line) => {
                        const ok = running(line);
                        return (
                            <div
                                key={line.line_id}
                                title={line.line_name}
                                className={clsx(
                                    CELL,
                                    'relative border',
                                    ok ? TAGS[line.line_id] : TAGS_HIT[line.line_id],
                                )}
                            >
                                <span className="font-mono text-code">{CODES[line.line_id]}</span>
                                <span
                                    className={clsx(
                                        'absolute -top-hair -right-hair size-2.5 rounded-full ring-[2.5px] ring-rail',
                                        ok ? 'bg-good' : 'animate-beacon bg-amber',
                                    )}
                                    aria-hidden="true"
                                />
                            </div>
                        );
                    })}
                </div>
            )}

            <div className="mt-auto flex flex-col items-center">
                <div className="grid size-11 place-items-center rounded-row">
                    <Settings
                        size={20}
                        strokeWidth={1.8}
                        className="text-hush"
                        aria-hidden="true"
                    />
                </div>
            </div>
        </aside>
    );
}

export default Collapsed;
