import { MapPin } from 'lucide-react';
import type { ChoicesCard, Picked } from '@/types/answer';

const CHIP =
    'relative flex max-w-full cursor-pointer items-center gap-2 rounded-full border border-edge bg-bubble px-3.5 py-2 text-sm text-soft transition-[color,background-color,scale] ease-out hover:bg-line hover:text-cream active:scale-97 pointer-coarse:after:absolute pointer-coarse:after:inset-x-0 pointer-coarse:after:-inset-y-1';

interface ChoicesProps {
    card: ChoicesCard;
    ask: (query: string, pick?: Picked) => void;
}

function Choices({ card, ask }: ChoicesProps) {
    return (
        <div className="flex flex-wrap gap-2 pt-1.5">
            {card.choices.map((choice) => (
                <button
                    key={choice.label}
                    type="button"
                    title={choice.question}
                    onClick={() => ask(choice.question, choice.pick)}
                    className={CHIP}
                >
                    <MapPin size={13} strokeWidth={2} className="shrink-0 text-quiet" />
                    <span className="min-w-0 truncate">{choice.label}</span>
                </button>
            ))}
        </div>
    );
}

export default Choices;
