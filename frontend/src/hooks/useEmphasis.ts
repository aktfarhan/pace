import { useState } from 'react';

// How far back a line sits while others are picked
const ASIDE = 0.1;

// How far back it sits while another is led
const BEHIND = 0.3;

// Which line the chart leans toward, and how far back the rest sit
export function useEmphasis(shown: string, near: string | null) {
    const [forLines, setForLines] = useState(shown);
    const [picked, setPicked] = useState<Set<string>>(new Set());
    const [lit, setLit] = useState<string | null>(null);

    // Show only the selected lines
    if (forLines !== shown) {
        setForLines(shown);
        setPicked(new Set());
        setLit(null);
    }

    // A chip under the cursor leads
    const lead = lit ?? near;

    // Picking holds lines up
    const strengthOf = (id: string) => {
        if (picked.size > 0) return picked.has(id) ? 1 : ASIDE;
        if (lead === null || lead === id) return 1;
        return BEHIND;
    };

    // Whichever line the pointer or the keyboard is on
    const light = (id: string | null) => setLit(id);

    // Picking a line already held lets it go
    const toggle = (id: string) =>
        setPicked((held) => {
            const next = new Set(held);
            if (!next.delete(id)) next.add(id);
            return next;
        });

    return { picked, lead, strengthOf, toggle, light };
}

export type Emphasis = ReturnType<typeof useEmphasis>;
