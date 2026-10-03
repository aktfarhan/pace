import { COUNT } from './tints';

interface SectionHeadingProps {
    label: string;
    count?: number;
}

function SectionHeading({ label, count }: SectionHeadingProps) {
    return (
        <h2 className="flex items-center gap-2 px-1 pt-3.5 pb-2">
            <span className="font-mono text-heading whitespace-nowrap text-dim uppercase">
                {label}
            </span>
            {count !== undefined && <span className={`-my-px ${COUNT}`}>{count}</span>}
        </h2>
    );
}

export default SectionHeading;
