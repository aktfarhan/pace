import { Briefcase, Dumbbell, GraduationCap, Heart, House, MapPin } from 'lucide-react';

// Presets for saved places
export const PRESETS = [
    { name: 'Home', Icon: House },
    { name: 'Work', Icon: Briefcase },
    { name: 'School', Icon: GraduationCap },
    { name: 'Gym', Icon: Dumbbell },
    { name: 'Family', Icon: Heart },
];

// Any other name
const PLACE = { Icon: MapPin };

// The kind of a place
export function kindOf(label: string) {
    const named = label.toLowerCase();
    return PRESETS.find((one) => one.name.toLowerCase() === named) ?? PLACE;
}
