import clsx from 'clsx';
import { MapPin } from 'lucide-react';
import { useId, useState } from 'react';
import { useSuggest } from './useSuggest';
import { MENU, RAISED, UNPICKED } from '@/components/layout/tints';
import type { KeyboardEvent, RefObject } from 'react';

const PIN = 'pointer-events-none absolute top-1/2 left-3.5 -translate-y-1/2 text-faint';

// What each kind of match is called in the list
const KINDS: Record<string, string> = {
    address: 'Address',
    street: 'Street',
    station: 'Station',
    neighborhood: 'Area',
    town: 'Town',
};

interface AddressFieldProps {
    value: string;
    change: (value: string) => void;
    fieldRef: RefObject<HTMLInputElement | null>;
    field: string;
    maxLength: number;
}

function AddressField({ value, change, fieldRef, field, maxLength }: AddressFieldProps) {
    const listId = useId();
    const found = useSuggest(value);
    const [focused, setFocused] = useState(false);

    // A pick or Escape hides the list until the next keystroke
    const [hidden, setHidden] = useState(false);
    const [lit, setLit] = useState(-1);

    const open = focused && !hidden && found.length > 0;
    const active = open && lit < found.length ? lit : -1;

    const type = (typed: string) => {
        change(typed);
        setHidden(false);
        setLit(-1);
    };

    const pick = (label: string) => {
        change(label);
        setHidden(true);
        setLit(-1);
    };

    // Arrows walk the list, Return picks, Escape puts it away
    const handleKey = (event: KeyboardEvent<HTMLInputElement>) => {
        if (!open) return;
        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
            const step = event.key === 'ArrowDown' ? 1 : -1;
            const next = active + step;
            setLit(next < -1 ? found.length - 1 : next >= found.length ? -1 : next);
            event.preventDefault();
        } else if (event.key === 'Enter' && active >= 0) {
            pick(found[active].label);
            event.preventDefault();
        } else if (event.key === 'Escape') {
            setHidden(true);
            event.stopPropagation();
        }
    };

    return (
        <span className="relative">
            <MapPin size={14} strokeWidth={2} className={PIN} />
            <input
                ref={fieldRef}
                value={value}
                maxLength={maxLength}
                onChange={(event) => type(event.target.value)}
                onKeyDown={handleKey}
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                role="combobox"
                aria-expanded={open}
                aria-controls={listId}
                aria-autocomplete="list"
                aria-activedescendant={active >= 0 ? `${listId}-${active}` : undefined}
                enterKeyHint="done"
                autoComplete="off"
                placeholder="1 Main Street, Boston"
                className={clsx(field, 'pl-9.5')}
            />
            {open && (
                <span
                    id={listId}
                    role="listbox"
                    className={`${MENU} absolute top-full right-0 left-0 z-10 mt-1.5 flex origin-top flex-col p-1`}
                >
                    {found.map((place, index) => (
                        <span
                            key={place.label}
                            id={`${listId}-${index}`}
                            role="option"
                            aria-selected={index === active}
                            onPointerDown={(event) => event.preventDefault()}
                            onClick={() => pick(place.label)}
                            onPointerEnter={() => setLit(index)}
                            className={clsx(
                                'flex cursor-pointer items-center justify-between gap-3 rounded-chip px-2.5 py-2 text-sm transition ease-out pointer-coarse:py-2.75',
                                index === active ? [RAISED, 'text-cream'] : UNPICKED,
                            )}
                        >
                            <span className="min-w-0 truncate">{place.label}</span>
                            <span className="shrink-0 font-mono text-label text-faint uppercase">
                                {KINDS[place.kind] ?? 'Place'}
                            </span>
                        </span>
                    ))}
                </span>
            )}
        </span>
    );
}

export default AddressField;
