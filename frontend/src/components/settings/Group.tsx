import SectionHeading from '@/components/layout/SectionHeading';
import type { ReactNode } from 'react';

const GROUP = 'divide-y divide-seam rounded-tile border border-seam bg-panel shadow-card';

interface GroupProps {
    label: string;
    foot?: ReactNode;
    children: ReactNode;
}

function Group({ label, foot, children }: GroupProps) {
    return (
        <section>
            <SectionHeading label={label} />
            <div className={GROUP}>{children}</div>
            {foot !== undefined && <p className="px-1 pt-2 text-xs text-hush">{foot}</p>}
        </section>
    );
}

export default Group;
