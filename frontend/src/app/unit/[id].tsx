import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useLocalSearchParams } from 'expo-router';
import { completeUnit, getUnit } from '@/api';
import type { UnitDetail } from '@/api/types';
import { OrnateFrame } from '@/components/OrnateFrame';
import { BackIcon, NextIcon } from '@/components/ui/Icons';
import { Notice, useNotice } from '@/components/ui/Notice';
import { FlipCard } from '@/components/unit/FlipCard';
import { GrammarCard } from '@/components/unit/GrammarCard';
import { colors, fonts, spacing, text } from '@/theme';
import { toMyanmarDigits } from '@/utils/myanmar';

type Tab = 'words' | 'grammar';

export default function UnitScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [unit, setUnit] = useState<UnitDetail | null>(null);
  const [tab, setTab] = useState<Tab>('words');
  const [index, setIndex] = useState(0);
  const [saved, setSaved] = useState<Set<number>>(new Set());
  const [review, setReview] = useState<Set<number>>(new Set());
  const [finishing, setFinishing] = useState(false);
  const notice = useNotice();

  useEffect(() => {
    getUnit(Number(id)).then((data) => {
      setUnit(data);
      setSaved(new Set(data.words.filter((w) => w.bookmarked).map((w) => w.id)));
    });
  }, [id]);

  if (!unit) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator color={colors.ink} />
      </SafeAreaView>
    );
  }

  const word = unit.words[index];
  const total = unit.words.length;

  function toggleSaved(wordId: number) {
    // Next step: POST /bookmarks (#17) and DELETE /bookmarks/{id} (#18).
    setSaved((current) => {
      const next = new Set(current);
      if (next.has(wordId)) next.delete(wordId);
      else next.add(wordId);
      return next;
    });
  }

  function toggleReview(wordId: number) {
    // Only remembered while this screen is open (not in the contract yet).
    setReview((current) => {
      const next = new Set(current);
      if (next.has(wordId)) next.delete(wordId);
      else next.add(wordId);
      return next;
    });
  }

  async function markDone() {
    if (!unit) return;
    setFinishing(true);
    await completeUnit(unit.id);
    router.back();
  }

  const showMoreExamples = () => notice.show('AI ဥပမာများ မကြာမီ ရပါမယ်');

  return (
    <SafeAreaView style={styles.screen} edges={['top']}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Pressable onPress={() => router.back()} accessibilityRole="button" accessibilityLabel="နောက်သို့" style={styles.iconButton}>
            <BackIcon color={colors.ink} />
          </Pressable>
          <OrnateFrame label={`ယူနစ် ${toMyanmarDigits(unit.number)}`} width={180} />
          <Text numberOfLines={1} style={styles.sessionLabel}>
            အပိုင်း {toMyanmarDigits(unit.session_number)}
          </Text>
        </View>
        <View style={styles.tabs} accessibilityRole="tablist">
          <TabButton label="ဝေါဟာရ" count={total} active={tab === 'words'} onPress={() => setTab('words')} />
          <TabButton label="သဒ္ဒါ" count={1} active={tab === 'grammar'} onPress={() => setTab('grammar')} />
        </View>
      </View>

      {tab === 'words' ? (
        <ScrollView contentContainerStyle={styles.body}>
          <View style={styles.counterRow}>
            <Text style={styles.counter}>
              {index + 1} <Text style={styles.counterTotal}>/ {total}</Text>
            </Text>
            <Text style={styles.muted}>ပြန်လေ့လာရန် {review.size}</Text>
          </View>
          <View style={styles.track}>
            <View style={[styles.fill, { width: `${((index + 1) / total) * 100}%` }]} />
          </View>

          <FlipCard
            key={word.id}
            word={word}
            saved={saved.has(word.id)}
            onToggleSaved={() => toggleSaved(word.id)}
            onMoreExamples={showMoreExamples}
          />

          <View style={styles.navRow}>
            <Pressable
              onPress={() => setIndex((i) => Math.max(0, i - 1))}
              disabled={index === 0}
              accessibilityRole="button"
              accessibilityLabel="ရှေ့ကတ်"
              style={[styles.round, index === 0 && styles.disabled]}
            >
              <BackIcon color={colors.ink} size={20} />
            </Pressable>
            <Pressable
              onPress={() => toggleReview(word.id)}
              accessibilityRole="button"
              accessibilityState={{ selected: review.has(word.id) }}
              style={[styles.reviewButton, review.has(word.id) && styles.reviewOn]}
            >
              <Text style={[styles.reviewText, review.has(word.id) && styles.reviewTextOn]}>ထပ်လေ့လာမည်</Text>
            </Pressable>
            <Pressable
              onPress={() => setIndex((i) => Math.min(total - 1, i + 1))}
              disabled={index === total - 1}
              accessibilityRole="button"
              accessibilityLabel="နောက်ကတ်"
              style={[styles.round, styles.roundDark, index === total - 1 && styles.disabled]}
            >
              <NextIcon color={colors.onInk} size={20} />
            </Pressable>
          </View>
        </ScrollView>
      ) : (
        <ScrollView contentContainerStyle={styles.body}>
          <GrammarCard grammar={unit.grammar} onMoreExamples={showMoreExamples} />
        </ScrollView>
      )}

      <Notice message={notice.message} />

      <SafeAreaView edges={['bottom']} style={styles.doneBar}>
        <Pressable
          onPress={markDone}
          disabled={finishing}
          style={({ pressed }) => [styles.doneButton, (pressed || finishing) && { opacity: 0.85 }]}
        >
          <Text style={styles.doneText}>{finishing ? '…' : 'ယူနစ် ပြီးပါပြီ'}</Text>
        </Pressable>
      </SafeAreaView>
    </SafeAreaView>
  );
}

