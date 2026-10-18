import { StyleSheet, Text, View } from 'react-native';
import { colors, fonts } from '@/theme';

// One piece of Japanese text, exactly like the API contract's "ruby" list:
// { "text": "継続", "reading": "けいぞく" } or { "text": "は" }
export type RubyPiece = {
  text: string;
  reading?: string;
};

type Props = {
  ruby: RubyPiece[];
  size?: number;
  color?: string;
  readingColor?: string;
  fontFamily?: string;
};

// Draws each reading (furigana) small, above its kanji.
export function RubyText({
  ruby,
  size = 16,
  color = colors.ink,
  readingColor = colors.inkMuted,
  fontFamily = fonts.japanese,
}: Props) {
  const readingSize = Math.max(8, Math.round(size * 0.5));

  return (
    <View style={styles.row}>
      {ruby.map((piece, index) => (
        <View key={index} style={styles.piece}>
          <Text
            style={{
              fontFamily: fonts.japanese,
              fontSize: readingSize,
              lineHeight: Math.round(readingSize * 1.3),
              color: readingColor,
            }}
          >
            {piece.reading ?? ' '}
          </Text>
          <Text style={{ fontFamily, fontSize: size, lineHeight: Math.round(size * 1.4), color }}>
            {piece.text}
          </Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'flex-end',
    justifyContent: 'center',
  },
  piece: {
    alignItems: 'center',
  },
});
