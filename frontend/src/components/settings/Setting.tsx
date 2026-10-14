import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';

interface SettingProps {
    Icon: LucideIcon;
    title: string;
    note: string;
    children: ReactNode;
}

function Setting({ Icon, title, note, children }: SettingProps) {
    return (
        <div className="flex flex-wrap items-center gap-x-3.5 gap-y-3 px-4 py-3.25">
            <span className="grid size-8.5 place-items-center rounded-mark bg-field text-hush">
                <Icon size={15} strokeWidth={2} />
            </span>
            <div className="flex-1 basis-40">
                <div className="text-row text-cream">{title}</div>
                <div className="mt-0.5 text-xs text-hush">{note}</div>
            </div>
            {children}
        </div>
    );
}

export default Setting;
