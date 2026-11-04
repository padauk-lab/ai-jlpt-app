import { useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, ActivityIndicator, Animated, Easing, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Path } from 'react-native-svg';
import type { Example, SavedWord, Word } from '@/api/types';
import { RubyText } from '@/components/RubyText';
import { Examples } from '@/components/unit/Examples';
import { FlipIcon } from '@/components/ui/Icons';
import { colors, fonts, spacing, text } from '@/theme';
import { toMyanmarDigits } from '@/utils/myanmar';
import { CardFrame, GOLD, LACQUER } from './CardFrame';

// One saved word as a traditional flash card.
// Front: only the word, so users can test themselves. Back: everything about it.

export type Details = { state: 'loading' } | { state: 'error' } | { state: 'ready'; word: Word | null };

type Props = {
  word: SavedWord;
  position: number; // 1-based
  total: number;
  flipped: boolean;
  onFlip: () => void;
  details: Details;
  aiExamples: Example[]; // new sentences from "More examples" (#27)
  onRetry: () => void;
};

const CARD_HEIGHT = 450;

function Divider() {
  return (
    <Svg width={120} height={12} viewBox="0 0 120 12">
      <Path d="M4 6 L46 6 M74 6 L116 6" stroke={GOLD} strokeWidth={1.3} strokeLinecap="round" />
      <Path d="M60 1 L65 6 L60 11 L55 6 Z" fill="#9E2A1E" />
      <Circle cx={50} cy={6} r={1.6} fill={GOLD} />
      <Circle cx={70} cy={6} r={1.6} fill={GOLD} />
    </Svg>
  );
}

function Medal({ position, total }: { position: number; total: number }) {
  return (
    <View style={styles.medal}>
      <Text style={styles.medalText}>
        {toMyanmarDigits(position)} / {toMyanmarDigits(total)}
      </Text>
    </View>
  );
}

