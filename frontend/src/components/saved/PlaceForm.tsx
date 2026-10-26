import { X } from 'lucide-react';
import Presets from './Presets';
import AddressField from './AddressField';
import { useRef, useState } from 'react';
import PlaceActions from './PlaceActions';
import type { KeyboardEvent, SubmitEvent } from 'react';
import type { Suggestion } from '@/types/place';

const LABEL = 'font-mono text-label text-faint uppercase';

const FIELD =
    'h-10 w-full rounded-xl border border-edge bg-field px-3.5 text-sm text-cream transition-colors outline-none placeholder:text-quiet focus:border-accent/40 contrast-more:focus:border-accent pointer-coarse:text-base';

// The lengths the server accepts
const MAX_LABEL = 60;
const MAX_ADDRESS = 200;

interface PlaceFormProps {
    keep: (label: string, address: string, spot: Suggestion | null) => Promise<void>;
    close: () => void;
}

function PlaceForm({ keep, close }: PlaceFormProps) {
    const [label, setLabel] = useState('');
    const [address, setAddress] = useState('');
    const [spot, setSpot] = useState<Suggestion | null>(null);
    const [saving, setSaving] = useState(false);
    const [failed, setFailed] = useState(false);
    const addressRef = useRef<HTMLInputElement>(null);

    const ready = label.trim() !== '' && address.trim() !== '';

    const save = async (event: SubmitEvent<HTMLFormElement>) => {
        event.preventDefault();
        setSaving(true);
        setFailed(false);
        try {
            await keep(label.trim(), address.trim(), spot);
            close();
        } catch (error) {
            console.error(error);
            setFailed(true);
            setSaving(false);
        }
    };

    // Escape closes the form
    const handleKey = (event: KeyboardEvent<HTMLFormElement>) => {
        if (event.key === 'Escape' && !saving) close();
    };

    // A picked suggestion keeps its spot until the address is typed over
    const changeAddress = (value: string, picked?: Suggestion) => {
        setAddress(value);
        setSpot(picked ?? null);
    };

    // A preset fills the name and moves on to the address
    const choose = (name: string) => {
        setLabel(name);
        addressRef.current?.focus();
    };

    // Return key in the name moves on to the address
    const next = (event: KeyboardEvent<HTMLInputElement>) => {
        if (event.key !== 'Enter') return;
        event.preventDefault();
        addressRef.current?.focus();
    };

    return (
        <form
            onSubmit={save}
            onKeyDown={handleKey}
            className="col-span-full flex flex-col gap-4 rounded-tile border border-edge bg-panel p-5 transition duration-200 ease-out starting:translate-y-1 starting:opacity-0 motion-reduce:starting:translate-y-0"
        >
            <div className="flex items-center justify-between gap-4">
                <span className="text-title text-bright">New place</span>
                <button
                    type="button"
                    onClick={close}
                    disabled={saving}
                    aria-label="Close"
                    className="grid size-8 cursor-pointer place-items-center rounded-full text-ghost transition ease-out hover:bg-line hover:text-cream active:scale-96 disabled:cursor-default"
                >
                    <X size={15} strokeWidth={2.2} />
                </button>
            </div>

            <Presets label={label} pick={choose} />

            <div className="grid gap-3 sm:grid-cols-3">
                <label className="flex flex-col gap-1.5">
                    <span className={LABEL}>Name</span>
                    <input
                        autoFocus
                        value={label}
                        maxLength={MAX_LABEL}
                        onChange={(event) => setLabel(event.target.value)}
                        onKeyDown={next}
                        enterKeyHint="next"
                        autoComplete="off"
                        autoCapitalize="words"
                        placeholder="Or type any name"
                        className={FIELD}
                    />
                </label>
                <label className="flex flex-col gap-1.5 sm:col-span-2">
                    <span className={LABEL}>Address</span>
                    <AddressField
                        value={address}
                        change={changeAddress}
                        fieldRef={addressRef}
                        field={FIELD}
                        maxLength={MAX_ADDRESS}
                    />
                </label>
            </div>
            <PlaceActions failed={failed} saving={saving} ready={ready} close={close} />
        </form>
    );
}

export default PlaceForm;
