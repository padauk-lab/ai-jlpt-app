import Svg, { Circle, G, Line, Path, Rect } from 'react-native-svg';

type Props = {
  size?: number;
};

// The 急合 logo: a red torii gate in front of a yellow sun.
export function Logo({ size = 70 }: Props) {
  return (
    <Svg width={size} height={size} viewBox="0 0 200 200" accessibilityLabel="急合 logo">
      <G opacity={0.65} stroke="#FDE047" strokeWidth={4.5} strokeLinecap="round">
        <Line x1={100} y1={5} x2={100} y2={28} />
        <Line x1={100} y1={172} x2={100} y2={195} />
        <Line x1={5} y1={100} x2={28} y2={100} />
        <Line x1={172} y1={100} x2={195} y2={100} />
        <Line x1={26} y1={26} x2={44} y2={44} />
        <Line x1={156} y1={156} x2={174} y2={174} />
        <Line x1={26} y1={174} x2={44} y2={156} />
        <Line x1={156} y1={44} x2={174} y2={26} />
      </G>
      <Circle cx={100} cy={100} r={62} fill="#FFFBEB" />
      <Circle cx={100} cy={100} r={48} fill="#FEF08A" />
      <Circle cx={100} cy={100} r={34} fill="#FDE047" />
      <G fill="#C8102E">
        <Path d="M 15 75 Q 100 90 185 75 L 180 58 Q 100 73 20 58 Z" fill="#D32F2F" />
        <Path d="M 10 59 Q 100 75 190 59 C 195 50, 185 45, 175 48 Q 100 63 25 48 C 15 45, 5 50, 10 59 Z" />
        <Rect x={30} y={90} width={140} height={10} />
        <Rect x={94} y={68} width={12} height={23} />
        <Rect x={48} y={70} width={14} height={115} />
        <Rect x={138} y={70} width={14} height={115} />
        <Rect x={36} y={112} width={6} height={73} />
        <Rect x={64} y={112} width={6} height={73} />
        <Rect x={130} y={112} width={6} height={73} />
        <Rect x={158} y={112} width={6} height={73} />
        <Rect x={36} y={112} width={34} height={5} />
        <Rect x={130} y={112} width={34} height={5} />
        <Rect x={36} y={152} width={34} height={5} />
        <Rect x={130} y={152} width={34} height={5} />
      </G>
    </Svg>
  );
}
