import { readCode } from '@/lib/pace';
import { useRef, useState } from 'react';

function Code() {
    const code = readCode();
    const timerRef = useRef(0);
    const [copied, setCopied] = useState(false);

    if (code === null) return null;

    // Copies the code to the clipboard
    const copy = async () => {
        try {
            await navigator.clipboard.writeText(code);
            setCopied(true);
            clearTimeout(timerRef.current);
            timerRef.current = setTimeout(() => setCopied(false), 1000);
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <button
            type="button"
            onClick={copy}
            className="w-fit cursor-pointer font-mono text-row text-hush"
        >
            {copied ? 'Copied' : code}
        </button>
    );
}

export default Code;
