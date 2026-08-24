import SectionHeading from '@/components/layout/sidebar/SectionHeading';

function Saved() {
    return (
        <div className="flex flex-col gap-3.5">
            <span className="text-board text-bright">Saved</span>

            <div>
                <SectionHeading label="Places" />
                <p className="px-0.5 text-row text-dim">No places saved.</p>
            </div>
        </div>
    );
}

export default Saved;
