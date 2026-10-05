// The picked look's copy
export const GLIDE =
    'pointer-events-none absolute inset-0 transition-[clip-path] duration-200 ease-out motion-reduce:transition-none';

// A status dot
export const LIVE = 'bg-good shadow-glow';
export const BEHIND = 'animate-beacon bg-amber shadow-pulse';

// A tile or chip no line tints
export const UNTINTED = 'border-line bg-bubble text-muted';

// Changed text fades in from a slight blur
export const TICK =
    'transition-[opacity,filter] duration-200 ease-out starting:opacity-0 starting:blur-xs';

// A count's pill
export const COUNT =
    'rounded-full bg-field px-1.75 py-px font-mono text-heading tracking-normal text-hush tabular-nums';

// The picked look
export const RAISED =
    'bg-edge/80 shadow-xs shadow-black/40 inset-ring inset-ring-white/8 contrast-more:inset-ring-white/40';

// The background of a switch
export const TRACK =
    'rounded-full bg-ink/45 inset-ring inset-ring-white/6 contrast-more:inset-ring-white/30';

// A round pill button
export const BUBBLE =
    'relative flex cursor-pointer items-center rounded-full border border-edge bg-bubble transition ease-out hover:border-ghost hover:bg-line hover:text-cream active:scale-96 pointer-coarse:after:absolute pointer-coarse:after:inset-x-0 pointer-coarse:after:-inset-y-2';

// The "Live · 12s ago" refresh button
export const STAMP = `${BUBBLE} shrink-0 gap-2 px-3.25 py-1.75 text-hush`;