export function SavedFlashCard({ word, position, total, flipped, onFlip, details, aiExamples, onRetry }: Props) {
  const turn = useRef(new Animated.Value(flipped ? 1 : 0)).current;
  const [reduceMotion, setReduceMotion] = useState(false);

  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then(setReduceMotion);
  }, []);

  // Turn the card whenever "flipped" changes.
  useEffect(() => {
    const target = flipped ? 1 : 0;
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
  }, [flipped, reduceMotion, turn]);

  const frontTurn = turn.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '180deg'] });
  const backTurn = turn.interpolate({ inputRange: [0, 1], outputRange: ['180deg', '360deg'] });
  const wordText = word.ruby.map((piece) => piece.text).join('');
  const source = `အပိုင်း ${toMyanmarDigits(word.session_number)} ၊ ယူနစ် ${toMyanmarDigits(word.unit_number)}`;
  const full = details.state === 'ready' ? details.word : null;

  return (
    <View style={styles.wrap}>
      {/* Two more cards peeking out behind, like a real stack */}
      <View style={[styles.behind, styles.behindFar]} />
      <View style={[styles.behind, styles.behindNear]} />

      <Animated.View
        pointerEvents={flipped ? 'none' : 'auto'}
        style={[styles.face, { transform: [{ perspective: 1200 }, { rotateY: frontTurn }] }]}
      >
        <CardFrame>
          <Pressable onPress={onFlip} accessibilityRole="button" accessibilityLabel={`${wordText}၊ ကတ်ကို လှန်မည်`} style={styles.front}>
            <Text style={styles.source}>{source}</Text>
            <Text style={styles.bigWord} adjustsFontSizeToFit numberOfLines={1}>
              {wordText}
            </Text>
            <Divider />
            <View style={styles.hint}>
              <FlipIcon color={colors.inkMuted} />
              <Text style={styles.hintText}>နှိပ်ပြီး လှန်ကြည့်ပါ</Text>
            </View>
          </Pressable>
          <Medal position={position} total={total} />
        </CardFrame>
      </Animated.View>

      <Animated.View
        pointerEvents={flipped ? 'auto' : 'none'}
        style={[styles.face, { transform: [{ perspective: 1200 }, { rotateY: backTurn }] }]}
      >
        <CardFrame>
          <ScrollView contentContainerStyle={styles.back} nestedScrollEnabled>
            <Pressable onPress={onFlip} accessibilityRole="button" accessibilityLabel="ကတ်ကို ပြန်လှန်မည်" style={styles.backTop}>
              <RubyText ruby={word.ruby} size={32} fontFamily={fonts.brand} align="left" />
              <Text style={styles.chip}>{source}</Text>
            </Pressable>
            <Text style={styles.meaning}>{word.meaning_my}</Text>

            {details.state === 'loading' && <ActivityIndicator color={LACQUER} style={{ marginTop: spacing.md }} />}
            {details.state === 'error' && (
              <Pressable onPress={onRetry} style={styles.retry}>
                <Text style={styles.retryText}>ဥပမာများ ရယူ၍ မရပါ။ နှိပ်ပြီး ပြန်ကြိုးစားပါ။</Text>
              </Pressable>
            )}

            {full && (full.meaning_ja || full.definition_my) && (
              <View style={styles.section}>
                <Text style={styles.label}>အဓိပ္ပာယ် ဖွင့်ဆိုချက်</Text>
                {full.meaning_ja && <Text style={styles.definitionJa}>{full.meaning_ja}</Text>}
                {full.definition_my && <Text style={styles.definitionMy}>{full.definition_my}</Text>}
              </View>
            )}

            {(full?.examples.length || aiExamples.length) > 0 && (
              <View style={styles.section}>
                <Text style={styles.label}>ဥပမာ</Text>
                <Examples examples={[...(full?.examples ?? []), ...aiExamples]} />
              </View>
            )}
          </ScrollView>
          <Medal position={position} total={total} />
        </CardFrame>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    width: '100%',
    maxWidth: 330,
    height: CARD_HEIGHT,
    alignSelf: 'center',
  },
  behind: {
    position: 'absolute',
    top: 4,
    left: 8,
    right: 8,
    bottom: -4,
    borderRadius: 18,
  },
  behindFar: {
    backgroundColor: '#5A2614',
    transform: [{ translateX: 8 }, { translateY: 8 }, { rotate: '4deg' }],
  },
  behindNear: {
    backgroundColor: '#7A3A22',
    transform: [{ translateX: -6 }, { translateY: 5 }, { rotate: '-3deg' }],
  },
  face: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backfaceVisibility: 'hidden',
  },
  front: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    paddingHorizontal: 34,
  },
  source: {
    ...text.small,
    fontSize: 12,
    color: '#8C6A2E',
  },
  bigWord: {
    fontFamily: fonts.brand,
    fontSize: 60,
    lineHeight: 80,
    color: colors.ink,
    textAlign: 'center',
  },
  hint: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: spacing.sm,
  },
  hintText: {
    ...text.small,
    fontSize: 13,
    color: colors.inkMuted,
  },
  medal: {
    position: 'absolute',
    bottom: 16,
    alignSelf: 'center',
    minWidth: 58,
    height: 26,
    paddingHorizontal: 10,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: GOLD,
    borderRadius: 13,
    backgroundColor: colors.goldSoft,
  },
  medalText: {
    ...text.small,
    fontSize: 13,
    lineHeight: 22,
    color: '#7A5A12',
  },
  back: {
    gap: spacing.sm,
    paddingTop: 30,
    paddingHorizontal: 22,
    paddingBottom: 56,
  },
  backTop: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    gap: spacing.sm,
  },
  chip: {
    ...text.small,
    fontSize: 11,
    lineHeight: 20,
    marginBottom: 8,
    paddingHorizontal: 9,
    borderRadius: 10,
    overflow: 'hidden',
    backgroundColor: '#F1E6D0',
    color: '#7A5A12',
  },
  meaning: {
    fontFamily: fonts.burmeseSerif,
    fontSize: 20,
    lineHeight: 42,
    color: LACQUER,
  },
  section: {
    gap: 4,
    marginTop: spacing.xs,
  },
  label: {
    ...text.label,
    fontSize: 11,
    lineHeight: 20,
    color: '#8C6A2E',
  },
  definitionJa: {
    fontFamily: fonts.japanese,
    fontSize: 14,
    lineHeight: 24,
    color: colors.ink,
  },
  definitionMy: {
    ...text.small,
    fontSize: 13,
    lineHeight: 23,
    color: colors.inkMuted,
  },
  retry: {
    padding: spacing.md,
    borderRadius: 10,
    backgroundColor: colors.wrongBg,
  },
  retryText: {
    ...text.small,
    fontSize: 13,
    color: '#9E2F29',
  },
});
