import Sync from './Sync';
import Keys from './Keys';
import Group from './Group';
import Reset from './Reset';
import { LINK } from './tints';
import General from './General';
import Keeping from './Keeping';
import Sources from './Sources';
import { useState } from 'react';
import { readCode } from '@/lib/pace';
import type { Page } from '@/components/layout/sidebar/tints';

interface SettingsProps {
    go: (page: Page) => void;
}

function Settings({ go }: SettingsProps) {
    const [round, setRound] = useState(0);

    const foot =
        readCode() === null ? (
            <>
                Save a place or trip to get a code.{' '}
                <button type="button" onClick={() => go('Saved')} className={LINK}>
                    Open Saved
                </button>
            </>
        ) : undefined;

    return (
        <div className="@container flex flex-col gap-3.5">
            <h1 className="text-board text-bright">Settings</h1>
            <div className="grid grid-cols-1 gap-x-6 gap-y-3.5 @4xl:grid-cols-2">
                <div className="flex flex-col gap-3.5">
                    <Group label="Sync" foot={foot}>
                        <Sync />
                    </Group>
                    <Group label="General">
                        <General key={round} />
                        <Reset done={() => setRound((one) => one + 1)} />
                    </Group>
                    <Group label="History">
                        <Keeping />
                    </Group>
                </div>
                <div className="flex flex-col gap-3.5">
                    <Group label="Sources">
                        <Sources />
                    </Group>
                    <div className="pointer-coarse:hidden">
                        <Group label="Keyboard">
                            <Keys />
                        </Group>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Settings;