function TabButton({ label, count, active, onPress }: { label: string; count: number; active: boolean; onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="tab"
      accessibilityState={{ selected: active }}
      style={[styles.tab, active && styles.tabActive]}
    >
      <Text style={[styles.tabText, active && styles.tabTextActive]}>
        {label} <Text style={styles.tabCount}>{count}</Text>
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  header: {
    paddingHorizontal: spacing.md,
    borderBottomWidth: 1.5,
    borderBottomColor: colors.divider,
    backgroundColor: colors.background,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  iconButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sessionLabel: {
    ...text.small,
    fontSize: 12,
    minWidth: 44,
    textAlign: 'right',
    color: colors.inkMuted,
  },
  tabs: {
    flexDirection: 'row',
    marginTop: spacing.xs,
  },
  tab: {
    flex: 1,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    borderBottomWidth: 3,
    borderBottomColor: 'transparent',
    marginBottom: -1.5,
  },
  tabActive: {
    borderBottomColor: colors.ink,
  },
  tabText: {
    ...text.body,
    fontSize: 15,
    color: colors.inkMuted,
  },
  tabTextActive: {
    fontFamily: fonts.burmeseBold,
    color: colors.ink,
  },
  tabCount: {
    fontSize: 12,
    color: colors.inkMuted,
  },
  body: {
    gap: spacing.md,
    padding: 20,
    paddingBottom: spacing.xxl,
    width: '100%',
    maxWidth: 520,
    alignSelf: 'center',
  },
  counterRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  counter: {
    fontFamily: fonts.japaneseBold,
    fontSize: 15,
    color: colors.ink,
  },
  counterTotal: {
    fontFamily: fonts.japanese,
    color: colors.inkMuted,
  },
  muted: {
    ...text.small,
    color: colors.inkMuted,
  },
  track: {
    height: 6,
    borderRadius: 3,
    overflow: 'hidden',
    backgroundColor: colors.track,
  },
  fill: {
    height: 6,
    backgroundColor: colors.gold,
  },
  navRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  round: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  roundDark: {
    borderColor: colors.ink,
    backgroundColor: colors.ink,
  },
  disabled: {
    opacity: 0.35,
  },
  reviewButton: {
    flex: 1,
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  reviewOn: {
    borderColor: colors.goldDeep,
    backgroundColor: colors.goldSoft,
  },
  reviewText: {
    ...text.label,
    fontSize: 15,
    color: colors.ink,
  },
  reviewTextOn: {
    color: '#7A5A12',
  },
  doneBar: {
    paddingHorizontal: 20,
    paddingTop: spacing.md,
    paddingBottom: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.divider,
    backgroundColor: colors.background,
  },
  doneButton: {
    height: 52,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.ink,
  },
  doneText: {
    fontFamily: fonts.burmeseBold,
    fontSize: 16,
    lineHeight: 28,
    color: colors.onInk,
  },
});
