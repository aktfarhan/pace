interface GuidesProps {
    most: number;
}

function Guides({ most }: GuidesProps) {
    return (
        <div
            aria-hidden="true"
            className="pointer-events-none absolute top-0 right-7 left-0 border-t border-line"
        >
            <span className="absolute left-full ml-1.5 -translate-y-1/2 font-mono text-axis text-faint">
                {most}
            </span>
        </div>
    );
}

export default Guides;
