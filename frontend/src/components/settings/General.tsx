import Setting from './Setting';
import { useState } from 'react';
import LineMenu from './LineMenu';
import { House, TrainFront } from 'lucide-react';
import Segmented from '@/components/layout/Segmented';
import { STARTS, readLine, readStart, writeLine, writeStart } from '@/lib/prefs';
import type { Start } from '@/lib/prefs';
import type { Tab } from '@/components/transit/tints';

function General() {
    const [start, setStart] = useState(readStart);
    const [line, setLine] = useState(readLine);

    // Keeps the picked start page
    const chooseStart = (one: Start) => {
        writeStart(one);
        setStart(one);
    };

    // Keeps the picked Transit tab
    const chooseLine = (one: Tab) => {
        writeLine(one);
        setLine(one);
    };

    return (
        <>
            <Setting Icon={House} title="Open Pace on" note="Where you land each time">
                <Segmented label="Open Pace on" options={STARTS} value={start} pick={chooseStart} />
            </Setting>
            <Setting Icon={TrainFront} title="Transit opens on" note="Your usual line">
                <LineMenu value={line} pick={chooseLine} />
            </Setting>
        </>
    );
}

export default General;
