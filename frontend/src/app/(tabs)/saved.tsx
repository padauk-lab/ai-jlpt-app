import { StyleSheet, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors, text } from '@/theme';

// Placeholder until this screen is built.
export default function SavedWordsScreen() {
  return (
    <SafeAreaView style={styles.screen}>
      <Text style={styles.title}>မှတ်ထားသော စကားလုံး</Text>
      <Text style={styles.soon}>မကြာမီ လာပါမည်</Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.background,
  },
  title: {
    ...text.title,
    color: colors.ink,
  },
  soon: {
    ...text.body,
    color: colors.inkMuted,
  },
});
