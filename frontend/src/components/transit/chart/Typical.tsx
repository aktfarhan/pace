interface TypicalProps {
    path: string;
    stroke: string;
}

function Typical({ path, stroke }: TypicalProps) {
    return (
        <path
            d={path}
            fill="none"
            strokeWidth={1.5}
            strokeOpacity={0.4}
            strokeDasharray="4 5"
            strokeLinecap="round"
            className={stroke}
        />
    );
}

export default Typical;
