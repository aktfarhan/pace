import { useRef } from 'react';
import { Search, X } from 'lucide-react';

interface FindProps {
    asked: string;
    ask: (asked: string) => void;
}

function Find({ asked, ask }: FindProps) {
    const boxRef = useRef<HTMLInputElement>(null);

    const clear = () => {
        ask('');
        boxRef.current?.focus();
    };

    return (
        <div className="flex w-64 shrink-0 items-center gap-2.25 self-center rounded-full border border-seam bg-rail px-3.5 py-1.5 focus-within:border-edge focus-within:bg-field">
            <Search size={14} strokeWidth={2} aria-hidden="true" className="shrink-0 text-faint" />
            <input
                ref={boxRef}
                value={asked}
                onChange={(event) => ask(event.target.value)}
                placeholder="Search alerts"
                className="min-w-0 flex-1 bg-transparent text-branch text-bright outline-none placeholder:text-ghost"
            />
            {asked !== '' && (
                <button
                    type="button"
                    onClick={clear}
                    className="shrink-0 cursor-pointer text-ghost transition-colors hover:text-cream"
                >
                    <X size={14} strokeWidth={2.2} aria-hidden="true" />
                </button>
            )}
        </div>
    );
}

export default Find;
