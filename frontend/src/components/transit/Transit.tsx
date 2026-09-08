import Tabs from './Tabs';
import { useState } from 'react';
import type { Tab } from './tints';

function Transit() {
    const [tab, setTab] = useState<Tab>('All');

    return (
        <div className="flex min-w-0 flex-col gap-4.5">
            <div className="text-board text-bright">Transit</div>
            <Tabs tab={tab} select={setTab} />
        </div>
    );
}

export default Transit;
