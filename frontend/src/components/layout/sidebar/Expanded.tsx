import clsx from 'clsx';
import Code from './Code';
import Status from './Status';
import Toggle from './Toggle';
import { Settings } from 'lucide-react';
import { useGlide } from '@/hooks/useGlide';
import { GLIDE } from '@/components/layout/tints';
import { AWAY, GLIDE_ROUND, HERE, NAV, OUTLINED } from './tints';
import type { PaneProps } from './tints';

const ROW = 'flex h-11 items-center gap-3.25 rounded-row px-3 text-sm';

interface ExpandedProps extends Omit<PaneProps, 'toggle'> {
    toggle?: () => void;
}

function Expanded({ status, toggle, page, select }: ExpandedProps) {
    const { rowRef, glideRef } = useGlide<HTMLElement>(page, 1, GLIDE_ROUND);

    return (
        <div className="flex h-full w-full touch-pan-y touch-pinch-zoom flex-col overflow-y-auto px-3">
            <div className="sticky top-0 z-10 flex items-center gap-3 bg-rail px-1.5 pt-5 pb-1">
                <span className="relative grid size-7 shrink-0 place-items-center rounded-mark bg-accent">
                    <span className="text-mark text-onaccent" aria-hidden="true">
                        p
                    </span>
                    <span className="absolute right-hair bottom-hair size-1.25 rounded-full bg-ember" />
                </span>
                <span className="text-brand text-bright uppercase">Pace</span>
                {toggle !== undefined && (
                    <div className="ml-auto">
                        <Toggle toggle={toggle} expanded={true} />
                    </div>
                )}
            </div>

            <nav ref={rowRef} className="relative mt-3.5 flex flex-col gap-0.5 px-1.5">
                {NAV.map(({ label, Icon }) => (
                    <button
                        key={label}
                        type="button"
                        aria-current={label === page ? 'page' : undefined}
                        data-picked={label === page}
                        onClick={() => select(label)}
                        className={clsx(ROW, AWAY, 'font-medium')}
                    >
                        <Icon {...OUTLINED} />
                        {label}
                    </button>
                ))}
                <div
                    ref={glideRef}
                    data-glide
                    aria-hidden="true"
                    className={`${GLIDE} flex flex-col gap-0.5 px-1.5`}
                >
                    {NAV.map(({ label, Icon }) => (
                        <span key={label} className="rounded-row bg-rail">
                            <span className={clsx(ROW, HERE, 'font-strong')}>
                                <Icon {...OUTLINED} />
                                {label}
                            </span>
                        </span>
                    ))}
                </div>
            </nav>

            <Status status={status} />

            <div className="sticky bottom-0 mt-auto flex flex-col gap-3 bg-rail px-1.5 pt-3 pb-3">
                <div className="-mx-1.5 h-px bg-seam" />
                <div className={clsx(ROW, 'font-medium text-quiet')}>
                    <Settings
                        size={20}
                        strokeWidth={1.8}
                        className="text-hush"
                        aria-hidden="true"
                    />
                    <div className="flex flex-col">
                        <span>Settings</span>
                        <Code />
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Expanded;
