import { useState } from 'react';
import { ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { resetProgress } from '@/api';
import { Button, Message, ScreenHeader } from '@/components/settings/SettingsUI';
import { colors, fonts, radius, spacing, text } from '@/theme';
import { errorMessage } from '@/utils/errors';

const CLEARED = ['ပြီးခဲ့သော ယူနစ်', 'စာမေးပွဲငယ် ရလဒ်', 'စမ်းသပ်စာမေးပွဲ ရလဒ်', '合格予測'];
const KEPT = ['အကောင့်', 'ဆက်တင်', 'မှတ်ထားသော စကားလုံး'];

// Reset all progress (#37): start a new round from Session 1. Old results are kept as history.
export default function ResetScreen() {
  const [typed, setTyped] = useState('');
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const confirmed = typed.trim() === 'RESET';

  async function reset() {
    setProblem(null);
    setBusy(true);
    try {
      await resetProgress();
      router.replace('/plan'); // the plan is recalculated from today
    } catch (error) {
      setBusy(false);
      setProblem(errorMessage(error));
    }
  }

  return (
    <SafeAreaView style={styles.screen}>
      <ScreenHeader title="တိုးတက်မှုအားလုံး ပြန်စမည်" />
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.warning}>
          <Text style={styles.warningTitle}>အပိုင်း ၁ ကနေ အစက ပြန်စပါမယ်</Text>
          <Text style={styles.warningText}>
            合格予測 အသစ်ရဖို့ သင်ခန်းစာ၊ စာမေးပွဲငယ်နဲ့ စမ်းသပ်စာမေးပွဲ အားလုံးကို ပြန်ဖြေရပါမယ်။
          </Text>
        </View>

        <View style={styles.lists}>
          <List title="ရှင်းလင်းမည်" color={colors.wrong} items={CLEARED} />
          <List title="ထိန်းထားမည်" color={colors.correct} items={KEPT} />
        </View>
        <Text style={styles.note}>ယခင် ရလဒ်တွေကို မဖျက်ဘဲ သိမ်းထားပါတယ်။ လေ့လာမှု အစီအစဉ်ကို ယနေ့ကစပြီး ပြန်တွက်ပါမယ်။</Text>

        <View style={styles.field}>
          <Text style={styles.label}>
            သေချာရင် <Text style={styles.code}>RESET</Text> လို့ ရိုက်ပါ
          </Text>
          <TextInput value={typed} onChangeText={setTyped} autoCapitalize="characters" autoCorrect={false} style={styles.input} />
        </View>

        {problem && <Message text={problem} />}
        <Button label="ပြန်စမည်" kind="danger" onPress={reset} busy={busy} disabled={!confirmed} />
        <Button label="မလုပ်တော့ပါ" kind="secondary" onPress={() => router.back()} />
      </ScrollView>
    </SafeAreaView>
  );
}

function List({ title, color, items }: { title: string; color: string; items: string[] }) {
  return (
    <View style={styles.list}>
      <Text style={[styles.listTitle, { color }]}>{title}</Text>
      {items.map((item) => (
        <Text key={item} style={styles.listItem}>
          • {item}
        </Text>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { gap: 14, padding: spacing.lg, paddingBottom: spacing.xxl, width: '100%', maxWidth: 520, alignSelf: 'center' },
  warning: { alignItems: 'center', gap: 4, padding: spacing.lg, borderRadius: radius.card, backgroundColor: colors.wrongBg },
  warningTitle: { fontFamily: fonts.burmeseSerif, fontSize: 19, lineHeight: 40, color: colors.wrong, textAlign: 'center' },
  warningText: { ...text.small, fontSize: 14, lineHeight: 25, color: '#6E2A24', textAlign: 'center' },
  lists: { flexDirection: 'row', gap: 10 },
  list: { flex: 1, padding: spacing.md, borderWidth: 1.5, borderColor: colors.divider, borderRadius: 14 },
  listTitle: { ...text.label, fontSize: 13 },
  listItem: { ...text.small, fontSize: 14, lineHeight: 25, color: colors.ink },
  note: { ...text.small, fontSize: 13, lineHeight: 23, color: colors.inkMuted },
  field: { gap: spacing.xs },
  label: { ...text.label, color: colors.ink },
  code: { fontFamily: fonts.japaneseBold },
  input: {
    height: 50,
    paddingHorizontal: spacing.lg,
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: radius.control,
    fontFamily: fonts.japaneseBold,
    fontSize: 16,
    letterSpacing: 2,
    color: colors.ink,
  },
});
