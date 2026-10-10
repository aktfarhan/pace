import clsx from 'clsx';
import Stretch from './Stretch';
import { useId, useState } from 'react';
import AlertDetail from './AlertDetail';
import { kindOf, sinceOf } from './feed';
import { effectWord } from '@/lib/status';
import { ChevronDown } from 'lucide-react';
import { PILL, PILLS } from '@/components/layout/sidebar/tints';
import type { Notice } from '@/types/transit';

const CHIP = 'rounded-chip border px-1.75 py-hair font-mono text-badge uppercase';

interface AlertProps extends Notice {
    searching: boolean;
}

function Alert({ lines, alert, searching }: AlertProps) {
    const detailId = useId();
    const [picked, setPicked] = useState<boolean | null>(null);
    const [was, setWas] = useState(searching);

    // Starting or clearing a search resets the row
    if (was !== searching) {
        setWas(searching);
        setPicked(null);
    }

    // A search opens every match
    const open = picked ?? searching;
    const kind = kindOf(alert.effect);
    const since = sinceOf(alert.since);
    const said = alert.where === null ? since : `${since} · ${alert.where}`;

    // The effect beside the row
    const effect = alert.slowing ? (
        <span className={clsx('block', PILL, PILLS.disrupted)}>{effectWord(alert.effect)}</span>
    ) : null;

    return (
        <article>
            <button
                type="button"
                aria-expanded={open}
                aria-controls={detailId}
                onClick={() => setPicked(!open)}
                className="flex w-full cursor-pointer items-center gap-3.5 px-4 py-3.25 text-left transition-colors ease-out hover:bg-field/70 focus-visible:-outline-offset-2 active:bg-field"
            >
                <span
                    className={clsx(
                        'grid size-8.5 place-items-center rounded-mark',
                        alert.slowing ? 'bg-amber/12 text-amber' : 'bg-field text-hush',
                    )}
                >
                    <kind.Icon size={15} strokeWidth={1.9} />
                </span>
                <span className="flex min-w-0 flex-1 flex-col gap-1.25">
                    <span className="text-branch leading-snug font-strong text-pretty text-bright">
                        {alert.headline}
                    </span>
                    <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
                        {effect !== null && <span className="sm:hidden">{effect}</span>}
                        <span className="flex gap-1">
                            {lines.map((one) => (
                                <span key={one.id} className={clsx(CHIP, one.chip)}>
                                    {one.code}
                                </span>
                            ))}
                        </span>
                        <span className="truncate font-mono text-chip text-faint uppercase">
                            {said}
                        </span>
                    </span>
                </span>
                {effect !== null && <span className="hidden sm:block">{effect}</span>}
                <Stretch since={alert.since} until={alert.until} slowing={alert.slowing} />
                <ChevronDown
                    size={15}
                    strokeWidth={2}
                    className={clsx(
                        'text-ghost transition-transform duration-200 ease-out',
                        open && 'rotate-180',
                    )}
                />
            </button>
            <AlertDetail id={detailId} open={open} alert={alert} />
        </article>
    );
}

export default Alert;
