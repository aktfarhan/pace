import clsx from 'clsx';
import { TABS } from './tints';
import type { Tab } from './tints';

const PILL =
    'inline-flex cursor-pointer items-center gap-1.75 rounded-full border px-3.5 py-1.5 font-mono text-state uppercase';

interface TabsProps {
    tab: Tab;
    select: (tab: Tab) => void;
}

function Tabs({ tab, select }: TabsProps) {
    return (
        <div className="flex gap-1.5">
            {TABS.map(({ label, dot }) => (
                <button
                    key={label}
                    type="button"
                    onClick={() => select(label)}
                    className={clsx(
                        PILL,
                        label === tab
                            ? 'border-edge bg-accent/10 text-accent'
                            : 'border-seam text-dim',
                    )}
                >
                    {dot && <span className={clsx('size-1.5 rounded-full', dot)} />}
                    {label}
                </button>
            ))}
        </div>
    );
}

export default Tabs;
