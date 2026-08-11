import { useState } from 'react';
import { ArrowUp } from 'lucide-react';
import type { AskController } from '@/hooks/useAsk';

interface AskInputProps {
    send: AskController['send'];
    busy: boolean;
}

function AskInput({ send, busy }: AskInputProps) {
    const [query, setQuery] = useState('');
    const blocked = busy || query.trim() === '';

    function submit() {
        if (blocked) {
            return;
        }
        send(query);
        setQuery('');
    }

    return (
        <div className="flex items-center gap-2">
            <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => event.key === 'Enter' && submit()}
                placeholder="Ask about trips, alerts, or parking"
                aria-label="Ask a question"
                className="h-13 min-w-0 flex-1 rounded-xl border border-edge bg-field px-4.5 text-sm text-cream outline-none placeholder:text-faint"
            />
            <button
                type="button"
                onClick={submit}
                disabled={blocked}
                aria-label="Ask"
                className="grid size-13 shrink-0 place-items-center rounded-xl bg-brass text-onbrass disabled:opacity-30"
            >
                <ArrowUp size={17} strokeWidth={2.2} aria-hidden="true" />
            </button>
        </div>
    );
}

export default AskInput;
