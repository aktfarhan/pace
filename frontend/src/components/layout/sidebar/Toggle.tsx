import { PanelLeft } from 'lucide-react';

interface ToggleProps {
    toggle: () => void;
    expanded: boolean;
}

function Toggle({ toggle, expanded }: ToggleProps) {
    return (
        <button
            type="button"
            onClick={toggle}
            aria-label="Toggle sidebar"
            aria-expanded={expanded}
            className="grid size-11 shrink-0 cursor-pointer place-items-center rounded-row text-faint transition-colors hover:bg-accent/11"
        >
            <PanelLeft size={22} strokeWidth={1.8} />
        </button>
    );
}

export default Toggle;
