import Setting from './Setting';
import OtherNote from './OtherNote';
import { BUTTON, SHAPE } from './tints';
import { countUnder } from '@/lib/pace';
import { useRef, useState } from 'react';
import { LoaderCircle, MonitorSmartphone } from 'lucide-react';
import type { ChangeEvent, SubmitEvent } from 'react';

interface OtherCodeProps {
    code: string | null;
    was: string | null;
    take: (code: string) => void;
    undo: () => void;
}

function OtherCode({ code, was, take, undo }: OtherCodeProps) {
    const [entry, setEntry] = useState('');
    const [problem, setProblem] = useState<string | null>(null);
    const [checking, setChecking] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    // The entry as a code
    const typed = entry.trim().toLowerCase().replace(/\s+/g, '-');

    // Checks the code, then switches to it
    const check = async () => {
        if (checking) return;
        if (!SHAPE.test(typed)) {
            setProblem("That doesn't match the style of a code");
            return;
        }
        if (typed === code) {
            setProblem('This device already uses that code');
            return;
        }

        setProblem(null);
        setChecking(true);

        // Looks for saved places and trips
        try {
            const { places, trips } = await countUnder(typed);
            if (places + trips === 0) {
                setProblem('Nothing is saved under that code');
            } else {
                take(typed);
                setEntry('');
            }
        } catch (error) {
            console.error(error);
            setProblem("That code couldn't be checked");
        } finally {
            setChecking(false);
            inputRef.current?.focus();
        }
    };

    // Sends the entry
    const submit = (event: SubmitEvent<HTMLFormElement>) => {
        event.preventDefault();
        check();
    };

    // Goes back to this device's code
    const back = () => {
        undo();
        inputRef.current?.focus();
    };

    // Typing clears the problem
    const edit = (event: ChangeEvent<HTMLInputElement>) => {
        setEntry(event.target.value);
        setProblem(null);
    };

    return (
        <Setting
            Icon={MonitorSmartphone}
            title="Use a code from another device"
            note={<OtherNote problem={problem} was={was} back={back} />}
        >
            <form onSubmit={submit} className="flex w-full gap-2 sm:pl-12">
                <input
                    ref={inputRef}
                    value={entry}
                    readOnly={checking}
                    onChange={edit}
                    placeholder="word-word-code"
                    aria-label="Code from another device"
                    autoComplete="off"
                    autoCapitalize="none"
                    spellCheck={false}
                    className="h-8.5 min-w-0 flex-1 rounded-xl border border-edge bg-field px-3 font-mono text-row text-cream transition-colors outline-none placeholder:text-quiet focus:border-accent/40 contrast-more:focus:border-accent pointer-coarse:text-base"
                />
                <button type="submit" disabled={entry.trim() === ''} className={BUTTON}>
                    {checking && (
                        <LoaderCircle size={11} strokeWidth={2.4} className="animate-spin" />
                    )}
                    {checking ? 'Checking' : 'Use'}
                </button>
            </form>
        </Setting>
    );
}

export default OtherCode;
