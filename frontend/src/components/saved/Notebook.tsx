import { useEffect, useRef, useState, type ReactNode } from 'react';
import { AccessibilityInfo, Animated, Easing, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import Svg, { Path } from 'react-native-svg';
import type { SavedWord } from '@/api/types';
import { RubyText } from '@/components/RubyText';
import { colors, fonts, spacing, text } from '@/theme';
import { formatDateMy, toMyanmarDigits } from '@/utils/myanmar';

// The saved-words notebook: a traditional Myanmar folding book. Closed, it shows a
// lacquer cover; opened, the folded pages fan out with one saved word on the middle page.

const LACQUER = '#6B2E1A';
const GOLD_LINE = '#C9A75E';
const PAGE = '#2B2623';
const CREAM = '#EFE3C8';
const FADED = '#C9B994';

function Corner({ style }: { style: object }) {
  return (
    <Svg width={20} height={20} viewBox="0 0 26 26" fill="none" style={[{ position: 'absolute' }, style]}>
      <Path d="M3 20 C 3 10, 10 3, 20 3" stroke={GOLD_LINE} strokeWidth={1.6} strokeLinecap="round" />
      <Path
        d="M20 3 C 23.5 3, 24.5 6.5, 22 7.4 C 20.2 8, 19 6.2, 20.4 5.4 M3 20 C 3 23.5, 6.5 24.5, 7.4 22 C 8 20.2, 6.2 19, 5.4 20.4"
        stroke={GOLD_LINE}
        strokeWidth={1.4}
        strokeLinecap="round"
      />
    </Svg>
  );
}

function Corners({ inset }: { inset: number }) {
  return (
    <>
      <Corner style={{ left: inset, top: inset }} />
      <Corner style={{ right: inset, top: inset, transform: [{ scaleX: -1 }] }} />
      <Corner style={{ left: inset, bottom: inset, transform: [{ scaleY: -1 }] }} />
      <Corner style={{ right: inset, bottom: inset, transform: [{ scaleX: -1 }, { scaleY: -1 }] }} />
    </>
  );
}

// ---------- closed ----------

export function ClosedNotebook({ subtitle, faded = false, onPress }: { subtitle: string; faded?: boolean; onPress?: () => void }) {
  const book = (
    <View style={[styles.closedWrap, faded && styles.faded]}>
      <View style={styles.cover}>
        <View style={styles.coverInner}>
          <Corners inset={10} />
          <View style={styles.plate}>
            <Text style={styles.plateTitle}>မှတ်ထားသော စကားလုံး</Text>
            <Text style={styles.plateSub}>{subtitle}</Text>
          </View>
        </View>
      </View>
      <View style={styles.folds}>
        {Array.from({ length: 8 }, (_, i) => (
          <View key={i} style={[styles.fold, { backgroundColor: i % 2 === 0 ? '#3A332F' : '#1F1B19' }]} />
        ))}
      </View>
      <View style={styles.backCover} />
    </View>
  );
  if (!onPress) return book;
  return (
    <Pressable onPress={onPress} accessibilityRole="button" accessibilityLabel="မှတ်စုစာအုပ်ကို ဖွင့်မည်" style={({ pressed }) => pressed && { opacity: 0.9 }}>
      {book}
    </Pressable>
  );
}

// ---------- open ----------

type OpenProps = {
  word: SavedWord;
  position: number; // 1-based
  total: number;
  previous?: SavedWord;
  next?: SavedWord;
};

export function OpenNotebook({ word, position, total, previous, next }: OpenProps) {
  const unfold = useRef(new Animated.Value(0)).current;
  const [ready, setReady] = useState(false);

  // Unfold once when the book opens: the middle page widens, then the side folds swing out.
  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then((reduce) => {
      setReady(true);
      if (reduce) {
        unfold.setValue(1);
        return;
      }
      Animated.timing(unfold, {
        toValue: 1,
        duration: 1000,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: Platform.OS !== 'web',
      }).start();
    });
  }, [unfold]);

  const centerScale = unfold.interpolate({ inputRange: [0, 0.6, 1], outputRange: [0.08, 1, 1] });
  const sideOpacity = unfold.interpolate({ inputRange: [0, 0.5, 1], outputRange: [0, 0, 1] });
  const leftTurn = unfold.interpolate({ inputRange: [0, 0.5, 1], outputRange: ['88deg', '88deg', '58deg'] });
  const rightTurn = unfold.interpolate({ inputRange: [0, 0.5, 1], outputRange: ['-88deg', '-88deg', '-58deg'] });

  if (!ready) return <View style={styles.spread} />;

  return (
    <View style={styles.spread}>
      <Animated.View
        style={[styles.side, { opacity: sideOpacity, transformOrigin: 'right center', transform: [{ perspective: 700 }, { rotateY: leftTurn }] }]}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        {previous && <Text style={styles.sideWord}>{previous.ruby.map((p) => p.text).join('')}</Text>}
      </Animated.View>

      <Animated.View style={[styles.page, { transform: [{ scaleX: centerScale }] }]}>
        <Corners inset={10} />
        <Text style={styles.pageNumber}>
          {toMyanmarDigits(position)} / {toMyanmarDigits(total)}
        </Text>
        <RubyText ruby={word.ruby} size={40} color={CREAM} readingColor={FADED} fontFamily={fonts.brand} />
        <Svg width={90} height={10} viewBox="0 0 90 10">
          <Path d="M2 5 L36 5 M54 5 L88 5" stroke={GOLD_LINE} strokeWidth={1.2} strokeLinecap="round" />
          <Path d="M45 1 L49 5 L45 9 L41 5 Z" fill={GOLD_LINE} />
        </Svg>
        <Text style={styles.meaning}>{word.meaning_my}</Text>
        <Text style={styles.source}>
          အပိုင်း {toMyanmarDigits(word.session_number)} ၊ ယူနစ် {toMyanmarDigits(word.unit_number)}
        </Text>
        <Text style={styles.savedAt}>{formatDateMy(word.saved_at.slice(0, 10), false)} တွင် သိမ်းခဲ့သည်</Text>
      </Animated.View>

      <Animated.View
        style={[styles.side, { opacity: sideOpacity, transformOrigin: 'left center', transform: [{ perspective: 700 }, { rotateY: rightTurn }] }]}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        {next && <Text style={styles.sideWord}>{next.ruby.map((p) => p.text).join('')}</Text>}
      </Animated.View>
    </View>
  );
}

