import { TOP } from './plot';
import { CHIP } from './tints';
import { CEIL, FLOOR, HEIGHT } from '@/hooks/useChartBox';

// The heights the axis rules its gridlines at
const RULES = [25, 50, 75, 100].map((share) => FLOOR - (share / TOP) * (FLOOR - CEIL));

interface WaitingProps {
    note: string;
    retry: (() => void) | null;
}

function Waiting({ note, retry }: WaitingProps) {
    return (
        <div className="flex flex-col gap-3 rounded-tile border border-seam bg-panel px-6 pt-5 pb-4">
            <span className={`${CHIP} w-fit text-hush`}>Arrivals behind schedule</span>
            <div className="relative" style={{ height: HEIGHT }}>
                {RULES.map((top) => (
                    <span
                        key={top}
                        className="absolute right-0 left-0 border-t border-rule"
                        style={{ top }}
                    />
                ))}
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
                    <span className="font-mono text-chip text-ghost uppercase">{note}</span>
                    {retry !== null && (
                        <button
                            type="button"
                            onClick={retry}
                            className="cursor-pointer rounded-chip border border-edge bg-bubble px-2.5 py-1 font-mono text-chip text-soft uppercase"
                        >
                            Try again
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

export default Waiting;
