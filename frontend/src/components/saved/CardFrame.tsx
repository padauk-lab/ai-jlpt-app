import type { ReactNode } from 'react';
import { StyleSheet, View, type ViewStyle } from 'react-native';
import Svg, { Circle, Path } from 'react-native-svg';

// The traditional Burmese card frame for saved words: a lacquer border, a thin gold
// line, cream paper, ကနုတ် (kanote) ornaments in the corners and a flame crest on top.

export const LACQUER = '#6B2E1A';
export const GOLD = '#B8913A';
export const PAPER = '#FBF7EE';
const RED = '#9E2A1E';

// A curling vine that ends in a pointed flame-leaf.
export function Kanote({ size = 46, style }: { size?: number; style?: ViewStyle }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48" fill="none" style={[{ position: 'absolute' }, style]}>
      <Path d="M4 44 L4 20 C4 10, 10 4, 20 4 L44 4" stroke={GOLD} strokeWidth={1.6} strokeLinecap="round" />
      <Path d="M9 40 L9 22 C9 14, 14 9, 22 9 L40 9" stroke={GOLD} strokeWidth={0.9} strokeLinecap="round" strokeDasharray="0.1 3" />
      <Path
        d="M13 30 C 13 20, 20 13, 30 13 C 24 15, 19 19, 17 25 C 22 21, 27 20, 31 22 C 25 23, 20 27, 18 33 C 16 31, 14 31, 13 30 Z"
        fill={GOLD}
      />
      <Path d="M30 13 C 33 11, 36 11.5, 38 13.5 C 35 13, 33 14, 31.5 15.5 Z M13 30 C 11 33, 11.5 36, 13.5 38 C 13 35, 14 33, 15.5 31.5 Z" fill={GOLD} />
      <Circle cx={21} cy={21} r={2} fill={RED} />
    </Svg>
  );
}

export function KanoteCorners({ inset = 8, size = 46 }: { inset?: number; size?: number }) {
  return (
    <>
      <Kanote size={size} style={{ left: inset, top: inset }} />
      <Kanote size={size} style={{ right: inset, top: inset, transform: [{ scaleX: -1 }] }} />
      <Kanote size={size} style={{ left: inset, bottom: inset, transform: [{ scaleY: -1 }] }} />
      <Kanote size={size} style={{ right: inset, bottom: inset, transform: [{ scaleX: -1 }, { scaleY: -1 }] }} />
    </>
  );
}

// A flame-shaped arch with a lotus bud, sitting on the top edge of the card.
function Crest() {
  return (
    <Svg width={96} height={30} viewBox="0 0 96 30" style={styles.crest}>
      <Path d="M4 28 C 20 28, 30 20, 38 10 C 42 5, 45 2, 48 0 C 51 2, 54 5, 58 10 C 66 20, 76 28, 92 28 Z" fill={LACQUER} />
      <Path d="M14 26 C 26 25, 34 18, 40 11 C 44 7, 46 5, 48 3.5 C 50 5, 52 7, 56 11 C 62 18, 70 25, 82 26" fill="none" stroke={GOLD} strokeWidth={1.2} />
      <Path d="M48 9 C 44 13, 44 18, 48 22 C 52 18, 52 13, 48 9 Z" fill={GOLD} />
      <Path d="M48 13 C 46.5 15, 46.5 17, 48 19 C 49.5 17, 49.5 15, 48 13 Z" fill={RED} />
    </Svg>
  );
}

export function CardFrame({ children, crest = true, style }: { children: ReactNode; crest?: boolean; style?: ViewStyle }) {
  return (
    <View style={[styles.outer, style]}>
      <View style={styles.paper}>
        <KanoteCorners />
        {children}
      </View>
      {crest && <Crest />}
    </View>
  );
}

const styles = StyleSheet.create({
  outer: {
    flex: 1,
    padding: 7,
    borderRadius: 18,
    backgroundColor: LACQUER,
  },
  paper: {
    flex: 1,
    overflow: 'hidden',
    borderWidth: 1.5,
    borderColor: GOLD,
    borderRadius: 13,
    backgroundColor: PAPER,
  },
  crest: {
    position: 'absolute',
    top: -14,
    alignSelf: 'center',
  },
});
