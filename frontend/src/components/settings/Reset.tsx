import Swap from './Swap';
import Setting from './Setting';
import { resetPrefs } from '@/lib/prefs';
import { BUTTON, SAID_MS } from './tints';
import { useMoment } from '@/hooks/useMoment';
import { Check, RotateCcw } from 'lucide-react';

interface ResetProps {
    done: () => void;
}

function Reset({ done }: ResetProps) {
    const [said, setSaid] = useMoment(false, SAID_MS);

    // Resets every choice
    const reset = () => {
        resetPrefs();
        done();
        setSaid(true);
    };

    return (
        <Setting
            Icon={RotateCcw}
            title="Reset preferences"
            note="Start page, Transit line, chart view and keeping questions"
        >
            <button type="button" onClick={reset} className={BUTTON}>
                <Swap on={String(said)} className="flex items-center gap-1.5">
                    {said && <Check size={11} strokeWidth={2.4} />}
                    {said ? 'Done' : 'Reset'}
                </Swap>
            </button>
        </Setting>
    );
}

export default Reset;
