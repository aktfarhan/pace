import clsx from 'clsx';
import { sinceOf } from './feed';
import { effectWord } from '@/lib/status';
import { CARDS, CHIPS, PILLS } from '@/components/layout/sidebar/tints';
import type { Notice } from '@/types/transit';

function Alert({ lines, alert }: Notice) {
    return (
        <article
            className={clsx(
                'flex flex-col gap-2.25 rounded-tile border px-3.5 py-3.25',
                alert.slowing ? CARDS.disrupted : CARDS.notice,
            )}
        >
            <div className="flex flex-wrap items-center gap-x-2.75 gap-y-2">
                <span className="flex shrink-0 items-center gap-1">
                    {lines.map((one) => (
                        <span
                            key={one.id}
                            className={clsx(
                                'rounded-chip border px-2 py-hair font-mono text-badge uppercase',
                                one.chip,
                            )}
                        >
                            {one.code}
                        </span>
                    ))}
                </span>
                <span className="min-w-48 flex-1 text-base leading-snug font-strong text-bright">
                    {alert.headline}
                </span>
                {alert.slowing && (
                    <span
                        className={clsx(
                            'shrink-0 rounded-chip border px-2 py-hair font-mono text-pill uppercase',
                            PILLS.disrupted,
                        )}
                    >
                        {effectWord(alert.effect)}
                    </span>
                )}
            </div>

            <div className="flex items-center gap-1.75">
                <span
                    className={clsx(
                        'rounded-chip border bg-ink px-2 py-0.75 font-mono text-chip whitespace-nowrap uppercase',
                        CHIPS.read,
                    )}
                >
                    {sinceOf(alert.since)}
                </span>
                {alert.where !== null && (
                    <span
                        className={clsx(
                            'truncate rounded-chip border bg-ink px-2 py-0.75 font-mono text-chip whitespace-nowrap uppercase',
                            CHIPS.quiet,
                        )}
                    >
                        {alert.where}
                    </span>
                )}
            </div>

            {alert.detail !== '' && (
                <p className="text-branch leading-relaxed text-hush">{alert.detail}</p>
            )}
        </article>
    );
}

export default Alert;
