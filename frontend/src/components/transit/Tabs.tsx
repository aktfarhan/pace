import clsx from 'clsx';
import { TABS } from './tints';
import { useGlide } from '@/hooks/useGlide';
import { GLIDE } from '@/components/layout/tints';
import type { Tab } from './tints';

// One tab's box
const BOX =
    'inline-flex items-center gap-1.75 rounded-full border px-3.5 py-1.5 font-mono text-state uppercase';

const PILL = `${BOX} cursor-pointer border-seam text-dim transition ease-out hover:border-edge hover:text-soft active:scale-96`;

// The picked look
const PICKED = `${BOX} border-edge bg-picked text-accent`;

// A ring for a line in trouble
const RING = 'outline-1 outline-offset-2 outline-amber/70';

interface TabsProps {
    tab: Tab;
    select: (tab: Tab) => void;
    troubled: ReadonlySet<Tab>;
}

function Tabs({ tab, select, troubled }: TabsProps) {
    const { rowRef, glideRef } = useGlide(tab);

    // Each tab's dot   
    const tabs = TABS.map(({ label, dot }) => {
        const trouble = troubled.has(label);
        return {
            label,
            trouble,
            dot: dot === null ? null : clsx('size-1.5 rounded-full', dot, trouble && RING),
        };
    });

    return (
        <div ref={rowRef} className="relative flex flex-wrap gap-1.5">
            {tabs.map(({ label, trouble, dot }) => (
                <button
                    key={label}
                    type="button"
                    aria-pressed={label === tab}
                    data-picked={label === tab}
                    onClick={() => select(label)}
                    className={PILL}
                >
                    {dot !== null && <span className={dot} />}
                    {label}
                    {trouble && <span className="sr-only">, not running normally</span>}
                </button>
            ))}
            <div ref={glideRef} aria-hidden="true" className={`${GLIDE} flex flex-wrap gap-1.5`}>
                {tabs.map(({ label, dot }) => (
                    <span key={label} className={PICKED}>
                        {dot !== null && <span className={dot} />}
                        {label}
                    </span>
                ))}
            </div>
        </div>
    );
}

export default Tabs;
