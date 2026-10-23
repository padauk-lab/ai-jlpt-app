import Svg, { Circle, Defs, G, LinearGradient, Path, Rect, Stop } from 'react-native-svg';

// The Bagan sunrise behind the profile card on Settings: a golden sky, three layers
// of stupas, temples and trees, and on the ground two monks walking and an ox cart.
// Drawn for a 358 x 150 frame; it scales to the card's width.
const FAR = '#C3DAEC';
const MID = '#98C0DF';
const NEAR = '#6FA3CD';
const GROUND = '#2F6496';

export function BaganBanner({ height = 150 }: { height?: number }) {
  return (
    <Svg width="100%" height={height} viewBox="0 0 358 150" preserveAspectRatio="xMidYMax slice" accessibilityLabel="ပုဂံ ရှုခင်း">
      <Defs>
        <LinearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0" stopColor="#F3D3A0" />
          <Stop offset="0.55" stopColor="#FBEBD3" />
          <Stop offset="1" stopColor="#FFFFFF" />
        </LinearGradient>
      </Defs>
      <Rect width={358} height={150} fill="url(#sky)" />
      <G fill="#FFFFFF" opacity={0.8}>
        <Rect x={12} y={18} width={120} height={3} rx={1.5} />
        <Rect x={40} y={26} width={90} height={2.5} rx={1.25} />
        <Rect x={210} y={14} width={130} height={3} rx={1.5} />
        <Rect x={236} y={22} width={80} height={2.5} rx={1.25} />
      </G>
      <Path
        d="M32 40 l3 2 l3 -2 M44 34 l2.5 1.6 l2.5 -1.6 M26 32 l2 1.4 l2 -1.4 M300 36 l3 2 l3 -2 M312 30 l2.5 1.6 l2.5 -1.6"
        stroke="#5E9CC9"
        strokeWidth={1.2}
        strokeLinecap="round"
        fill="none"
      />
      <Path fill={FAR} d="M42.0 112 L42.0 102.0 L47.6 102.0 L47.6 93.0 L53.2 93.0 C53.2 68.0, 63.3 62.0, 66.1 54.0 L70.0 12.0 L73.9 54.0 C76.7 62.0, 86.8 68.0, 86.8 93.0 L92.4 93.0 L92.4 102.0 L98.0 102.0 L98.0 112 Z M166.0 112 L166.0 91.8 L174.4 91.8 L174.4 78.9 L182.8 78.9 L182.8 67.8 L190.0 67.8 L192.4 55.0 L196.0 20.0 L199.6 55.0 L202.0 67.8 L209.2 67.8 L209.2 78.9 L217.6 78.9 L217.6 91.8 L226.0 91.8 L226.0 112 Z M168.1 91.8 L170.2 75.2 L172.3 91.8 Z M219.7 91.8 L221.8 75.2 L223.9 91.8 Z M176.8 78.9 L178.6 64.2 L180.4 78.9 Z M211.6 78.9 L213.4 64.2 L215.2 78.9 Z M277.0 112 L277.0 104.0 L281.6 104.0 L281.6 96.8 L286.2 96.8 C286.2 76.8, 294.5 72.0, 296.8 65.6 L300.0 32.0 L303.2 65.6 C305.5 72.0, 313.8 76.8, 313.8 96.8 L318.4 96.8 L318.4 104.0 L323.0 104.0 L323.0 112 Z M245.0 112 L245.0 107.2 L247.6 107.2 L247.6 102.9 L250.2 102.9 C250.2 90.9, 254.9 88.0, 256.2 84.2 L258.0 64.0 L259.8 84.2 C261.1 88.0, 265.8 90.9, 265.8 102.9 L268.4 102.9 L268.4 107.2 L271.0 107.2 L271.0 112 Z M115.0 112 L115.0 108.0 L117.2 108.0 L117.2 104.4 L119.4 104.4 C119.4 94.4, 123.4 92.0, 124.5 88.8 L126.0 72.0 L127.5 88.8 C128.6 92.0, 132.6 94.4, 132.6 104.4 L134.8 104.4 L134.8 108.0 L137.0 108.0 L137.0 112 Z" />
      <G fill={MID}>
          <Circle key="0" cx={8} cy={108.8} r={8.0} />
          <Circle key="1" cx={13.6} cy={111.2} r={6.0} />
          <Circle key="2" cx={30} cy={106.3} r={10.8} />
          <Circle key="3" cx={37.6} cy={109.5} r={8.1} />
          <Circle key="4" cx={104} cy={107.4} r={9.6} />
          <Circle key="5" cx={110.7} cy={110.2} r={7.2} />
          <Circle key="6" cx={150} cy={108.4} r={8.4} />
          <Circle key="7" cx={155.9} cy={111.0} r={6.3} />
          <Circle key="8" cx={228} cy={105.9} r={11.2} />
          <Circle key="9" cx={235.8} cy={109.3} r={8.4} />
          <Circle key="10" cx={330} cy={107.0} r={10.0} />
          <Circle key="11" cx={337.0} cy={110.0} r={7.5} />
          <Circle key="12" cx={350} cy={108.1} r={8.8} />
          <Circle key="13" cx={356.2} cy={110.7} r={6.6} />
      </G>
      <Path fill={MID} d="M148.0 120 L148.0 113.8 L151.4 113.8 L151.4 108.2 L154.8 108.2 C154.8 92.7, 160.9 89.0, 162.6 84.0 L165.0 58.0 L167.4 84.0 C169.1 89.0, 175.2 92.7, 175.2 108.2 L178.6 108.2 L178.6 113.8 L182.0 113.8 L182.0 120 Z M248.0 120 L248.0 107.7 L253.6 107.7 L253.6 99.8 L259.2 99.8 L259.2 93.1 L264.0 93.1 L265.6 85.3 L268.0 64.0 L270.4 85.3 L272.0 93.1 L276.8 93.1 L276.8 99.8 L282.4 99.8 L282.4 107.7 L288.0 107.7 L288.0 120 Z M249.4 107.7 L250.8 97.6 L252.2 107.7 Z M283.8 107.7 L285.2 97.6 L286.6 107.7 Z M255.2 99.8 L256.4 90.9 L257.6 99.8 Z M278.4 99.8 L279.6 90.9 L280.8 99.8 Z M12.0 120 L12.0 116.2 L14.0 116.2 L14.0 112.8 L16.0 112.8 C16.0 103.3, 19.6 101.0, 20.6 98.0 L22.0 82.0 L23.4 98.0 C24.4 101.0, 28.0 103.3, 28.0 112.8 L30.0 112.8 L30.0 116.2 L32.0 116.2 L32.0 120 Z" />
      <G fill={NEAR}>
          <Circle key="0" cx={20} cy={120.1} r={8.8} />
          <Circle key="1" cx={26.2} cy={122.7} r={6.6} />
          <Circle key="2" cx={58} cy={117.3} r={11.9} />
          <Circle key="3" cx={66.3} cy={120.9} r={8.9} />
          <Circle key="4" cx={92} cy={118.5} r={10.6} />
          <Circle key="5" cx={99.4} cy={121.7} r={7.9} />
          <Circle key="6" cx={130} cy={119.7} r={9.2} />
          <Circle key="7" cx={136.5} cy={122.5} r={6.9} />
          <Circle key="8" cx={190} cy={116.9} r={12.3} />
          <Circle key="9" cx={198.6} cy={120.6} r={9.2} />
          <Circle key="10" cx={226} cy={118.1} r={11.0} />
          <Circle key="11" cx={233.7} cy={121.4} r={8.2} />
          <Circle key="12" cx={300} cy={119.3} r={9.7} />
          <Circle key="13" cx={306.8} cy={122.2} r={7.3} />
          <Circle key="14" cx={340} cy={116.5} r={12.8} />
          <Circle key="15" cx={348.9} cy={120.3} r={9.6} />
      </G>
      <Rect x={0} y={126} width={358} height={24} fill={GROUND} />
      <G fill={GROUND}>
        <Circle cx={40} cy={104} r={2.8} />
        <Path d="M36.5 108 C 37 106, 43 106, 43.5 108 L 45 126 L 35 126 Z" />
        <Circle cx={56} cy={104} r={2.8} />
        <Path d="M52.5 108 C 53 106, 59 106, 59.5 108 L 61 126 L 51 126 Z" />
      </G>
      <Path d="M33 101 L 49 109 M49 101 L 65 109" stroke={GROUND} strokeWidth={2.2} strokeLinecap="round" />
      <G transform="translate(232 98) scale(0.36)" fill={GROUND}>
        <Path d="M58 44 C 60 36, 55 31, 47 31 C 37 30.5, 27 31.5, 21 33 C 18 31, 14 30, 12 31 L 6 37 C 4 39, 5 42, 8 42 C 11 42, 13 41.5, 15 43 C 17 48, 20 52, 25 54 L 50 54.5 C 55 53.5, 58 49.5, 58 44 Z" />
        <Path d="M14 30.5 C 14.8 27.5, 13.5 25.5, 11.5 25.2 M10 31 C 9 28, 7 27, 5.4 27.6" stroke={GROUND} strokeWidth={2} fill="none" strokeLinecap="round" />
        <Path d="M49 53 L 51 72 M25 53 L 23 72 M44 53 L 43 72 M30 53 L 31 72 M58 46 L 95 52" stroke={GROUND} strokeWidth={3.4} strokeLinecap="round" />
        <Circle cx={96} cy={31} r={3.2} />
        <Path d="M90 28 a6 1.6 0 1 0 12 0 a6 1.6 0 1 0 -12 0 Z M92 35 C 94 33.5, 98 33.5, 100 35 L 101 48 L 91 48 Z M90 50 L 150 50 L 150 54 L 90 54 Z" />
        <Path
          d="M100 50 L 98 28 M114 50 L 113 28 M128 50 L 128 28 M142 50 L 143 28 M96 30 L 148 30 M150 50 C 158 46, 160 40, 158 34"
          stroke={GROUND}
          strokeWidth={3}
          strokeLinecap="round"
          fill="none"
        />
        <Circle cx={128} cy={62} r={14} fill="none" stroke={GROUND} strokeWidth={3.6} />
        <Path d="M128 48 L128 76 M114 62 L142 62 M118 52 L138 72 M118 72 L138 52" stroke={GROUND} strokeWidth={2} />
      </G>
    </Svg>
  );
}
