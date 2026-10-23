import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { ApiError, submitOnboarding } from '@/api';
import type { OnboardingRequest } from '@/api/types';
import { PlanLoading } from '@/components/Loading';
import { Logo } from '@/components/Logo';
import { StudyForm } from '@/components/setup/StudyForm';
import { colors, fonts, spacing, text } from '@/theme';
import { errorMessage } from '@/utils/errors';

// First-time setup (#9): last level, score and exam date.
export default function SetupScreen() {
  const [submitting, setSubmitting] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  async function send(answers: OnboardingRequest) {
    setProblem(null);
    setSubmitting(true);
    try {
      await submitOnboarding(answers);
      router.replace('/plan');
    } catch (error) {
      if (error instanceof ApiError && error.code === 'onboarding_already_done') {
        router.replace('/plan'); // already set up earlier: just show the plan
        return;
      }
      if (error instanceof ApiError && error.status === 401) {
        router.replace('/login');
        return;
      }
      setSubmitting(false);
      setProblem(errorMessage(error));
    }
  }

  if (submitting) return <PlanLoading />;

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <View style={styles.logoTile}>
            <Logo size={48} />
          </View>
          <Text style={styles.title}>မေးခွန်း ၃ ခု ဖြေပေးပါ</Text>
          <Text style={styles.subtitle}>သင့်အတွက် လေ့လာမှု အစီအစဉ်ကို ပြုလုပ်ပေးပါမယ်။</Text>
        </View>
        <StudyForm submitLabel="အစီအစဉ် ပြုလုပ်မည်" problem={problem} onSubmit={send} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.goldSoft,
  },
  content: {
    gap: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xxl,
    width: '100%',
    maxWidth: 520,
    alignSelf: 'center',
  },
  header: {
    alignItems: 'center',
    gap: spacing.sm,
    paddingTop: spacing.xl,
    paddingBottom: spacing.sm,
  },
  logoTile: {
    width: 64,
    height: 64,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: colors.goldDeep,
    borderRadius: 18,
    backgroundColor: colors.background,
  },
  title: {
    fontFamily: fonts.burmeseSerif,
    fontSize: 22,
    lineHeight: 46,
    color: colors.lacquer,
  },
  subtitle: {
    ...text.small,
    fontSize: 14,
    color: colors.inkMuted,
    textAlign: 'center',
  },
});
