import Svg, { Circle, Ellipse, Path, Rect } from 'react-native-svg';
import { colors } from '@/theme';

const ROPE = { base: '#B48A45', twist: '#E6CB8E' };

function Rope({ d }: { d: string }) {
  return (
    <>
      <Path d={d} stroke={ROPE.base} strokeWidth={5.5} strokeLinecap="round" fill="none" />
      <Path d={d} stroke={ROPE.twist} strokeWidth={5.5} strokeDasharray="2.2 3" fill="none" />
    </>
  );
}

function Shide({ x, y }: { x: number; y: number }) {
  return (
    <Path
      transform={`translate(${x} ${y})`}
      d="M0 0 l3.2 0 l-1.6 3.4 l3.2 0 l-1.6 3.4 l3.2 0 l-3.4 4.2 l1.4 -3.2 l-3.2 0 l1.6 -3.4 l-3.2 0 Z"
      fill="#FFFFFF"
      stroke="#B8A57A"
      strokeWidth={0.7}
      strokeLinejoin="round"
    />
  );
}

// The quiz gate on the result screen. Not passed: the shrine rope is tied
// across it. Passed: the rope is untied and the way through is open.
export function ResultGate({ open, size = 92 }: { open: boolean; size?: number }) {
  const red = colors.brandRed;
  const black = colors.ink;
  return (
    <Svg
      width={size}
      height={Math.round(size * 0.94)}
      viewBox="0 0 100 94"
      accessibilityLabel={open ? 'ကြိုးဖြေပြီးသော တိုရီး တံခါး' : 'ကြိုးချည်ထားဆဲ တိုရီး တံခါး'}
    >
      <Ellipse cx={50} cy={89} rx={42} ry={5} fill={black} opacity={0.12} />
      <Path d="M3 9 Q50 19 97 9 L96 3 Q50 13 4 3 Z" fill={black} />
      <Path d="M6 11 Q50 21 94 11 L93 19 Q50 28 7 19 Z" fill={red} />
      <Rect x={46} y={22} width={8} height={12} fill={red} />
      <Rect x={14} y={33} width={72} height={7} fill={red} />
      <Rect x={22} y={20} width={9} height={64} fill={red} />
      <Rect x={69} y={20} width={9} height={64} fill={red} />
      <Rect x={19} y={82} width={15} height={6} fill={black} />
      <Rect x={66} y={82} width={15} height={6} fill={black} />
      {open ? (
        <>
          <Rope d="M26.5 47 C 33 53, 33 62, 29 70 C 26 76, 31 80, 33 82" />
          <Circle cx={26.5} cy={47} r={3.4} fill={ROPE.base} />
          <Shide x={31.5} y={57} />
        </>
      ) : (
        <>
          <Rope d="M26.5 47 Q50 57 73.5 47" />
          <Circle cx={26.5} cy={47} r={3.4} fill={ROPE.base} />
          <Circle cx={73.5} cy={47} r={3.4} fill={ROPE.base} />
          <Shide x={36} y={51.5} />
          <Shide x={48.4} y={53.6} />
          <Shide x={60.8} y={51.5} />
        </>
      )}
    </Svg>
  );
}
