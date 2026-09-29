import { branchLettersOf, branchesHeard, effectWord, running } from '@/lib/status';
import type { LineStatus } from '@/types/status';

interface BranchMarksProps {
    line: LineStatus;
}

function BranchMarks({ line }: BranchMarksProps) {
    const shown = branchLettersOf(line);
    if (shown.length === 0) return null;

    return (
        <span className="ml-auto flex shrink-0 items-center gap-1">
            {line.state !== 'clear' && !running(line) && (
                <span className="sr-only">{branchesHeard(effectWord(line.effect), shown)}</span>
            )}
            {shown.map((letter) => (
                <span
                    key={letter}
                    aria-hidden="true"
                    className="grid size-4.5 place-items-center rounded-full bg-green-fill text-letter text-ink"
                >
                    {letter}
                </span>
            ))}
        </span>
    );
}

export default BranchMarks;