export function NotebookArea({ children }: { children: ReactNode }) {
  return <View style={styles.area}>{children}</View>;
}

const styles = StyleSheet.create({
  area: {
    alignItems: 'center',
    gap: spacing.lg,
  },
  closedWrap: {
    alignItems: 'center',
  },
  faded: {
    opacity: 0.55,
  },
  cover: {
    width: 318,
    height: 170,
    padding: 4,
    borderRadius: 6,
    backgroundColor: LACQUER,
  },
  coverInner: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: GOLD_LINE,
    borderRadius: 4,
  },
  plate: {
    alignItems: 'center',
    paddingHorizontal: 26,
    paddingVertical: 8,
    borderWidth: 1.5,
    borderColor: GOLD_LINE,
    borderRadius: 4,
    backgroundColor: '#5A2614',
  },
  plateTitle: {
    fontFamily: fonts.burmeseSerif,
    fontSize: 17,
    lineHeight: 36,
    color: '#F2D27A',
  },
  plateSub: {
    ...text.small,
    fontSize: 13,
    color: '#E6CB8E',
  },
  folds: {
    width: 306,
    overflow: 'hidden',
    borderBottomLeftRadius: 4,
    borderBottomRightRadius: 4,
  },
  fold: {
    height: 3,
  },
  backCover: {
    width: 318,
    height: 9,
    borderBottomLeftRadius: 6,
    borderBottomRightRadius: 6,
    backgroundColor: LACQUER,
  },
  spread: {
    height: 350,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  side: {
    width: 70,
    height: 330,
    alignItems: 'center',
    justifyContent: 'center',
    borderTopWidth: 2,
    borderBottomWidth: 2,
    borderColor: GOLD_LINE,
    backgroundColor: '#211D1B',
  },
  sideWord: {
    fontFamily: fonts.brand,
    fontSize: 18,
    lineHeight: 26,
    color: 'rgba(239, 227, 200, 0.45)',
    transform: [{ rotate: '90deg' }],
    width: 200,
    textAlign: 'center',
  },
  page: {
    width: 226,
    height: 350,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    paddingHorizontal: 18,
    borderTopWidth: 3,
    borderBottomWidth: 3,
    borderColor: GOLD_LINE,
    backgroundColor: PAGE,
  },
  pageNumber: {
    position: 'absolute',
    top: 16,
    fontFamily: fonts.japanese,
    fontSize: 12,
    color: FADED,
  },
  meaning: {
    fontFamily: fonts.burmeseSerif,
    fontSize: 18,
    lineHeight: 38,
    color: CREAM,
    textAlign: 'center',
  },
  source: {
    ...text.small,
    fontSize: 12,
    lineHeight: 21,
    color: FADED,
  },
  savedAt: {
    position: 'absolute',
    bottom: 14,
    ...text.small,
    fontSize: 11,
    lineHeight: 19,
    color: '#9C8D6E',
  },
});
