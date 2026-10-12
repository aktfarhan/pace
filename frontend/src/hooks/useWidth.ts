import { useLayoutEffect, useState } from 'react';

// An element's width in pixels
export function useWidth<Target extends HTMLElement>() {
    const [node, setNode] = useState<Target | null>(null);
    const [width, setWidth] = useState(0);

    useLayoutEffect(() => {
        if (node === null) return;

        const measure = (room: number) => setWidth(Math.round(room));

        // Measured once before the first draw
        const style = getComputedStyle(node);
        measure(node.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight));
        const watch = new ResizeObserver(([entry]) => measure(entry.contentRect.width));
        watch.observe(node);

        return () => watch.disconnect();
    }, [node]);

    return [setNode, width] as const;
}
