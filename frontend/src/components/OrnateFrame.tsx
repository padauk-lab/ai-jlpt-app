import { StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, G, Path } from 'react-native-svg';
import { fonts } from '@/theme';

type Props = {
  label: string;
  width?: number; // height follows the frame's shape (196 x 60)
};

const GOLD = '#B8913A';

// One end of the frame. The top scroll meets the top line (y 8), the bottom
// scroll meets the bottom line (y 52), and the leaf sits in the middle (y 30).
function Flourish() {
  return (
    <>
      <Path d="M30 8 C 21 8, 16 12, 16 17 C 16 21.5, 21 22.5, 23 19.5 C 24.8 16.8, 22.6 14.2, 20.4 15.6" stroke={GOLD} strokeWidth={1.8} fill="none" strokeLinecap="round" />
      <G transform="translate(0 10)">
        <Path d="M30 42 C 21 42, 16 38, 16 33 C 16 28.5, 21 27.5, 23 30.5 C 24.8 33.2, 22.6 35.8, 20.4 34.4" stroke={GOLD} strokeWidth={1.8} fill="none" strokeLinecap="round" />
      </G>
      <G transform="translate(0 5)">
        <Path d="M2 25 C 8 21, 14 21, 21 25 C 14 29, 8 29, 2 25 Z" fill={GOLD} />
        <Path d="M21 25 C 23 21.5, 27.5 21.5, 28.5 25 C 27.5 28.5, 23 28.5, 21 25 Z" fill="none" stroke={GOLD} strokeWidth={1.5} />
        <Circle cx={31.5} cy={25} r={1.6} fill={GOLD} />
      </G>
    </>
  );
}

// A gold ornamental title frame (double line, dotted line, scroll flourishes),
// used for "အပိုင်း ၃" on Home and "ယူနစ် ၅" on the unit screen.
export function OrnateFrame({ label, width = 236 }: Props) {
  const height = Math.round((width * 60) / 196);
  // Burmese letters are tall (marks above and below), so the text is kept
  // smaller than the frame and given a generous line height. On iPhone, a line
  // height that is too small cuts off the top of the letters.
  const fontSize = Math.max(13, Math.round(width / 15));

  return (
    <View style={[styles.box, { width, height }]}>
      <Svg width={width} height={height} viewBox="0 0 196 60" style={StyleSheet.absoluteFill}>
        <Path d="M34 8 L162 8 M34 52 L162 52" stroke={GOLD} strokeWidth={2.2} strokeLinecap="round" />
        <Path d="M38 13 L158 13 M38 47 L158 47" stroke={GOLD} strokeWidth={1.6} strokeLinecap="round" strokeDasharray="0.1 3.4" />
        <G>
          <Flourish />
        </G>
        <G transform="translate(196 0) scale(-1 1)">
          <Flourish />
        </G>
      </Svg>
      <Text numberOfLines={1} style={[styles.label, { fontSize, lineHeight: Math.round(fontSize * 2.1) }]}>
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  box: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  label: {
    fontFamily: fonts.burmeseSerif,
    color: '#6B2E1A',
    textAlign: 'center',
    textAlignVertical: 'center',
    includeFontPadding: false,
  },
});

