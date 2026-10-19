import Svg, { Defs, Ellipse, G, Path, Rect, Symbol as SvgSymbol, Use } from 'react-native-svg';

// The Bagan plain behind the study map: stupas, temples, sugar palms,
// the Ayeyarwady river and a hot-air balloon. Drawn faded so the path stays clear.
// It is drawn in a 390 x 1000 frame, the same frame the map uses.
export const MAP_WIDTH = 390;
export const MAP_HEIGHT = 1000;

export function BaganBackground() {
  return (
    <Svg width={MAP_WIDTH} height={MAP_HEIGHT} viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`}>
      <Defs>
        <SvgSymbol id="stupa" viewBox="0 0 40 60">
          <Path d="M20 0 L22.5 15 L17.5 15 Z" />
          <Rect x={15} y={15} width={10} height={4} />
          <Path d="M8 40 C8 27 14 20 20 20 C26 20 32 27 32 40 Z" />
          <Rect x={5} y={40} width={30} height={6} />
          <Rect x={2} y={46} width={36} height={7} />
          <Rect x={0} y={53} width={40} height={7} />
        </SvgSymbol>
        <SvgSymbol id="temple" viewBox="0 0 80 64">
          <Path d="M40 0 L44 17 L36 17 Z" />
          <Path d="M30 34 C30 23 35 17 40 17 C45 17 50 23 50 34 Z" />
          <Path d="M17 34 L20.5 24 L24 34 Z" />
          <Path d="M56 34 L59.5 24 L63 34 Z" />
          <Rect x={14} y={34} width={52} height={8} />
          <Rect x={8} y={42} width={64} height={10} />
          <Rect x={2} y={52} width={76} height={12} />
        </SvgSymbol>
        <SvgSymbol id="palm" viewBox="0 0 30 60">
          <Path d="M15 58 L15 20" strokeWidth={2.4} />
          <Path
            d="M15 20 Q8 12 1 15 M15 20 Q22 12 29 15 M15 20 Q10 8 5 3 M15 20 Q20 8 25 3 M15 20 L15 1 M15 20 Q6 18 2 24 M15 20 Q24 18 28 24"
            strokeWidth={2}
          />
        </SvgSymbol>
      </Defs>

      <Path d="M-30 1000 C 40 930, -10 860, 34 790 S 0 660, -30 610" stroke="#CFE0E1" strokeWidth={46} strokeLinecap="round" fill="none" />

      <G fill="#E8DCC0">
        <Ellipse cx={330} cy={905} rx={70} ry={34} />
        <Ellipse cx={60} cy={470} rx={64} ry={40} />
        <Ellipse cx={340} cy={420} rx={58} ry={30} />
      </G>
      <G fill="#DCE2C2">
        <Ellipse cx={110} cy={700} rx={48} ry={26} />
        <Ellipse cx={330} cy={140} rx={60} ry={32} />
        <Ellipse cx={60} cy={250} rx={46} ry={24} />
      </G>

      <G fill="#C9895A" opacity={0.5}>
        <Use href="#stupa" x={60} y={860} width={34} height={51} />
        <Use href="#stupa" x={330} y={950} width={26} height={39} />
        <Use href="#stupa" x={120} y={745} width={22} height={33} />
        <Use href="#stupa" x={320} y={575} width={30} height={45} />
        <Use href="#stupa" x={20} y={355} width={30} height={45} />
        <Use href="#stupa" x={88} y={290} width={22} height={33} />
        <Use href="#stupa" x={330} y={60} width={30} height={45} />
        <Use href="#stupa" x={350} y={300} width={24} height={36} />
      </G>
      <G fill="#B9744A" opacity={0.45}>
        <Use href="#temple" x={44} y={770} width={74} height={59} />
        <Use href="#temple" x={280} y={490} width={86} height={69} />
        <Use href="#temple" x={18} y={185} width={70} height={56} />
        <Use href="#temple" x={250} y={955} width={56} height={45} />
      </G>
      <G stroke="#7E8A5A" fill="none" strokeLinecap="round" opacity={0.6}>
        <Use href="#palm" x={352} y={610} width={24} height={48} />
        <Use href="#palm" x={96} y={845} width={20} height={40} />
        <Use href="#palm" x={54} y={300} width={22} height={44} />
        <Use href="#palm" x={342} y={245} width={20} height={40} />
      </G>

      <G opacity={0.55}>
        <Path d="M352 6 C 338 6, 332 18, 336 28 C 339 36, 346 40, 349 44 L 355 44 C 358 40, 365 36, 368 28 C 372 18, 366 6, 352 6 Z" fill="#D9A441" />
        <Path d="M344 12 Q352 26 352 44 M360 12 Q352 26 352 44" stroke="#B9744A" strokeWidth={1.2} fill="none" />
        <Rect x={348} y={48} width={8} height={6} rx={1} fill="#8A5A33" />
      </G>
    </Svg>
  );
}
