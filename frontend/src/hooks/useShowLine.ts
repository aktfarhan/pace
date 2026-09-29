import { createContext, useContext } from 'react';

// Opens Transit on one line
export const ShowLine = createContext<(lineId: string) => void>(() => {});

export function useShowLine() {
    return useContext(ShowLine);
}
