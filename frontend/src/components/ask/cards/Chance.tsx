interface ChanceProps {
    chance: number | null;
}

function Chance({ chance }: ChanceProps) {
    if (chance === null) return null;

    return (
        <span className="inline-flex items-center gap-2 rounded-full border border-edge bg-bubble px-2.25 py-hair font-mono text-tag uppercase tabular-nums">
            <span className="text-cream">{Math.round(chance * 100)}%</span>
            <span className="text-soft">5+ min delay</span>
        </span>
    );
}

export default Chance;
