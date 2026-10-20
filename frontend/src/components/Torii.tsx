import Svg, { Ellipse, Path, Rect } from 'react-native-svg';
import { colors } from '@/theme';

type Props = {
  width: number;
  // The mock test gate gets a gold name plaque, like a shrine's main gate.
  withPlaque?: boolean;
};

// A red torii gate. Quizzes and mock tests appear as gates on the study map.
export function Torii({ width, withPlaque = false }: Props) {
  const height = Math.round(width * 0.94);
  const red = colors.brandRed;
  const black = colors.ink;

  return (
    <Svg width={width} height={height} viewBox="0 0 100 94">
      <Ellipse cx={50} cy={89} rx={42} ry={5} fill={black} opacity={0.12} />
      <Path d="M3 9 Q50 19 97 9 L96 3 Q50 13 4 3 Z" fill={black} />
      <Path d="M6 11 Q50 21 94 11 L93 19 Q50 28 7 19 Z" fill={red} />
      <Rect x={46} y={22} width={8} height={12} fill={red} />
      <Rect x={14} y={33} width={72} height={7} fill={red} />
      <Rect x={22} y={20} width={9} height={64} fill={red} />
      <Rect x={69} y={20} width={9} height={64} fill={red} />
      <Rect x={19} y={82} width={15} height={6} fill={black} />
      <Rect x={66} y={82} width={15} height={6} fill={black} />
      {withPlaque && (
        <Rect x={42} y={20} width={16} height={15} rx={1.5} fill={colors.gold} stroke={black} strokeWidth={1.5} />
      )}
    </Svg>
  );
}
