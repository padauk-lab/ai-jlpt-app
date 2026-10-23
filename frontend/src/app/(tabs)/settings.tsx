import { useState } from 'react';
import { Pressable, StyleSheet, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { logout } from '@/api';
import { colors, fonts, spacing, text } from '@/theme';

// Placeholder until the Settings design is built. Log out is here already,
// so you can test signing up and logging in with different accounts.
export default function SettingsScreen() {
  const [busy, setBusy] = useState(false);

  async function handleLogout() {
    setBusy(true);
    await logout().catch(() => undefined); // the tokens are cleared on this phone either way
    router.replace('/login');
  }

  return (
    <SafeAreaView style={styles.screen}>
      <Text style={styles.title}>ဆက်တင်</Text>
      <Text style={styles.soon}>မကြာမီ လာပါမည်</Text>
      <Pressable onPress={handleLogout} disabled={busy} style={styles.button}>
        <Text style={styles.buttonText}>{busy ? '…' : 'ထွက်မည်'}</Text>
      </Pressable>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
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
  button: {
    marginTop: spacing.xl,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: 10,
  },
  buttonText: {
    fontFamily: fonts.burmeseBold,
    fontSize: 16,
    lineHeight: 28,
    color: colors.ink,
  },
});
