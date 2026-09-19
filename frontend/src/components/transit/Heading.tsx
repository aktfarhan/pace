import { CHIP } from './tints';

interface HeadingProps {
    late: number;
    stretched: boolean;
    tight: boolean;
}

function Heading({ late, stretched, tight }: HeadingProps) {
    return (
        <span className={`${CHIP} w-fit text-hush`}>
            {tight
                ? `${late}+ minutes late`
                : `Arrivals over ${late} minutes late · rolling ${stretched ? 'window' : 'hour'}`}
        </span>
    );
}

export default Heading;
