import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { Dashboard, Proverb, SessionDetail } from '@/api/types';
import { OrnateFrame } from '@/components/OrnateFrame';
import { RubyText } from '@/components/RubyText';
import { colors, fonts, spacing, text } from '@/theme';
import { toMyanmarDigits } from '@/utils/myanmar';
import { PredictionRing } from './PredictionRing';

type Props = {
  dashboard: Dashboard;
  session: SessionDetail;
  proverb: Proverb | null;
};

// The top of the Home screen: overall progress, the session name in a gold frame,
// the pass prediction (合格予測) ring, today's goal and the proverb of the day.
export function HomeHeader({ dashboard, session, proverb }: Props) {
  const [showProverb, setShowProverb] = useState(false);
  const { units_done, units_goal } = dashboard.today;

  return (
    <View style={styles.header}>
      <View style={styles.overall}>
        <View style={styles.rowBetween}>
          <Text style={styles.muted}>စုစုပေါင်း တိုးတက်မှု</Text>
          <Text style={styles.overallNumber}>{dashboard.overall_progress}%</Text>
        </View>
        <View style={styles.track}>
          <View style={[styles.fill, { width: `${dashboard.overall_progress}%` }]} />
        </View>
      </View>

      <View style={styles.rowBetween}>
        <View>
          <OrnateFrame label={`အပိုင်း ${toMyanmarDigits(session.number)}`} />
          <Text style={[styles.muted, styles.unitsDone]}>
            ယူနစ် {session.units.length} ခုအနက် {session.units_done} ခု ပြီးပါပြီ
          </Text>
        </View>
        <View style={styles.prediction}>
          <PredictionRing value={dashboard.pass_prediction} />
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
        <Pressable
          onPress={() => setShowProverb((open) => !open)}
          accessibilityRole="button"
          accessibilityState={{ expanded: showProverb }}
          style={styles.leaf}
        >
          <View style={[styles.hole, styles.holeLeft]} />
          <View style={[styles.hole, styles.holeRight]} />
          <View style={styles.leafRow}>
            <Text style={styles.leafLabel}>ယနေ့ ဆိုရိုးစကား</Text>
            <View style={styles.leafDivider} />
            <View style={styles.leafProverb}>
              <RubyText ruby={proverb.ruby} size={17} fontFamily={fonts.brand} />
            </View>
          </View>
          {showProverb && (
            <View style={styles.leafMore}>
              <Text style={styles.proverbMeaning}>{proverb.meaning_my}</Text>
              <Text style={styles.proverbExplain}>{proverb.explanation_my}</Text>
            </View>
          )}
        </Pressable>
      )}
    </View>
  );
}

const LEAF = '#EAD6A2';
const LEAF_EDGE = '#B8914A';

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
  overall: {
    gap: 6,
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  overallNumber: {
    fontFamily: fonts.japaneseBold,
    fontSize: 15,
    color: colors.ink,
  },
  track: {
    height: 9,
    borderRadius: 5,
    backgroundColor: '#EFE9E1',
    overflow: 'hidden',
  },
  fill: {
    height: 9,
    borderRadius: 5,
    backgroundColor: colors.gold,
  },
  muted: {
    ...text.small,
    color: colors.inkMuted,
  },
  unitsDone: {
    paddingLeft: 41,
  },
  prediction: {
    alignItems: 'center',
    gap: 2,
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
  leaf: {
    paddingVertical: 7,
    paddingHorizontal: 32,
    borderRadius: 22,
    borderWidth: 1.5,
    borderColor: LEAF_EDGE,
    backgroundColor: LEAF,
  },
  hole: {
    position: 'absolute',
    top: '50%',
    width: 10,
    height: 10,
    marginTop: -5,
    borderRadius: 5,
    borderWidth: 2,
    borderColor: '#8A6A2E',
    backgroundColor: '#FFFFFF',
  },
  holeLeft: {
    left: 12,
  },
  holeRight: {
    right: 12,
  },
  leafRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  leafLabel: {
    fontFamily: fonts.burmeseSerif,
    fontSize: 12,
    lineHeight: 21,
    color: '#6B2E1A',
  },
  leafDivider: {
    width: 1,
    alignSelf: 'stretch',
    backgroundColor: LEAF_EDGE,
  },
  leafProverb: {
    flex: 1,
    alignItems: 'flex-start',
  },
  leafMore: {
    marginTop: spacing.sm,
    gap: spacing.xs,
  },
  proverbMeaning: {
    ...text.label,
    fontSize: 15,
    lineHeight: 26,
    color: '#3E2A12',
  },
  proverbExplain: {
    ...text.small,
    fontSize: 14,
    lineHeight: 24,
    color: '#3E2A12',
  },
});
