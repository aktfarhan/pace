import clsx from 'clsx';
import Tip from './Tip';
import Toggle from './Toggle';
import { running } from '@/lib/status';
import { Settings } from 'lucide-react';
import { LINE_BY_ID } from '@/lib/lines';
import { useGlide } from '@/hooks/useGlide';
import { GLIDE } from '@/components/layout/tints';
import { AWAY, GLIDE_ROUND, HERE, NAV, OUTLINED } from './tints';
import type { Page } from './tints';
import type { SystemStatus } from '@/types/status';

const CELL = 'grid size-11 shrink-0 place-items-center rounded-row';

interface CollapsedProps {
    status: SystemStatus | null;
    toggle: () => void;
    page: Page;
    select: (page: Page) => void;
}

function Collapsed({ status, toggle, page, select }: CollapsedProps) {
    const { rowRef, glideRef } = useGlide<HTMLElement>(page, 1, GLIDE_ROUND);

    return (
        <div className="flex h-full w-collapsed flex-col overflow-y-auto">
            <div className="sticky top-0 z-10 flex flex-col items-center bg-rail pt-5">
                <Toggle toggle={toggle} />
            </div>

            <nav ref={rowRef} className="relative mt-4.5 flex flex-col items-center gap-0.5">
                {NAV.map(({ label, Icon }, index) => (
                    <Tip key={label} label={label} keycap={String(index + 1)}>
                        <button
                            type="button"
                            aria-label={label}
                            aria-current={label === page ? 'page' : undefined}
                            data-picked={label === page}
                            onClick={() => select(label)}
                            className={clsx(CELL, AWAY)}
                        >
                            <Icon {...OUTLINED} />
                        </button>
                    </Tip>
                ))}
                <div
                    ref={glideRef}
                    data-glide
                    aria-hidden="true"
                    className={`${GLIDE} flex flex-col items-center gap-0.5`}
                >
                    {NAV.map(({ label, Icon }) => (
                        <span key={label} className="rounded-row bg-rail">
                            <span className={clsx(CELL, HERE)}>
                                <Icon {...OUTLINED} />
                            </span>
                        </span>
                    ))}
                </div>
            </nav>

            <div className="mx-3.5 mt-4.5 h-px bg-seam" />

            {status !== null && status.ok && (
                <div className="mt-5.5 flex flex-col items-center gap-3">
                    {status.lines.map((line) => {
                        const ok = running(line);
                        const tint = LINE_BY_ID[line.line_id];
                        return (
                            <div
                                key={line.line_id}
                                title={line.line_name}
                                className={clsx(
                                    CELL,
                                    'relative border',
                                    ok ? tint?.tag : tint?.tagHit,
                                )}
                            >
                                <span className="font-mono text-code">{tint?.code}</span>
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

            <div className="sticky bottom-0 mt-auto flex flex-col items-center bg-rail pb-3">
                <div className="grid size-11 place-items-center rounded-row">
                    <Settings
                        size={20}
                        strokeWidth={1.8}
                        className="text-hush"
                        aria-hidden="true"
                    />
                </div>
            </div>
        </div>
    );
}

export default Collapsed;
