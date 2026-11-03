const FOUR_PATH = 'M62 0 L0 92 V116 H62 V140 H90 V116 H100 V92 H90 V0 Z M62 30 V92 H24 Z';

const VIEWBOX_WIDTH = 400;
const FOUR_WIDTH = 100;
const FOUR_OFFSET_Y = 5;

const LEFT_FOUR_X = 0;
const RIGHT_FOUR_X = VIEWBOX_WIDTH - FOUR_WIDTH;

export const NotFoundIllustration = () => (
  <svg
    viewBox="0 0 400 150"
    role="img"
    aria-label="404"
    className="h-auto w-72 sm:w-96"
    xmlns="http://www.w3.org/2000/svg"
  >
    {/* Левая четвёрка */}
    <path
      d={FOUR_PATH}
      transform={`translate(${LEFT_FOUR_X} ${FOUR_OFFSET_Y})`}
      fillRule="evenodd"
      className="fill-foreground"
    />

    {/* Лицо */}
    <circle cx="200" cy="75" r="70" className="fill-primary" />

    {/* Брови */}
    <g className="stroke-foreground" strokeWidth="5" strokeLinecap="round">
      <line x1="163" y1="50" x2="191" y2="46" />
      <line x1="209" y1="56" x2="237" y2="58" />
    </g>

    {/* Глаза */}
    <circle cx="178" cy="76" r="14" className="fill-white" />
    <circle cx="222" cy="76" r="14" className="fill-white" />
    <circle cx="183" cy="71" r="6.5" className="fill-foreground" />
    <circle cx="227" cy="71" r="6.5" className="fill-foreground" />

    {/* Знак вопроса */}
    <g transform="translate(268 36) rotate(10)">
      <path
        d="M-10 -8 C-10 -22 12 -22 12 -8 C12 2 0 4 0 14"
        fill="none"
        strokeWidth="7"
        strokeLinecap="round"
        className="stroke-secondary"
      />
      <circle cx="0" cy="28" r="4" className="fill-secondary" />
    </g>

    {/* Правая четвёрка */}
    <path
      d={FOUR_PATH}
      transform={`translate(${RIGHT_FOUR_X} ${FOUR_OFFSET_Y})`}
      fillRule="evenodd"
      className="fill-foreground"
    />
  </svg>
);
