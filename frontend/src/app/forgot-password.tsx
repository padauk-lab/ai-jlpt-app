import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useLocalSearchParams } from 'expo-router';
import { forgotPassword, resetPassword } from '@/api';
import { Button, Message, ScreenHeader } from '@/components/settings/SettingsUI';
import { TextField } from '@/components/ui/TextField';
import { colors, fonts, spacing, text } from '@/theme';
import { errorMessage } from '@/utils/errors';

type Step = 'email' | 'code';
type FieldErrors = { email?: string; code?: string; password?: string; confirm?: string };

const EMAIL_RULE = /^\S+@\S+\.\S+$/;

// Forgot password, in two steps:
// 1. the user types their email and we ask for a 6-digit code (#5)
// 2. the user types the code from the email and a new password (#6), then logs in again
export default function ForgotPasswordScreen() {
  const params = useLocalSearchParams<{ email?: string }>();
  const [step, setStep] = useState<Step>('email');
  const [email, setEmail] = useState(params.email ?? '');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');

  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  async function sendCode() {
    setProblem(null);
    setInfo(null);
    if (!EMAIL_RULE.test(email.trim())) {
      setFieldErrors({ email: 'အီးမေးလ် ပုံစံ မမှန်ပါ။' });
      return;
    }
    setFieldErrors({});
    setBusy(true);
    try {
      await forgotPassword(email.trim());
      // The backend gives the same answer for every email, so we never say whether an account exists.
      setInfo(step === 'code' ? 'ကုဒ်အသစ် ပို့ပြီးပါပြီ။ အရင်ကုဒ်က အလုပ်မလုပ်တော့ပါ။' : null);
      setCode('');
      setStep('code');
    } catch (error) {
      setProblem(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function savePassword() {
    setProblem(null);
    setInfo(null);
    // The same rules as the backend (#6). The backend still checks everything itself.
    const found: FieldErrors = {};
    if (!/^[0-9]{6}$/.test(code)) found.code = 'ဂဏန်း 6 လုံး ထည့်ပါ။';
    if (password.length < 8) found.password = 'စာလုံး 8 လုံး အနည်းဆုံး လိုပါတယ်။';
    else if (password.length > 128) found.password = 'စာလုံး 128 လုံးထက် မပိုရပါ။';
    if (confirm !== password) found.confirm = 'စကားဝှက် နှစ်ခု မတူပါ။';
    setFieldErrors(found);
    if (Object.keys(found).length > 0) return;

    setBusy(true);
    try {
      await resetPassword(email.trim(), code, password);
      // Every device is signed out now, so the user logs in with the new password.
      router.replace({ pathname: '/login', params: { reset: '1', email: email.trim() } });
    } catch (error) {
      setBusy(false);
      setProblem(errorMessage(error));
    }
  }

  function changeEmail() {
    setStep('email');
    setProblem(null);
    setInfo(null);
    setFieldErrors({});
  }

  return (
    <SafeAreaView style={styles.screen}>
      <ScreenHeader title="စကားဝှက် ပြန်သတ်မှတ်မည်" />
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {step === 'email' ? (
          <>
            <Text style={styles.intro}>
              အကောင့်ဖွင့်ခဲ့တဲ့ အီးမေးလ်ကို ထည့်ပါ။ စကားဝှက် ပြန်သတ်မှတ်ဖို့ ဂဏန်း 6 လုံး ကုဒ်ကို ပို့ပေးပါမယ်။
            </Text>
            <TextField
              label="အီးမေးလ်"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
              autoCorrect={false}
              placeholder="you@example.com"
              error={fieldErrors.email}
              onSubmitEditing={sendCode}
            />
            {problem && <Message text={problem} />}
            <Button label="ကုဒ် ပို့မည်" onPress={sendCode} busy={busy} />
          </>
        ) : (
          <>
            <View style={styles.sentBox}>
              <Text style={styles.sentText}>ဒီအီးမေးလ်နဲ့ အကောင့်ရှိရင် ကုဒ်ကို ပို့ပြီးပါပြီ</Text>
              <Text style={styles.email}>{email.trim()}</Text>
              <Text style={styles.sentHint}>ကုဒ်က မိနစ် 15 အတွင်း သက်တမ်းကုန်ပါမယ်။ မတွေ့ရင် Spam ထဲမှာ ကြည့်ပါ။</Text>
            </View>

            <TextField
              label="ကုဒ် (ဂဏန်း 6 လုံး)"
              value={code}
              onChangeText={(value) => setCode(value.replace(/[^0-9]/g, ''))}
              keyboardType="number-pad"
              autoComplete="one-time-code"
              textContentType="oneTimeCode"
              maxLength={6}
              placeholder="000000"
              error={fieldErrors.code}
              style={styles.codeInput}
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
              onSubmitEditing={savePassword}
            />

            {info && <Message text={info} kind="info" />}
            {problem && <Message text={problem} />}
            <Button label="စကားဝှက် အသစ် သတ်မှတ်မည်" onPress={savePassword} busy={busy} />

            <View style={styles.links}>
              <Pressable onPress={sendCode} disabled={busy} hitSlop={8} accessibilityRole="button">
                <Text style={styles.link}>ကုဒ် ပြန်ပို့မည်</Text>
              </Pressable>
              <Pressable onPress={changeEmail} disabled={busy} hitSlop={8} accessibilityRole="button">
                <Text style={styles.link}>အီးမေးလ် ပြောင်းမည်</Text>
              </Pressable>
            </View>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { gap: 14, padding: spacing.lg, paddingBottom: spacing.xxl, width: '100%', maxWidth: 520, alignSelf: 'center' },
  intro: { ...text.small, fontSize: 15, lineHeight: 27, color: colors.inkMuted },
  sentBox: { alignItems: 'center', gap: 2, padding: spacing.lg, borderRadius: 12, backgroundColor: colors.goldSoft },
  sentText: { ...text.small, fontSize: 14, lineHeight: 25, color: colors.ink, textAlign: 'center' },
  email: { fontFamily: fonts.japaneseBold, fontSize: 15, lineHeight: 24, color: colors.ink },
  sentHint: { ...text.small, fontSize: 13, lineHeight: 23, color: colors.inkMuted, textAlign: 'center' },
  codeInput: { fontFamily: fonts.japaneseBold, fontSize: 22, letterSpacing: 8, textAlign: 'center' },
  links: { flexDirection: 'row', justifyContent: 'space-between', paddingTop: spacing.xs },
  link: { ...text.small, fontSize: 14, color: colors.ink, textDecorationLine: 'underline' },
});
