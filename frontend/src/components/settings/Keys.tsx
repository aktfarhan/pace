import Setting from './Setting';
import { KEYED } from '@/lib/keys';
import { Eraser, History, Keyboard } from 'lucide-react';

// A key drawn as a keycap
const CAP =
    'grid h-6 min-w-6 place-items-center rounded-mark border border-edge bg-field px-1.5 font-mono text-tag text-soft shadow-card';

// Each page and the key that opens it
const PAGES = KEYED.map((page, index) => ({ page, key: String(index + 1) }));

// The page keys
const ORDER = PAGES.map(({ page, key }) => `${key} ${page}`).join(' · ');

function Keys() {
    return (
        <>
            <Setting
                Icon={History}
                title="Navigate past questions"
                note="From an empty question box"
            >
                <div className="flex gap-1">
                    <kbd className={CAP}>↑</kbd>
                    <kbd className={CAP}>↓</kbd>
                </div>
            </Setting>
            <Setting Icon={Eraser} title="Clear the box" note="In the question or search box">
                <kbd className={CAP}>esc</kbd>
            </Setting>
            <Setting Icon={Keyboard} title="Pages" note={ORDER}>
                <div className="flex gap-1">
                    {PAGES.map(({ page, key }) => (
                        <kbd key={page} className={CAP}>
                            {key}
                        </kbd>
                    ))}
                </div>
            </Setting>
        </>
    );
}

export default Keys;
