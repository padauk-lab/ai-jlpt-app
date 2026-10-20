import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { getPlan } from '@/api';
import type { StudyPlan } from '@/api/types';
import { SparkIcon } from '@/components/ui/Icons';
import { colors, fonts, radius, spacing, text } from '@/theme';
import { daysUntil, formatDateMy, formatShortDate } from '@/utils/myanmar';

// The study plan (#10). The numbers come from the backend; the AI only writes the tip.
export default function PlanScreen() {
  const [plan, setPlan] = useState<StudyPlan | null>(null);

  useEffect(() => {
    getPlan().then(setPlan);
  }, []);

  if (!plan) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator color={colors.ink} />
      </SafeAreaView>
    );
  }

  const hasDate = plan.exam_date !== null && plan.days_left !== null && plan.finish_by !== null;
  // Share of the time until the exam spent on units; the rest is for review.
  const studyDays = hasDate ? Math.max(0, daysUntil(plan.finish_by as string)) : 0;
  const share = hasDate && plan.days_left ? Math.min(1, studyDays / plan.days_left) : 1;
  const reviewDays = hasDate ? Math.max(0, (plan.days_left as number) - studyDays) : 0;

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Text style={styles.title}>သင့်ရဲ့ လေ့လာမှု အစီအစဉ်</Text>
          <Text style={styles.subtitle}>
            {hasDate ? `${formatDateMy(plan.exam_date as string, false)} စာမေးပွဲအတွက်` : 'စာမေးပွဲ ရက်စွဲ မဆုံးဖြတ်ရသေးပါ'}
          </Text>
        </View>

        <View style={styles.hero}>
          <Text style={styles.muted}>တစ်နေ့လျှင်</Text>
          <View style={styles.perDay}>
            <Text style={styles.perDayNumber}>{plan.units_per_day}</Text>
            <Text style={styles.perDayUnit}>ယူနစ်</Text>
          </View>
          <View style={styles.bars}>
            {Array.from({ length: plan.units_per_day }, (_, i) => (
              <View key={i} style={styles.bar} />
            ))}
          </View>
          <View style={styles.stats}>
            {hasDate && <Stat value={String(plan.days_left)} label="ကျန်ရက်" />}
            <Stat value={String(plan.units_total - plan.units_done)} label="ကျန်ယူနစ်" />
            {hasDate && <Stat value={formatShortDate(plan.finish_by as string)} label="ပြီးမည့်ရက်" />}
          </View>
        </View>

        {hasDate && (
          <View style={styles.card}>
            <View style={styles.timelineLabelRow}>
              <Text style={[styles.finishLabel, { left: `${share * 100}%` }]} numberOfLines={1}>
                ယူနစ်အားလုံး ပြီး {formatShortDate(plan.finish_by as string)} ▾
              </Text>
            </View>
            <View style={styles.timeline}>
              <View style={[styles.timelineStudy, { width: `${share * 100}%` }]} />
            </View>
            <View style={styles.timelineEnds}>
              <Text style={styles.small}>ယနေ့</Text>
              <Text style={styles.small}>စာမေးပွဲ {formatShortDate(plan.exam_date as string)}</Text>
            </View>
            {reviewDays > 0 && <Text style={styles.small}>စာမေးပွဲမတိုင်ခင် ပြန်နွှေးဖို့ {reviewDays} ရက် ကျန်ပါမယ်။</Text>}
          </View>
        )}

        {plan.ai_tip_my && (
          <View style={styles.tip}>
            <View style={styles.tipHead}>
              <SparkIcon color={colors.lacquer} />
              <Text style={styles.tipLabel}>အကြံပြုချက်</Text>
            </View>
            <Text style={styles.tipText}>{plan.ai_tip_my}</Text>
          </View>
        )}

        <Pressable onPress={() => router.replace('/home')} style={({ pressed }) => [styles.primaryButton, pressed && { opacity: 0.85 }]}>
          <Text style={styles.primaryText}>စတင်လေ့လာမည်</Text>
        </Pressable>
        <Text style={[styles.small, styles.centerText]}>ဆက်တင်ထဲမှာ အချိန်မရွေး ပြောင်းနိုင်ပါတယ်</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.small}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.goldSoft,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.goldSoft,
  },
  content: {
    gap: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xxl,
    width: '100%',
    maxWidth: 520,
    alignSelf: 'center',
  },
  header: {
    alignItems: 'center',
    paddingTop: spacing.xl,
    paddingBottom: spacing.sm,
  },
  title: {
    fontFamily: fonts.burmeseSerif,
    fontSize: 22,
    lineHeight: 46,
    color: colors.lacquer,
  },
  subtitle: {
    ...text.small,
    fontSize: 14,
    color: colors.inkMuted,
  },
  hero: {
    alignItems: 'center',
    gap: spacing.xs,
    padding: spacing.lg,
    paddingTop: 22,
    borderWidth: 1.5,
    borderColor: colors.paperEdge,
    borderRadius: 18,
    backgroundColor: colors.background,
  },
  muted: {
    ...text.small,
    fontSize: 14,
    color: colors.inkMuted,
  },
  perDay: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: spacing.sm,
  },
  perDayNumber: {
    fontFamily: fonts.japaneseBold,
    fontSize: 64,
    lineHeight: 72,
    color: colors.ink,
  },
  perDayUnit: {
    ...text.label,
    fontSize: 18,
    lineHeight: 30,
    color: colors.ink,
  },
  bars: {
    flexDirection: 'row',
    gap: 6,
  },
  bar: {
    width: 26,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.gold,
  },
  stats: {
    alignSelf: 'stretch',
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.lg,
  },
  stat: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: spacing.md,
    borderRadius: 12,
    backgroundColor: colors.surface,
  },
  statValue: {
    fontFamily: fonts.japaneseBold,
    fontSize: 20,
    lineHeight: 28,
    color: colors.ink,
  },
  small: {
    ...text.small,
    fontSize: 12,
    lineHeight: 21,
    color: colors.inkMuted,
  },
  centerText: {
    textAlign: 'center',
  },
  card: {
    gap: spacing.sm,
    padding: spacing.lg,
    borderWidth: 1.5,
    borderColor: colors.paperEdge,
    borderRadius: radius.card,
    backgroundColor: colors.background,
  },
  timelineLabelRow: {
    height: 22,
  },
  finishLabel: {
    position: 'absolute',
    bottom: 0,
    transform: [{ translateX: '-100%' }],
    paddingRight: 4,
    ...text.label,
    fontSize: 12,
    lineHeight: 21,
    color: '#7A5A12',
  },
  timeline: {
    height: 12,
    borderRadius: 6,
    overflow: 'hidden',
    backgroundColor: colors.borderWarm,
  },
  timelineStudy: {
    height: 12,
    backgroundColor: colors.gold,
  },
  timelineEnds: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  tip: {
    gap: 6,
    padding: spacing.lg,
    paddingVertical: 14,
    borderWidth: 1.5,
    borderColor: colors.paperEdge,
    borderRadius: 14,
    backgroundColor: colors.paper,
  },
  tipHead: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  tipLabel: {
    ...text.label,
    fontSize: 13,
    color: colors.lacquer,
  },
  tipText: {
    ...text.small,
    fontSize: 14,
    lineHeight: 25,
    color: colors.ink,
  },
  primaryButton: {
    height: 54,
    marginTop: spacing.sm,
    borderRadius: radius.control,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.ink,
  },
  primaryText: {
    fontFamily: fonts.burmeseBold,
    fontSize: 17,
    lineHeight: 28,
    color: colors.onInk,
  },
});
