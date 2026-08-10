import { useState } from 'react';
import { ArrowUp } from 'lucide-react';
import type { AskController } from '@/hooks/useAsk';

interface AskInputProps {
    send: AskController['send'];
    busy: boolean;
}

function AskInput({ send, busy }: AskInputProps) {
    const [query, setQuery] = useState('');

    function submit() {
        send(query);
        setQuery('');
    }

    return (
        <div className="flex items-center gap-2">
            <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => event.key === 'Enter' && submit()}
                disabled={busy}
                placeholder="Ask about trips, alerts, or parking"
                aria-label="Ask a question"
                className="h-11 min-w-0 flex-1 rounded-xl border border-edge bg-field px-4 text-sm text-cream outline-none placeholder:text-faint disabled:opacity-50"
            />
            <button
                type="button"
                onClick={submit}
                disabled={busy || query.trim() === ''}
                aria-label="Ask"
                className="grid size-11 shrink-0 place-items-center rounded-xl bg-brass text-onbrass disabled:opacity-30"
            >
                <ArrowUp size={17} strokeWidth={2.2} aria-hidden="true" />
            </button>
        </div>
    );
}

export default AskInput;
