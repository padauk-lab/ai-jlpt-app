import { useState } from 'react';
import { ScrollView, StyleSheet, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { ApiError, changePassword } from '@/api';
import { Button, Message, ScreenHeader } from '@/components/settings/SettingsUI';
import { Notice, useNotice } from '@/components/ui/Notice';
import { TextField } from '@/components/ui/TextField';
import { colors, spacing, text } from '@/theme';
import { errorMessage } from '@/utils/errors';

type FieldErrors = { current?: string; password?: string; confirm?: string };

// Change password (#34). Only email accounts reach this screen (Settings hides it for Google accounts).
export default function ChangePasswordScreen() {
  const [current, setCurrent] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const notice = useNotice();

  async function save() {
    setProblem(null);
    // The same rules as the backend (#34). The backend still checks everything itself.
    const found: FieldErrors = {};
    if (current.length === 0) found.current = 'လက်ရှိ စကားဝှက် ထည့်ပါ။';
    if (password.length < 8) found.password = 'စာလုံး 8 လုံး အနည်းဆုံး လိုပါတယ်။';
    else if (password.length > 128) found.password = 'စာလုံး 128 လုံးထက် မပိုရပါ။';
    if (confirm !== password) found.confirm = 'စကားဝှက် နှစ်ခု မတူပါ။';
    setFieldErrors(found);
    if (Object.keys(found).length > 0) return;

    setBusy(true);
    try {
      await changePassword(current, password); // also saves the new login tokens for this phone
      notice.show('စကားဝှက် ပြောင်းပြီးပါပြီ');
      setTimeout(() => router.back(), 1200);
    } catch (error) {
      setBusy(false);
      if (error instanceof ApiError && error.code === 'wrong_password') setFieldErrors({ current: 'စကားဝှက် မှားနေပါတယ်။' });
      else setProblem(errorMessage(error));
    }
  }

  return (
    <SafeAreaView style={styles.screen}>
      <ScreenHeader title="စကားဝှက် ပြောင်းမည်" />
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <TextField
          label="လက်ရှိ စကားဝှက်"
          value={current}
          onChangeText={setCurrent}
          secureTextEntry
          autoCapitalize="none"
          autoComplete="current-password"
          textContentType="password"
          error={fieldErrors.current}
        />
        <TextField
          label="စကားဝှက် အသစ်"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          autoCapitalize="none"
          autoComplete="new-password"
          textContentType="newPassword"
          maxLength={128}
          hint="အနည်းဆုံး စာလုံး 8 လုံး"
          error={fieldErrors.password}
        />
        <TextField
          label="စကားဝှက် အသစ် ထပ်ရိုက်ပါ"
          value={confirm}
          onChangeText={setConfirm}
          secureTextEntry
          autoCapitalize="none"
          autoComplete="new-password"
          textContentType="newPassword"
          maxLength={128}
          error={fieldErrors.confirm}
          onSubmitEditing={save}
        />

        <Text style={styles.note}>ပြောင်းပြီးရင် တခြားဖုန်းနဲ့ ကွန်ပျူတာတွေမှာ ပြန်ဝင်ရပါမယ်။ ဒီဖုန်းမှာတော့ ဆက်သုံးနိုင်ပါတယ်။</Text>

        {problem && <Message text={problem} />}
        <Button label="စကားဝှက် ပြောင်းမည်" onPress={save} busy={busy} />
        <Button label="မပြောင်းတော့ပါ" kind="secondary" onPress={() => router.back()} />
      </ScrollView>
      <Notice message={notice.message} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { gap: 14, padding: spacing.lg, paddingBottom: spacing.xxl, width: '100%', maxWidth: 520, alignSelf: 'center' },
  note: { ...text.small, fontSize: 13, lineHeight: 23, color: colors.inkMuted },
});
