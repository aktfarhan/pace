import { useKeeps } from '@/hooks/useKeeps';
import { writeKeepsHistory } from '@/lib/prefs';

function Paused() {
    const keeps = useKeeps();
    if (keeps) return null;

    return (
        <>
            {' · Saving is paused. '}
            <button
                type="button"
                onClick={() => writeKeepsHistory(true)}
                className="cursor-pointer text-accent underline-offset-2 hover:underline"
            >
                Resume
            </button>
        </>
    );
}

export default Paused;
