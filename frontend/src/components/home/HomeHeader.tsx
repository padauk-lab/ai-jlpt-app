import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { Dashboard, Proverb, SessionDetail } from '@/api/types';
import { RubyText } from '@/components/RubyText';
import { colors, fonts, spacing, text } from '@/theme';

type Props = {
  dashboard: Dashboard;
  session: SessionDetail;
  proverb: Proverb | null;
};

// The top of the Home screen: session progress, pass prediction (合格予測),
// today's goal and the proverb of the day.
export function HomeHeader({ dashboard, session, proverb }: Props) {
  const [showProverb, setShowProverb] = useState(false);
  const { units_done, units_goal } = dashboard.today;
  const prediction = dashboard.pass_prediction;

  return (
    <View style={styles.header}>
      <View style={styles.topRow}>
        <View>
          <Text style={styles.sessionTitle}>အပိုင်း {session.number}</Text>
          <Text style={styles.muted}>ယူနစ် {session.units.length} ခုအနက် {session.units_done} ခု ပြီးပါပြီ</Text>
        </View>
        <View style={styles.prediction}>
          <Text style={styles.predictionNumber}>
            {prediction === null ? '—' : prediction}
            {prediction !== null && <Text style={styles.percent}>%</Text>}
          </Text>
          <Text style={styles.mutedSmall}>အောင်မြင်နိုင်ခြေ</Text>
        </View>
      </View>

      <View style={styles.goalRow}>
        <Text style={styles.goalText}>
          ယနေ့ {units_done}/{units_goal}
        </Text>
        <View style={styles.goalBars}>
          {Array.from({ length: units_goal }, (_, i) => (
            <View key={i} style={[styles.goalBar, i < units_done && styles.goalBarDone]} />
          ))}
        </View>
      </View>

      {proverb && (
        <Pressable onPress={() => setShowProverb((open) => !open)} style={styles.proverb}>
          <View style={styles.proverbRow}>
            <Text style={styles.proverbLabel}>ယနေ့ ဆိုရိုးစကား</Text>
            <View style={styles.proverbJa}>
              <RubyText ruby={proverb.ruby} size={17} fontFamily={fonts.brand} />
            </View>
          </View>
          {showProverb && (
            <View style={styles.proverbMore}>
              <Text style={styles.proverbMeaning}>{proverb.meaning_my}</Text>
              <Text style={styles.proverbExplain}>{proverb.explanation_my}</Text>
            </View>
          )}
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    gap: spacing.md,
    paddingHorizontal: 20,
    paddingTop: spacing.sm,
    paddingBottom: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
    backgroundColor: colors.background,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sessionTitle: {
    ...text.title,
    fontSize: 22,
    lineHeight: 36,
    color: colors.ink,
  },
  muted: {
    ...text.small,
    color: colors.inkMuted,
  },
  prediction: {
    alignItems: 'flex-end',
  },
  predictionNumber: {
    fontFamily: fonts.japaneseBold,
    fontSize: 26,
    lineHeight: 32,
    color: colors.ink,
  },
  percent: {
    fontSize: 14,
  },
  mutedSmall: {
    ...text.small,
    fontSize: 12,
    lineHeight: 20,
    color: colors.inkMuted,
  },
  goalRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  goalText: {
    ...text.label,
    fontSize: 13,
    color: colors.ink,
  },
  goalBars: {
    flex: 1,
    flexDirection: 'row',
    gap: 4,
  },
  goalBar: {
    flex: 1,
    height: 7,
    borderRadius: 4,
    backgroundColor: '#EFE9E1',
  },
  goalBarDone: {
    backgroundColor: colors.gold,
  },
  proverb: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 12,
    backgroundColor: colors.goldSoft,
  },
  proverbRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  proverbLabel: {
    ...text.label,
    fontSize: 12,
    lineHeight: 20,
    color: '#7A5A12',
  },
  proverbJa: {
    flex: 1,
    alignItems: 'flex-start',
  },
  proverbMore: {
    marginTop: spacing.sm,
    gap: spacing.xs,
  },
  proverbMeaning: {
    ...text.label,
    fontSize: 15,
    lineHeight: 26,
    color: colors.ink,
  },
  proverbExplain: {
    ...text.small,
    fontSize: 14,
    lineHeight: 24,
    color: '#4A4440',
  },
});
