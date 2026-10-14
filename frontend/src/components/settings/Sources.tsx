import Setting from './Setting';
import { POLL_MS } from '@/lib/poll';
import { KINDS } from '@/components/history/tints';
import { ALERTS, PLANNER, TIMETABLE } from '@/lib/sources';

// Where answers come from
const SOURCES = [
    { look: KINDS.route, title: 'Trips', note: PLANNER },
    {
        look: KINDS.alert,
        title: 'Alerts and line status',
        note: `${ALERTS}, checked every ${POLL_MS / 1000} seconds`,
    },
    { look: KINDS.schedule, title: 'Timetables', note: TIMETABLE },
];

function Sources() {
    return SOURCES.map(({ look, title, note }) => (
        <Setting key={title} Icon={look.Icon} tile={look.tile} title={title} note={note} />
    ));
}

export default Sources;
