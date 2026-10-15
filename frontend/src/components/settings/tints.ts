// A small bordered pill's look
const PILL =
    'cursor-pointer rounded-full border border-seam bg-field text-soft transition ease-out hover:border-edge hover:text-cream active:scale-97';

// A pill with words
export const BUTTON = `${PILL} flex items-center gap-1.5 px-3 py-1.5 font-mono text-tag uppercase disabled:pointer-events-none disabled:opacity-40`;

// A pill with only an icon
export const ICON_BUTTON = `${PILL} p-2`;

// A link inside a note
export const LINK = 'cursor-pointer text-accent underline-offset-2 hover:underline';

// The shape of a code
export const SHAPE = /^[a-z]+-[a-z]+-[2-9a-hjkmnp-z]{8}$/;

// How long Copied and Done stay (ms)
export const SAID_MS = 1200;
