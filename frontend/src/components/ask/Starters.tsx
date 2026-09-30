import clsx from 'clsx';
import { RISE } from './tints';
import { useEffect, useState } from 'react';
import { useShowLine } from '@/hooks/useShowLine';
import { effectWord, running } from '@/lib/status';
import type { AskController } from '@/hooks/useAsk';
import type { AlertedLine, SystemStatus } from '@/types/status';

const CHIP =
    'relative cursor-pointer rounded-full border border-edge bg-field px-3.5 py-2 text-sm text-soft transition-[color,background-color,scale] ease-out hover:bg-bubble hover:text-cream active:scale-97 pointer-coarse:after:absolute pointer-coarse:after:inset-x-0 pointer-coarse:after:-inset-y-1';

// Questions on the ask screen
const STARTERS = [
    'How do I get from Park Street to Harvard?',
    'Is the Red Line running normally?',
    'When is the last train from Kenmore?',
    'When is the next train at Downtown Crossing?',
];

// Whether the greeting already happened
let greeted = false;

interface StartersProps {
    ask: AskController['send'];
    status: SystemStatus | null;
}

function Starters({ ask, status }: StartersProps) {
    const show = useShowLine();

    // The greeting rises on the first visit
    const [first] = useState(() => !greeted);
    useEffect(() => {
        greeted = true;
    }, []);

    // Lines that are down
    const down = status?.ok
        ? status.lines.filter((line): line is AlertedLine => !running(line))
        : [];

    return (
        <div className="flex flex-1 flex-col items-center justify-center gap-6 px-4 text-center">
            <div className={clsx('flex flex-col gap-2', first && RISE)}>
                <h1 className="text-board text-bright">Where to?</h1>
                <span className="text-sm text-hush">
                    Trips, schedules and alerts across the MBTA.
                </span>
            </div>
            {down.length > 0 && (
                <div className="-mt-2 flex flex-wrap justify-center gap-1.5 sm:hidden">
                    {down.map((line) => (
                        <button
                            key={line.line_id}
                            type="button"
                            onClick={() => show(line.line_id)}
                            className="flex cursor-pointer items-center gap-1.5 rounded-full border border-amber/28 bg-amber/10 px-3 py-1 font-mono text-chip text-amber uppercase transition-[scale] ease-out active:scale-96"
                        >
                            <span className="size-1.5 rounded-full bg-amber" />
                            {line.line_name} · {effectWord(line.effect)}
                        </button>
                    ))}
                </div>
            )}
            <div
                className={clsx(
                    'flex max-w-xl flex-wrap justify-center gap-2',
                    first && [RISE, 'delay-75'],
                )}
            >
                {STARTERS.map((query) => (
                    <button key={query} type="button" onClick={() => ask(query)} className={CHIP}>
                        {query}
                    </button>
                ))}
            </div>
        </div>
    );
}

export default Starters;
