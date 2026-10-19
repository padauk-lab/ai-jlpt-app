import { useEffect, useRef, useState } from 'react';
import {
  AccessibilityInfo,
  Animated,
  Easing,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import type { Word } from '@/api/types';
import { RubyText } from '@/components/RubyText';
import { BookmarkIcon, FlipIcon } from '@/components/ui/Icons';
import { colors, fonts, radius, spacing, text } from '@/theme';
import { Examples, MoreExamplesButton } from './Examples';

type Props = {
  word: Word;
  saved: boolean;
  onToggleSaved: () => void;
  onMoreExamples: () => void;
};

// A memory card: the front shows only the word, the back shows everything.
// Tapping turns it over with a 3D flip (instantly when Reduce Motion is on).
export function FlipCard({ word, saved, onToggleSaved, onMoreExamples }: Props) {
  const [flipped, setFlipped] = useState(false);
  const [reduceMotion, setReduceMotion] = useState(false);
  const turn = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then(setReduceMotion);
  }, []);

  function toggle() {
    const target = flipped ? 0 : 1;
    setFlipped(!flipped);
    if (reduceMotion) {
      turn.setValue(target);
      return;
    }
    Animated.timing(turn, {
      toValue: target,
      duration: 450,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: Platform.OS !== 'web',
    }).start();
  }

  const frontTurn = turn.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '180deg'] });
  const backTurn = turn.interpolate({ inputRange: [0, 1], outputRange: ['180deg', '360deg'] });
  const wordText = word.ruby.map((piece) => piece.text).join('');

  const bookmark = (
    <Pressable
      onPress={onToggleSaved}
      hitSlop={8}
      accessibilityRole="button"
      accessibilityLabel="စကားလုံး သိမ်းမည်"
      accessibilityState={{ selected: saved }}
      style={styles.bookmark}
    >
      <BookmarkIcon color={colors.inkMuted} filled={saved} />
    </Pressable>
  );

  return (
    <View style={styles.card}>
      <Animated.View
        pointerEvents={flipped ? 'none' : 'auto'}
        style={[styles.face, styles.front, { transform: [{ perspective: 1200 }, { rotateY: frontTurn }] }]}
      >
        <Pressable
          onPress={toggle}
          accessibilityRole="button"
          accessibilityLabel={`${wordText}၊ ကတ်ကို လှန်မည်`}
          style={styles.frontInner}
        >
          <Text style={styles.frontWord}>{wordText}</Text>
          <View style={styles.goldLine} />
          <View style={styles.hint}>
            <FlipIcon color={colors.inkMuted} />
            <Text style={styles.hintText}>နှိပ်ပြီး လှန်ကြည့်ပါ</Text>
          </View>
        </Pressable>
        {bookmark}
      </Animated.View>

      <Animated.View
        pointerEvents={flipped ? 'auto' : 'none'}
        style={[styles.face, styles.back, { transform: [{ perspective: 1200 }, { rotateY: backTurn }] }]}
      >
        <ScrollView contentContainerStyle={styles.backContent} nestedScrollEnabled>
          <Pressable onPress={toggle} accessibilityRole="button" accessibilityLabel="ကတ်ကို ပြန်လှန်မည်">
            <RubyText ruby={word.ruby} size={30} fontFamily={fonts.japaneseBold} align="left" />
            <Text style={styles.meaning}>{word.meaning_my}</Text>
          </Pressable>

          {(word.meaning_ja || word.definition_my) && (
            <View style={styles.definitions}>
              {word.meaning_ja && (
                <View style={styles.defRow}>
                  <Text style={[styles.chip, styles.chipJa]}>日本語</Text>
                  <Text style={styles.defJa}>{word.meaning_ja}</Text>
                </View>
              )}
              {word.definition_my && (
                <View style={styles.defRow}>
                  <Text style={[styles.chip, styles.chipMy]}>မြန်မာ</Text>
                  <Text style={styles.defMy}>{word.definition_my}</Text>
                </View>
              )}
            </View>
          )}

          <View style={styles.dotted} />
          <Examples examples={word.examples} />
          <MoreExamplesButton onPress={onMoreExamples} />
        </ScrollView>
        {bookmark}
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    height: 520,
  },
  face: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    borderWidth: 1.5,
    borderColor: colors.paperEdge,
    borderRadius: 20,
    overflow: 'hidden',
    backfaceVisibility: 'hidden',
  },
  front: {
    backgroundColor: colors.background,
  },
  back: {
    backgroundColor: '#FFFDF7',
  },
  frontInner: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.lg,
  },
  frontWord: {
    fontFamily: fonts.japaneseBold,
    fontSize: 52,
    lineHeight: 68,
    color: colors.ink,
  },
  goldLine: {
    width: 40,
    height: 3,
    borderRadius: 2,
    backgroundColor: colors.gold,
  },
  hint: {
    position: 'absolute',
    bottom: 26,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  hintText: {
    ...text.small,
    color: colors.inkMuted,
  },
  bookmark: {
    position: 'absolute',
    top: 14,
    right: 14,
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backContent: {
    gap: spacing.md,
    padding: 20,
    paddingTop: 22,
  },
  meaning: {
    ...text.label,
    fontSize: 17,
    lineHeight: 30,
    color: colors.ink,
  },
  definitions: {
    gap: spacing.sm,
    padding: spacing.md,
    borderRadius: radius.control,
    borderWidth: 1,
    borderColor: '#EFE6D3',
    backgroundColor: colors.background,
  },
  defRow: {
    flexDirection: 'row',
    gap: 10,
  },
  chip: {
    alignSelf: 'flex-start',
    marginTop: 3,
    paddingHorizontal: 8,
    borderRadius: 10,
    overflow: 'hidden',
    fontSize: 11,
    lineHeight: 20,
  },
  chipJa: {
    fontFamily: fonts.japaneseBold,
    backgroundColor: '#F3EFEA',
    color: colors.inkMuted,
  },
  chipMy: {
    fontFamily: fonts.burmeseBold,
    backgroundColor: colors.goldSoft,
    color: '#7A5A12',
  },
  defJa: {
    flex: 1,
    fontFamily: fonts.japanese,
    fontSize: 15,
    lineHeight: 25,
    color: colors.ink,
  },
  defMy: {
    flex: 1,
    ...text.small,
    fontSize: 14,
    lineHeight: 25,
    color: colors.ink,
  },
  dotted: {
    borderTopWidth: 1.5,
    borderStyle: 'dotted',
    borderColor: colors.paperEdge,
  },
});
