import Hold from './Hold';
import Switch from './Switch';
import Setting from './Setting';
import { useKeeps } from '@/hooks/useKeeps';
import { writeKeepsHistory } from '@/lib/prefs';
import { useId, useSyncExternalStore } from 'react';
import { Archive, Clock, Pause } from 'lucide-react';
import { clearHistory, countHistory, onHistory } from '@/lib/history';

function Keeping() {
    const keeps = useKeeps();
    const kept = useSyncExternalStore(onHistory, countHistory);
    const noteId = useId();

    return (
        <>
            <Setting
                Icon={keeps ? Clock : Pause}
                title="Keep questions"
                noteId={noteId}
                note={keeps ? 'Each question is saved' : "Paused: new questions aren't saved"}
            >
                <Switch
                    on={keeps}
                    label="Keep questions"
                    described={noteId}
                    flip={writeKeepsHistory}
                />
            </Setting>
            <Setting Icon={Archive} title="Questions on this device" note="Never synced">
                <div className="flex items-center gap-2.5">
                    <span className="font-mono text-tag text-soft tabular-nums">
                        {kept === 0 ? 'None' : kept}
                    </span>
                    {kept > 0 && <Hold label="Hold to clear" done={clearHistory} />}
                </div>
            </Setting>
        </>
    );
}

export default Keeping;
