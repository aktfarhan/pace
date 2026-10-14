import Setting from './Setting';
import { useState } from 'react';
import { House } from 'lucide-react';
import Segmented from '@/components/layout/Segmented';
import { STARTS, readStart, writeStart } from '@/lib/prefs';
import type { Start } from '@/lib/prefs';

function General() {
    const [start, setStart] = useState(readStart);

    // Keeps the picked start page
    const choose = (one: Start) => {
        writeStart(one);
        setStart(one);
    };

    return (
        <Setting Icon={House} title="Open Pace on" note="Where you land each time">
            <Segmented label="Open Pace on" options={STARTS} value={start} pick={choose} />
        </Setting>
    );
}

export default General;
