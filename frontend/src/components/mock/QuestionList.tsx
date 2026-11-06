import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Button } from '@/components/settings/SettingsUI';
import { colors, fonts, spacing, text } from '@/theme';
import { toMyanmarDigits } from '@/utils/myanmar';

type Props = {
  visible: boolean;
  total: number;
  readingFrom: number; // index where the reading questions start
  current: number; // index
  answered: (index: number) => boolean;
  flagged: (index: number) => boolean;
  onJump: (index: number) => void;
  onSubmit: () => void;
  onClose: () => void;
};

// A sheet with every question as a numbered square: dark = answered, outlined = not yet,
// gold dot = "check later", gold ring = the current one. Tap a number to go there.
export function QuestionList({ visible, total, readingFrom, current, answered, flagged, onJump, onSubmit, onClose }: Props) {
  const answeredCount = Array.from({ length: total }, (_, i) => i).filter(answered).length;

  const cells = (from: number, to: number) => (
    <View style={styles.grid}>
      {Array.from({ length: to - from }, (_, k) => from + k).map((i) => {
        const done = answered(i);
        return (
          <Pressable
            key={i}
            onPress={() => onJump(i)}
            accessibilityRole="button"
            accessibilityLabel={`မေးခွန်း ${i + 1}${done ? '၊ ဖြေပြီး' : ''}${flagged(i) ? '၊ ပြန်ကြည့်ရန်' : ''}`}
            style={[styles.cell, done && styles.cellDone, i === current && styles.cellCurrent]}
          >
            <Text style={[styles.cellText, done && styles.cellTextDone]}>{i + 1}</Text>
            {flagged(i) && <View style={styles.flagDot} />}
          </Pressable>
        );
      })}
    </View>
  );

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose} accessibilityLabel="ပိတ်မည်" />
      <View style={styles.sheet}>
        <View style={styles.handle} />
        <View style={styles.titleRow}>
          <Text style={styles.title}>မေးခွန်းစာရင်း</Text>
          <Text style={styles.count}>
            ဖြေပြီး {toMyanmarDigits(answeredCount)} ၊ မဖြေရသေး {toMyanmarDigits(total - answeredCount)}
          </Text>
        </View>
        <ScrollView contentContainerStyle={styles.body}>
          <Text style={styles.section}>ဝေါဟာရ ၊ သဒ္ဒါ 言語知識 ၁–{toMyanmarDigits(readingFrom)}</Text>
          {cells(0, readingFrom)}
          <Text style={styles.section}>
            စာဖတ် 読解 {toMyanmarDigits(readingFrom + 1)}–{toMyanmarDigits(total)}
          </Text>
          {cells(readingFrom, total)}
          <View style={{ marginTop: spacing.sm }}>
            <Button label="တင်သွင်းမည်" onPress={onSubmit} />
          </View>
        </ScrollView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: 'rgba(42,37,34,0.4)' },
  sheet: {
    maxHeight: '80%',
    paddingTop: spacing.md,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    backgroundColor: colors.background,
  },
  handle: { alignSelf: 'center', width: 44, height: 5, borderRadius: 3, backgroundColor: colors.border },
  titleRow: { flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between', paddingHorizontal: 18, paddingTop: spacing.sm },
  title: { ...text.label, fontSize: 17, lineHeight: 30, color: colors.ink },
  count: { ...text.small, fontSize: 13, color: colors.inkMuted },
  body: { gap: 10, padding: 18, paddingBottom: 34 },
  section: { ...text.label, fontSize: 13, color: '#7A5A12' },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 },
  cell: {
    width: 42,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: 9,
    backgroundColor: colors.background,
  },
  cellDone: { borderColor: colors.ink, backgroundColor: colors.ink },
  cellCurrent: { borderWidth: 2.5, borderColor: colors.gold },
  cellText: { fontFamily: fonts.japaneseBold, fontSize: 14, color: colors.ink },
  cellTextDone: { color: colors.onInk },
  flagDot: {
    position: 'absolute',
    top: -3,
    right: -3,
    width: 10,
    height: 10,
    borderWidth: 2,
    borderColor: '#FFFFFF',
    borderRadius: 6,
    backgroundColor: colors.gold,
  },
});
