import Svg, { Circle, G, Path, Rect } from 'react-native-svg';

// A palm-leaf manuscript (ပေစာ) with a stylus (ကညစ်) beside it,
// leaning at 75 degrees with the point down. Used on the quiz progress bar.
export function PalmLeafStylus({ width = 46 }: { width?: number }) {
  const height = Math.round((width * 34) / 46);
  return (
    <Svg width={width} height={height} viewBox="0 -4 46 34">
      <Rect x={1} y={21} width={30} height={5} rx={2.5} fill="#6B2E1A" />
      <Rect x={2} y={17.5} width={28} height={4} rx={2} fill="#EAD6A2" stroke="#8A6A2E" strokeWidth={1} />
      <Rect x={2} y={14} width={28} height={4} rx={2} fill="#F1E1B6" stroke="#8A6A2E" strokeWidth={1} />
      <Rect x={1} y={11.2} width={30} height={3.4} rx={1.7} fill="#6B2E1A" />
      <Circle cx={9} cy={18} r={1.1} fill="#8A6A2E" />
      <Circle cx={23} cy={18} r={1.1} fill="#8A6A2E" />
      <Path d="M12 16 L 15 16 M16.5 16 L 21 16" stroke="#5B4A3A" strokeWidth={0.9} strokeLinecap="round" />
      <G>
        <Path d="M35.37 21.98 L37.28 16.79 L39.40 9.08 L40.50 4.20 L37.41 3.37 L35.92 8.15 L33.90 15.89 L32.96 21.33 Z" fill="#5B4A3A" />
        <Path d="M33.00 26.00 L35.37 21.98 L32.96 21.33 L33.00 26.00 Z" fill="#8A9096" />
        <Path d="M40.33 6.74 L36.28 5.66" stroke="#D9A441" strokeWidth={1.5} strokeLinecap="round" />
        <Circle cx={39.47} cy={1.85} r={2.5} fill="#D9A441" />
      </G>
    </Svg>
  );
}
