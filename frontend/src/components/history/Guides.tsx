const CLEAR = 0.15;
const LABEL = 'absolute left-full ml-1.5 -translate-y-1/2 font-mono text-axis text-faint';

interface GuidesProps {
    most: number;
    average: number | null;
}

function Guides({ most, average }: GuidesProps) {
    // An average near the top hides the top's number
    const crowded = average !== null && 1 - average / most < CLEAR;

    return (
        <>
            <div
                aria-hidden="true"
                className="pointer-events-none absolute top-0 right-7 left-0 border-t border-line"
            >
                {!crowded && <span className={LABEL}>{most}</span>}
            </div>
            {average !== null && average > 0 && (
                <div
                    aria-hidden="true"
                    className="pointer-events-none absolute right-7 left-0 border-t border-dashed border-faint/60"
                    style={{ bottom: `${(average / most) * 100}%` }}
                >
                    <span className={LABEL}>avg</span>
                </div>
            )}
        </>
    );
}

export default Guides;
