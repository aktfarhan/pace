import clsx from 'clsx';
import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';

// A plain tile
const TILE = 'bg-field text-hush';

interface SettingProps {
    Icon: LucideIcon;
    tile?: string;
    title: string;
    note: ReactNode;
    noteId?: string;
    children?: ReactNode;
}

function Setting({ Icon, tile = TILE, title, note, noteId, children }: SettingProps) {
    return (
        <div className="flex flex-wrap items-center gap-x-3.5 gap-y-3 px-4 py-3.25">
            <span className={clsx('grid size-8.5 place-items-center rounded-mark', tile)}>
                <Icon size={15} strokeWidth={2} />
            </span>
            <div className="flex-1 basis-40">
                <div className="text-row text-cream">{title}</div>
                <div id={noteId} className="mt-0.5 text-xs text-hush">
                    {note}
                </div>
            </div>
            {children}
        </div>
    );
}

export default Setting;
