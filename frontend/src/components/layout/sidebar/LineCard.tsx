import clsx from 'clsx';
import { BADGES, CARDS, CHIPS, PILLS } from './tints';
import { chipsOf, effectWord, running } from '@/lib/status';
import type { LineStatus } from '@/types/status';

interface LineCardProps {
    line: LineStatus;
}

function LineCard({ line }: LineCardProps) {
    const chips = chipsOf(line);
    const ok = running(line);

    const tinted = line.state === 'disrupted' || line.state === 'severe';
    const chipFill = tinted ? 'bg-panel' : 'bg-ink';

    return (
        <div
            className={clsx(
                'flex flex-col gap-2.25 rounded-tile border px-3.5 py-3.25',
                ok ? CARDS.clear : CARDS[line.state],
            )}
        >
            <div className="flex items-center gap-2.75">
                <span
                    className={clsx(
                        'shrink-0 rounded-chip border px-2 py-hair font-mono text-badge uppercase',
                        BADGES[line.line_id],
                    )}
                >
                    {line.badge_text}
                </span>
                <span className="min-w-0 flex-1 truncate text-base font-strong text-bright">
                    {line.line_name}
                </span>

                {ok && (
                    <span className="flex shrink-0 items-center gap-1.75">
                        <span className="size-1.75 rounded-full bg-good shadow-glow" />
                        <span className="font-mono text-state text-steady uppercase">On time</span>
                    </span>
                )}
                {!ok && line.alert_delay_minutes !== null && (
                    <span className="flex shrink-0 items-baseline gap-0.75">
                        <span className="text-hero text-delay">
                            +{line.alert_delay_minutes[0]}
                            {line.alert_delay_minutes[1] !== line.alert_delay_minutes[0] &&
                                `-${line.alert_delay_minutes[1]}`}
                        </span>
                        <span className="font-mono text-unit text-faint uppercase">min</span>
                    </span>
                )}
                {!ok && line.state !== 'clear' && line.alert_delay_minutes === null && (
                    <span
                        className={clsx(
                            'shrink-0 rounded-chip border px-2 py-hair font-mono text-pill uppercase',
                            PILLS[line.state],
                        )}
                    >
                        {effectWord(line.effect)}
                    </span>
                )}
            </div>

            <div className="flex items-center gap-1.75">
                {chips.map((chip) => (
                    <span
                        key={chip.text}
                        className={clsx(
                            'rounded-chip border px-2 py-0.75 font-mono text-chip whitespace-nowrap uppercase',
                            chipFill,
                            CHIPS[chip.tone],
                        )}
                    >
                        {chip.text}
                    </span>
                ))}
            </div>
        </div>
    );
}

export default LineCard;
