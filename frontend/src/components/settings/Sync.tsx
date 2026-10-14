import clsx from 'clsx';
import Swap from './Swap';
import Setting from './Setting';
import { useState } from 'react';
import OtherCode from './OtherCode';
import { useMoment } from '@/hooks/useMoment';
import { useHolding } from '@/hooks/useHolding';
import { Check, Copy, KeyRound } from 'lucide-react';
import { BUTTON, ICON_BUTTON, SAID_MS } from './tints';
import { readCode, readWas, takeCode, undoCode } from '@/lib/pace';

// Shown when the clipboard refuses
const BLOCKED = 'Copying was blocked';

function Sync() {
    const code = readCode();
    const was = readWas();
    const [shown, setShown] = useState(false);
    const [blocked, setBlocked] = useState(false);
    const [copied, setCopied] = useMoment(false, SAID_MS);
    const count = useHolding(code);

    // Copies the code
    const copy = async (text: string) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setBlocked(false);
        } catch (error) {
            console.error(error);
            setBlocked(true);
        }
    };

    // What the code holds
    const noteOf = () => {
        if (code === null) return 'None yet';
        if (blocked) return <span className="text-red">{BLOCKED}</span>;
        if (count === null) return "Checking what's saved…";
        return count.failed ? <span className="text-red">{count.text}</span> : count.text;
    };

    // Switches to another device's code
    const take = (other: string) => {
        takeCode(other);
        setBlocked(false);
    };

    // Goes back to this device's code
    const undo = () => {
        undoCode();
        setBlocked(false);
    };

    return (
        <>
            <Setting
                Icon={KeyRound}
                tile="bg-accent/10 text-accent"
                title="This device's code"
                note={noteOf()}
            >
                {code !== null && (
                    <div className="flex flex-wrap items-center gap-2">
                        <Swap
                            on={shown ? code : 'hidden'}
                            className={clsx(
                                'font-mono text-code text-bright',
                                shown && 'select-all',
                            )}
                        >
                            {shown ? code : '•'.repeat(code.length)}
                        </Swap>
                        <button type="button" onClick={() => setShown(!shown)} className={BUTTON}>
                            {shown ? 'Hide' : 'Show'}
                        </button>
                        <button
                            type="button"
                            aria-label="Copy"
                            onClick={() => copy(code)}
                            className={ICON_BUTTON}
                        >
                            <Swap on={String(copied)}>
                                {copied ? (
                                    <Check size={11} strokeWidth={2.4} />
                                ) : (
                                    <Copy size={11} strokeWidth={2.2} />
                                )}
                            </Swap>
                        </button>
                    </div>
                )}
            </Setting>
            <OtherCode code={code} was={was} take={take} undo={undo} />
        </>
    );
}

export default Sync;
