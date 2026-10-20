import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { Example } from '@/api/types';
import { RubyText } from '@/components/RubyText';
import { SparkIcon } from '@/components/ui/Icons';
import { colors, spacing, text } from '@/theme';

// Example sentences: Japanese with furigana, then the Burmese translation.
export function Examples({ examples }: { examples: Example[] }) {
  return (
    <View style={styles.list}>
      {examples.map((example, i) => (
        <View key={i} style={styles.item}>
          <RubyText ruby={example.ruby} size={16} align="left" />
          <Text style={styles.translation}>{example.translation_my}</Text>
        </View>
      ))}
    </View>
  );
}

// "More examples" (#27). It asks the AI, so it is marked with a sparkle.
export function MoreExamplesButton({ onPress }: { onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.more, pressed && { opacity: 0.8 }]}>
      <SparkIcon color={colors.lacquer} />
      <Text style={styles.moreText}>ဥပမာ ထပ်ကြည့်မည်</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  list: {
    gap: spacing.md,
  },
  item: {
    gap: 2,
  },
  translation: {
    ...text.small,
    fontSize: 14,
    lineHeight: 24,
    color: colors.inkMuted,
  },
  more: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    height: 36,
    paddingHorizontal: spacing.md,
    borderWidth: 1.5,
    borderColor: '#E2D3B5',
    borderRadius: 18,
    backgroundColor: '#FBF7EE',
  },
  moreText: {
    ...text.label,
    fontSize: 13,
    lineHeight: 22,
    color: colors.lacquer,
  },
});
