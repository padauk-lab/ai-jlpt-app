import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { getMe } from '@/api';
import { colors, fonts, spacing, text } from '@/theme';
import { errorMessage } from '@/utils/errors';

// The first screen (contract #1): who is logged in, and is setup done?
// No login → Login. Setup not done → First-time setup. Otherwise → Home.
export default function Index() {
  const [problem, setProblem] = useState<string | null>(null);

  async function decide() {
    setProblem(null);
    try {
      const me = await getMe();
      if (!me) router.replace('/login');
      else router.replace(me.onboarding_completed ? '/home' : '/setup');
    } catch (error) {
      setProblem(errorMessage(error));
    }
  }

  useEffect(() => {
    decide();
  }, []);

  return (
    <View style={styles.screen}>
      {problem ? (
        <>
          <Text style={styles.message}>{problem}</Text>
          <Pressable onPress={decide} style={styles.retry}>
            <Text style={styles.retryText}>ပြန်ကြိုးစားမည်</Text>
          </Pressable>
        </>
      ) : (
        <ActivityIndicator color={colors.ink} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.lg,
    padding: spacing.xl,
    backgroundColor: colors.goldSoft,
  },
  message: {
    ...text.body,
    color: colors.ink,
    textAlign: 'center',
  },
  retry: {
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderRadius: 10,
    backgroundColor: colors.ink,
  },
  retryText: {
    fontFamily: fonts.burmeseBold,
    fontSize: 16,
    lineHeight: 28,
    color: colors.onInk,
  },
});
