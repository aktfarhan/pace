import { COUNT } from './tints';

interface SectionHeadingProps {
    label: string;
    count?: number;
    level?: 2 | 3;
}

function SectionHeading({ label, count, level = 2 }: SectionHeadingProps) {
    const Heading = level === 3 ? 'h3' : 'h2';

    return (
        <Heading className="flex items-center gap-2 px-1 pt-3.5 pb-2">
            <span className="font-mono text-heading whitespace-nowrap text-dim uppercase">
                {label}
            </span>
            {count !== undefined && count > 0 && <span className={`-my-px ${COUNT}`}>{count}</span>}
        </Heading>
    );
}

export default SectionHeading;
