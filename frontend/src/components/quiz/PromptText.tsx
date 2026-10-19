import { StyleSheet, Text } from 'react-native';
import type { RubyPiece } from '@/components/RubyText';
import { RubyText } from '@/components/RubyText';
import { colors, fonts } from '@/theme';

// The question sentence. If the contract sends "underline", that part is
// underlined (the word being tested). Readings are drawn when present.
export function PromptText({ ruby, underline }: { ruby: RubyPiece[]; underline?: string }) {
  const hasReadings = ruby.some((piece) => piece.reading);
  if (hasReadings) {
    return <RubyText ruby={ruby} size={22} align="left" />;
  }

  const sentence = ruby.map((piece) => piece.text).join('');
  const at = underline ? sentence.indexOf(underline) : -1;
  if (!underline || at < 0) {
    return <Text style={styles.sentence}>{sentence}</Text>;
  }
  return (
    <Text style={styles.sentence}>
      {sentence.slice(0, at)}
      <Text style={styles.underlined}>{underline}</Text>
      {sentence.slice(at + underline.length)}
    </Text>
  );
}

const styles = StyleSheet.create({
  sentence: {
    fontFamily: fonts.japanese,
    fontSize: 22,
    lineHeight: 40,
    color: colors.ink,
  },
  underlined: {
    fontFamily: fonts.japaneseBold,
    textDecorationLine: 'underline',
  },
});
