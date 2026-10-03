import type { LucideIcon } from 'lucide-react';

interface EmptyProps {
    Icon: LucideIcon;
    title: string;
    note: string;
    action: string;
    ActionIcon: LucideIcon;
    run: () => void;
}

function Empty({ Icon, title, note, action, ActionIcon, run }: EmptyProps) {
    return (
        <div className="flex flex-col items-center gap-3 rounded-tile border border-dashed border-line px-6 py-12 text-center">
            <span className="grid size-10 place-items-center rounded-full bg-field text-hush">
                <Icon size={18} strokeWidth={1.9} />
            </span>
            <div className="flex flex-col gap-1">
                <span className="text-branch font-strong text-bright">{title}</span>
                <span className="text-row text-faint">{note}</span>
            </div>
            <button
                type="button"
                onClick={run}
                className="mt-1 flex cursor-pointer items-center gap-2 rounded-full border border-edge bg-bubble px-3.5 py-1.75 text-row text-soft transition ease-out hover:border-ghost hover:text-cream active:scale-97"
            >
                <ActionIcon size={13} strokeWidth={2} />
                {action}
            </button>
        </div>
    );
}

export default Empty;
