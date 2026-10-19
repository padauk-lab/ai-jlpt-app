import { StyleSheet, Text, View } from 'react-native';
import type { Grammar } from '@/api/types';
import { WarningIcon } from '@/components/ui/Icons';
import { colors, fonts, radius, spacing, text } from '@/theme';
import { Examples, MoreExamplesButton } from './Examples';

// The grammar pattern of the unit (contract #14, "grammar").
export function GrammarCard({ grammar, onMoreExamples }: { grammar: Grammar; onMoreExamples: () => void }) {
  return (
    <View style={styles.card}>
      <Text style={styles.pattern}>{grammar.pattern}</Text>
      <Text style={styles.meaning}>{grammar.meaning_my}</Text>

      <View style={styles.section}>
        <Text style={styles.sectionLabel}>ပုံစံ</Text>
        <Text style={styles.formula}>{grammar.how_to_use}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionLabel}>သုံးပုံ</Text>
        <Text style={styles.body}>{grammar.how_to_use_my}</Text>
      </View>

      <View style={styles.note}>
        <WarningIcon color="#7A5A12" />
        <View style={styles.noteText}>
          <Text style={styles.noteLabel}>သတိပြုရန်</Text>
          <Text style={styles.noteBody}>{grammar.note_my}</Text>
        </View>
      </View>

      <View style={styles.dotted} />
      <Text style={styles.sectionLabel}>ဥပမာ</Text>
      <Examples examples={grammar.examples} />
      <MoreExamplesButton onPress={onMoreExamples} />
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.md,
    padding: spacing.lg,
    paddingVertical: 18,
    borderWidth: 1.5,
    borderColor: colors.divider,
    borderRadius: radius.card,
    backgroundColor: colors.background,
  },
  pattern: {
    fontFamily: fonts.brand,
    fontSize: 30,
    lineHeight: 44,
    color: colors.ink,
  },
  meaning: {
    ...text.label,
    fontSize: 17,
    lineHeight: 30,
    color: colors.ink,
  },
  section: {
    gap: spacing.xs,
  },
  sectionLabel: {
    ...text.label,
    fontSize: 13,
    color: colors.inkMuted,
  },
  formula: {
    alignSelf: 'flex-start',
    paddingHorizontal: spacing.md,
    paddingVertical: 6,
    borderRadius: 8,
    overflow: 'hidden',
    backgroundColor: '#F3EFEA',
    fontFamily: fonts.japaneseBold,
    fontSize: 15,
    lineHeight: 24,
    color: colors.ink,
  },
  body: {
    ...text.body,
    fontSize: 15,
    lineHeight: 27,
    color: colors.ink,
  },
  note: {
    flexDirection: 'row',
    gap: 10,
    padding: spacing.md,
    borderRadius: 12,
    backgroundColor: colors.goldSoft,
  },
  noteText: {
    flex: 1,
  },
  noteLabel: {
    ...text.label,
    fontSize: 13,
    color: '#7A5A12',
  },
  noteBody: {
    ...text.small,
    fontSize: 14,
    lineHeight: 25,
    color: '#3E2A12',
  },
  dotted: {
    borderTopWidth: 1.5,
    borderStyle: 'dotted',
    borderColor: colors.paperEdge,
  },
});
