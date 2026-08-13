interface SectionHeadingProps {
    label: string;
}

function SectionHeading({ label }: SectionHeadingProps) {
    return (
        <div className="flex items-center gap-2.5 px-0.5 pt-3.25 pb-1.75">
            <span className="font-mono text-heading whitespace-nowrap text-faint uppercase">
                {label}
            </span>
            <span className="h-px flex-1 bg-seam" />
        </div>
    );
}

export default SectionHeading;
