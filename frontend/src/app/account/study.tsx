import { useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { getPlan, updateStudySettings } from '@/api';
import type { OnboardingRequest } from '@/api/types';
import { PlanLoading } from '@/components/Loading';
import { StudyForm } from '@/components/setup/StudyForm';
import { Message, ScreenHeader } from '@/components/settings/SettingsUI';
import { colors, spacing } from '@/theme';
import { errorMessage } from '@/utils/errors';

// Change study setup (#29). Saving recalculates the plan, so the app warns first (contract).
export default function StudySettingsScreen() {
  const [examDate, setExamDate] = useState<string | null | undefined>(undefined);
  const [saving, setSaving] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  // The plan (#10) tells us the saved exam date. The contract has no way to read the saved
  // level and score yet, so those two are asked again.
  useEffect(() => {
    getPlan()
      .then((plan) => setExamDate(plan.exam_date))
      .catch(() => setExamDate(null));
  }, []);

  async function save(answers: OnboardingRequest) {
    setProblem(null);
    setSaving(true);
    try {
      await updateStudySettings(answers);
      router.replace('/plan'); // show the new plan
    } catch (error) {
      setSaving(false);
      setProblem(errorMessage(error));
    }
  }

  if (saving) return <PlanLoading />;

  return (
    <SafeAreaView style={styles.screen}>
      <ScreenHeader title="လေ့လာမှု ဆက်တင်" />
      {examDate === undefined ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.ink} />
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <Message
            kind="info"
            text="ပြောင်းလိုက်ရင် လေ့လာမှု အစီအစဉ် (တစ်နေ့ ယူနစ်အရေအတွက်) ကို ယနေ့ကစပြီး ပြန်တွက်ပါမယ်။ လေ့လာပြီးသား ယူနစ်တွေ မပျက်ပါ။"
          />
          <StudyForm initial={{ examDate }} submitLabel="သိမ်းပြီး အစီအစဉ် ပြန်တွက်မည်" problem={problem} onSubmit={save} />
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.goldSoft },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  content: { gap: spacing.md, padding: spacing.lg, paddingBottom: spacing.xxl, width: '100%', maxWidth: 520, alignSelf: 'center' },
});
