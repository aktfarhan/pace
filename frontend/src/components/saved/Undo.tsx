import { useId } from 'react';
import { Undo2 } from 'lucide-react';
import { UNDO_MS } from '@/hooks/useUndo';
import { BUBBLE } from '@/components/layout/tints';

interface UndoProps {
    said: string;
    undo: (() => void) | null;
}

function Undo({ said, undo }: UndoProps) {
    const id = useId();

    return (
        <div
            role="status"
            className="flex min-w-0 flex-1 items-center gap-3 transition-opacity ease-out starting:opacity-0"
        >
            <span id={id} className="min-w-0 flex-1 truncate text-row text-soft">
                {said}
            </span>
            {undo !== null && (
                <button
                    type="button"
                    autoFocus
                    aria-describedby={id}
                    onClick={(event) => event.detail < 2 && undo()}
                    className={`${BUBBLE} -mr-1.5 shrink-0 gap-2 px-3.25 py-1.5 text-soft`}
                >
                    <span
                        aria-hidden="true"
                        className="absolute inset-0 overflow-hidden rounded-full"
                    >
                        <span
                            style={{ transitionDuration: `${UNDO_MS}ms` }}
                            className="absolute inset-0 origin-left scale-x-0 bg-white/7 transition-transform ease-linear starting:scale-x-100"
                        />
                    </span>
                    <Undo2 size={12} strokeWidth={2.4} className="relative" />
                    <span className="relative font-mono text-stamp uppercase">Undo</span>
                </button>
            )}
        </div>
    );
}

export default Undo;
