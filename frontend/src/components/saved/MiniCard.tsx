import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { SavedWord } from '@/api/types';
import { colors, fonts, text } from '@/theme';
import { toMyanmarDigits } from '@/utils/myanmar';
import { GOLD, Kanote, LACQUER, PAPER } from './CardFrame';

// A small card in the "all cards" view. Tapping it opens the big flash card.
export function MiniCard({ word, onPress }: { word: SavedWord; onPress: () => void }) {
  const wordText = word.ruby.map((piece) => piece.text).join('');
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`${wordText}၊ ${word.meaning_my}`}
      style={({ pressed }) => [styles.card, pressed && { opacity: 0.85 }]}
    >
      <View style={styles.paper}>
        <Kanote size={22} style={{ left: 3, top: 3 }} />
        <Kanote size={22} style={{ right: 3, bottom: 3, transform: [{ scaleX: -1 }, { scaleY: -1 }] }} />
        <Text style={styles.word} adjustsFontSizeToFit numberOfLines={1}>
          {wordText}
        </Text>
        <Text style={styles.meaning} numberOfLines={2}>
          {word.meaning_my}
        </Text>
        <Text style={styles.source}>
          အပိုင်း {toMyanmarDigits(word.session_number)} ၊ {toMyanmarDigits(word.unit_number)}
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    height: 140,
    padding: 5,
    borderRadius: 12,
    backgroundColor: LACQUER,
  },
  paper: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 8,
    borderWidth: 1,
    borderColor: GOLD,
    borderRadius: 8,
    backgroundColor: PAPER,
  },
  word: {
    fontFamily: fonts.brand,
    fontSize: 28,
    lineHeight: 40,
    color: colors.ink,
  },
  meaning: {
    ...text.small,
    fontSize: 12,
    lineHeight: 21,
    textAlign: 'center',
    color: LACQUER,
  },
  source: {
    ...text.small,
    fontSize: 10,
    lineHeight: 18,
    color: '#8C6A2E',
  },
});
