import { useRef } from 'react';
import { Search, X } from 'lucide-react';
import { useStrayKeys } from '@/hooks/useStrayKeys';
import type { KeyboardEvent } from 'react';

interface FindProps {
    asked: string;
    search: (asked: string) => void;
    label: string;
}

function Find({ asked, search, label }: FindProps) {
    const boxRef = useRef<HTMLInputElement>(null);

    const clear = () => {
        search('');
        boxRef.current?.focus();
    };

    // Escape empties the search, then closes focus
    const handleKey = (event: KeyboardEvent<HTMLInputElement>) => {
        if (event.key !== 'Escape') return;
        if (asked === '') event.currentTarget.blur();
        else search('');
    };

    // Typing outside a text field starts a search
    useStrayKeys(boxRef, (key) => search(asked + key));

    return (
        <div className="flex w-64 shrink-0 items-center gap-2.25 self-center rounded-full border border-seam bg-rail px-3.5 py-1.5 transition-colors focus-within:border-accent/35 focus-within:bg-field">
            <Search size={14} strokeWidth={2} className="shrink-0 text-faint" />
            <input
                ref={boxRef}
                value={asked}
                onChange={(event) => search(event.target.value)}
                onKeyDown={handleKey}
                placeholder={label}
                aria-label={label}
                enterKeyHint="search"
                className="min-w-0 flex-1 bg-transparent text-branch text-bright outline-none placeholder:text-quiet pointer-coarse:text-base"
            />
            {asked !== '' && (
                <button
                    type="button"
                    onClick={clear}
                    aria-label="Clear search"
                    className="-m-1.5 shrink-0 cursor-pointer rounded-full p-1.5 text-ghost transition ease-out hover:bg-line hover:text-cream active:scale-96"
                >
                    <X size={14} strokeWidth={2.2} />
                </button>
            )}
        </div>
    );
}

export default Find;
