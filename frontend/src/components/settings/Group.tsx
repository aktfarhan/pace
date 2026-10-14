import SectionHeading from '@/components/layout/SectionHeading';
import type { ReactNode } from 'react';

const GROUP = 'rounded-tile border border-seam bg-panel shadow-card';

interface GroupProps {
    label: string;
    children: ReactNode;
}

function Group({ label, children }: GroupProps) {
    return (
        <section>
            <SectionHeading label={label} />
            <div className={GROUP}>{children}</div>
        </section>
    );
}

export default Group;
