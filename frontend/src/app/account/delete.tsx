import { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { ApiError, deleteAccount, getMe } from '@/api';
import { tokens } from '@/api/tokens';
import { Button, Message, ScreenHeader } from '@/components/settings/SettingsUI';
import { colors, fonts, radius, spacing, text } from '@/theme';
import { errorMessage } from '@/utils/errors';

// Delete the account and all its data (#36). Email accounts confirm with their password.
export default function DeleteAccountScreen() {
  const [isEmailUser, setIsEmailUser] = useState(true);
  const [password, setPassword] = useState('');
  const [typed, setTyped] = useState('');
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  useEffect(() => {
    getMe().then((me) => me && setIsEmailUser(me.login_method === 'email'));
  }, []);

  const confirmed = typed.trim() === 'DELETE' && (!isEmailUser || password.length > 0);

  async function remove() {
    setProblem(null);
    setBusy(true);
    try {
      await deleteAccount(isEmailUser ? password : null);
      await tokens.clear(); // the account is gone, so this phone forgets the login
      router.replace('/login');
    } catch (error) {
      setBusy(false);
      setProblem(error instanceof ApiError && error.code === 'wrong_password' ? 'စကားဝှက် မှားနေပါတယ်။' : errorMessage(error));
    }
  }

  return (
    <SafeAreaView style={styles.screen}>
      <ScreenHeader title="အကောင့် ဖျက်မည်" />
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.warning}>
          <Text style={styles.warningTitle}>ဒါကို ပြန်ပြင်လို့ မရပါ</Text>
          <Text style={styles.warningText}>
            အကောင့်နဲ့ လေ့လာခဲ့သမျှ ရလဒ်၊ မှတ်ထားသော စကားလုံး အားလုံး အပြီးတိုင် ပျက်သွားပါမယ်။
          </Text>
        </View>

        {isEmailUser && (
          <View style={styles.field}>
            <Text style={styles.label}>စကားဝှက်</Text>
            <TextInput value={password} onChangeText={setPassword} secureTextEntry autoComplete="current-password" style={styles.input} />
          </View>
        )}

        <View style={styles.field}>
          <Text style={styles.label}>
            သေချာရင် <Text style={styles.code}>DELETE</Text> လို့ ရိုက်ပါ
          </Text>
          <TextInput value={typed} onChangeText={setTyped} autoCapitalize="characters" autoCorrect={false} style={[styles.input, styles.codeInput]} />
        </View>

        {problem && <Message text={problem} />}
        <Button label="အကောင့် အပြီး ဖျက်မည်" kind="danger" onPress={remove} busy={busy} disabled={!confirmed} />
        <Button label="မဖျက်တော့ပါ" kind="secondary" onPress={() => router.back()} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { gap: 14, padding: spacing.lg, paddingBottom: spacing.xxl, width: '100%', maxWidth: 520, alignSelf: 'center' },
  warning: { alignItems: 'center', gap: 4, padding: spacing.lg, borderRadius: radius.card, backgroundColor: colors.wrongBg },
  warningTitle: { fontFamily: fonts.burmeseSerif, fontSize: 19, lineHeight: 40, color: colors.wrong, textAlign: 'center' },
  warningText: { ...text.small, fontSize: 14, lineHeight: 25, color: '#6E2A24', textAlign: 'center' },
  field: { gap: spacing.xs },
  label: { ...text.label, color: colors.ink },
  code: { fontFamily: fonts.japaneseBold },
  input: {
    height: 50,
    paddingHorizontal: spacing.lg,
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: radius.control,
    fontSize: 16,
    color: colors.ink,
  },
  codeInput: { fontFamily: fonts.japaneseBold, letterSpacing: 2 },
});
