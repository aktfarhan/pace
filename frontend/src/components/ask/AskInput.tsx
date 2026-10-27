import PlacePill from './PlacePill';
import { placesNamed } from './named';
import { readHistory } from '@/lib/history';
import { ArrowUp, CornerDownLeft } from 'lucide-react';
import { useSavedPlaces } from './useSavedPlaces';
import { useStrayKeys } from '@/hooks/useStrayKeys';
import { setDraft, useDraft } from './useDraft';
import { useEffect, useLayoutEffect } from 'react';
import type { AskController } from './useAsk';
import type { KeyboardEvent, RefObject } from 'react';

const SHOWN_PILLS = 2;

interface AskInputProps {
    send: AskController['send'];
    busy: boolean;
    asked: string[];
    ref: RefObject<HTMLTextAreaElement | null>;
}

// Fits the box to its lines
function fit(box: HTMLTextAreaElement) {
    box.style.height = 'auto';
    box.style.height = `${box.scrollHeight}px`;

    // Typing at the end keeps the last line in full view
    if (box.selectionStart === box.value.length) box.scrollTop = box.scrollHeight;
}

function AskInput({ send, busy, asked, ref }: AskInputProps) {
    const query = useDraft();
    const blocked = busy || query.trim() === '';

    // The saved places the question names
    const named = placesNamed(query, useSavedPlaces());
    const hidden = named.length - SHOWN_PILLS;

    // A key typed outside text fields starts the question
    useStrayKeys(ref, (key) => setDraft(query + key));

    // The box grows with the question
    useLayoutEffect(() => {
        if (ref.current !== null) fit(ref.current);
    }, [ref, query]);

    // A new width can change the line count
    useEffect(() => {
        const refit = () => ref.current !== null && fit(ref.current);
        window.addEventListener('resize', refit);
        return () => window.removeEventListener('resize', refit);
    }, [ref]);

    function submit() {
        if (blocked) {
            return;
        }
        send(query);
        setDraft('');
    }

    // Browse past queries
    function browsePastQueries(event: KeyboardEvent<HTMLTextAreaElement>) {
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
        setDraft(next === -1 ? '' : queries[next]);
    }

    // Handle input box functions like submit, clear, and past queries
    function handleKey(event: KeyboardEvent<HTMLTextAreaElement>) {
        if (event.nativeEvent.isComposing) return;
        switch (event.key) {
            case 'Enter':
                event.preventDefault();
                submit();
                break;
            case 'Escape':
                if (query === '') event.currentTarget.blur();
                else setDraft('');
                break;
            case 'ArrowUp':
            case 'ArrowDown':
                browsePastQueries(event);
        }
    }

    return (
        <div className="flex items-end gap-1.5 rounded-tile border border-line bg-panel pr-2.25 transition-colors ease-out focus-within:border-accent/30 hover:not-focus-within:border-edge contrast-more:focus-within:border-accent">
            <textarea
                ref={ref}
                rows={1}
                value={query}
                onChange={(event) => setDraft(event.target.value.replace(/\s*[\r\n]+\s*/g, ' '))}
                onKeyDown={handleKey}
                enterKeyHint="send"
                placeholder="Ask about trips, schedules, or alerts"
                aria-label="Ask a question"
                className="max-h-29.5 min-w-0 flex-1 resize-none bg-transparent py-2.75 pl-4 text-sm/6 text-cream outline-none placeholder:text-quiet pointer-coarse:max-h-31 pointer-coarse:py-2.5 pointer-coarse:text-base/6.5"
            />
            {named.length > 0 && (
                <span className="mb-2.75 flex shrink-0 items-center gap-1">
                    {named.slice(0, SHOWN_PILLS).map((place) => (
                        <PlacePill key={place.id} place={place} size="box" />
                    ))}
                    {hidden > 0 && <span className="px-0.5 text-clock text-hush">+{hidden}</span>}
                </span>
            )}
            <button
                type="button"
                onClick={submit}
                disabled={blocked}
                aria-label="Ask"
                className="relative mb-2.25 grid h-7 w-7.5 shrink-0 place-items-center rounded-place text-ghost transition-[color,background-color,scale] duration-160 ease-out after:absolute after:-inset-x-1.75 after:-inset-y-2 enabled:cursor-pointer enabled:text-cream enabled:hover:bg-bubble enabled:active:scale-97"
            >
                <CornerDownLeft size={16} strokeWidth={2} className="pointer-coarse:hidden" />
                <ArrowUp size={16} strokeWidth={2} className="hidden pointer-coarse:block" />
            </button>
        </div>
    );
}

export default AskInput;
