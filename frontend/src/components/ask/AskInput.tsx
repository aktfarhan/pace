import { useState } from 'react';
import { ArrowUp } from 'lucide-react';
import { readHistory } from '@/lib/history';
import { useStrayKeys } from '@/hooks/useStrayKeys';
import type { AskController } from '@/hooks/useAsk';
import type { KeyboardEvent, RefObject } from 'react';

interface AskInputProps {
    send: AskController['send'];
    busy: boolean;
    asked: string[];
    ref: RefObject<HTMLInputElement | null>;
}

function AskInput({ send, busy, asked, ref }: AskInputProps) {
    const [query, setQuery] = useState('');
    const blocked = busy || query.trim() === '';

    // A key typed outside text fields starts the question
    useStrayKeys(ref, (key) => setQuery((was) => was + key));

    function submit() {
        if (blocked) {
            return;
        }
        send(query);
        setQuery('');
    }

    // Browse past queries
    function browsePastQueries(event: KeyboardEvent<HTMLInputElement>) {
        // This session's queries, then the history
        const queries = [
            ...new Set([...asked.toReversed(), ...readHistory().map((one) => one.query)]),
        ];

        // Which one the box shows
        const shown = queries.indexOf(query);
        if (shown === -1 && query !== '') return;
        event.preventDefault();

        // Up shows older, and down shows newer
        const next = shown + (event.key === 'ArrowUp' ? 1 : -1);
        if (next < -1 || next === queries.length) return;
        setQuery(next === -1 ? '' : queries[next]);
    }

    // Handle input box functions like submit, clear, and past queries
    function handleKey(event: KeyboardEvent<HTMLInputElement>) {
        switch (event.key) {
            case 'Enter':
                submit();
                break;
            case 'Escape':
                if (query === '') event.currentTarget.blur();
                else setQuery('');
                break;
            case 'ArrowUp':
            case 'ArrowDown':
                browsePastQueries(event);
        }
    }

    return (
        <div className="flex items-center gap-2">
            <input
                ref={ref}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={handleKey}
                enterKeyHint="send"
                placeholder="Ask about trips, schedules, or alerts"
                aria-label="Ask a question"
                className="h-13 min-w-0 flex-1 rounded-xl border border-edge bg-field px-4.5 text-sm text-cream transition-colors outline-none placeholder:text-quiet focus:border-accent/40 contrast-more:focus:border-accent pointer-coarse:text-base"
            />
            <button
                type="button"
                onClick={submit}
                disabled={blocked}
                aria-label="Ask"
                className="grid size-13 shrink-0 cursor-pointer place-items-center rounded-xl bg-accent text-onaccent transition-[background-color,opacity,scale] ease-out enabled:hover:bg-bright enabled:active:scale-97 disabled:cursor-default disabled:opacity-30"
            >
                <ArrowUp size={17} strokeWidth={2.2} />
            </button>
        </div>
    );
}

export default AskInput;
