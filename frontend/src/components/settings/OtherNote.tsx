import { LINK } from './tints';

interface OtherNoteProps {
    problem: string | null;
    was: string | null;
    back: () => void;
}

function OtherNote({ problem, was, back }: OtherNoteProps) {
    if (problem !== null) return <span className="text-red">{problem}</span>;
    if (was === null) return 'The code shown on that device';

    return (
        <button type="button" onClick={back} className={LINK}>
            Go back to this device's code
        </button>
    );
}

export default OtherNote;
