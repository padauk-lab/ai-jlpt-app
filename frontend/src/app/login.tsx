import { useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { ApiError, login, register } from '@/api';
import { Logo } from '@/components/Logo';
import { RubyText, type RubyPiece } from '@/components/RubyText';
import { colors, fonts, radius, spacing, text } from '@/theme';
import { errorMessage } from '@/utils/errors';

const TAGLINE: RubyPiece[] = [
  { text: '小', reading: 'ちい' },
  { text: 'さな' },
  { text: '継続', reading: 'けいぞく' },
  { text: 'が、' },
  { text: '大', reading: 'おお' },
  { text: 'きな' },
  { text: '到達', reading: 'とうたつ' },
  { text: 'になる。' },
];

type Mode = 'login' | 'register';
type FieldErrors = { username?: string; email?: string; password?: string };

const USERNAME_RULE = /^[A-Za-z0-9_]{3,20}$/;

export default function LoginScreen() {
  const [mode, setMode] = useState<Mode>('login');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const isRegister = mode === 'register';

  function switchMode(next: Mode) {
    setMode(next);
    setMessage(null);
    setFieldErrors({});
  }

  // The same rules as the backend (#2). The backend still checks everything itself.
  function checkFields(): FieldErrors {
    const found: FieldErrors = {};
    if (isRegister && !USERNAME_RULE.test(username)) found.username = 'စာလုံး 3 မှ 20 ၊ အင်္ဂလိပ်စာ၊ ဂဏန်းနှင့် _ သာ ရပါတယ်။';
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) found.email = 'အီးမေးလ် ပုံစံ မမှန်ပါ။';
    if (isRegister && password.length < 8) found.password = 'စာလုံး 8 လုံး အနည်းဆုံး လိုပါတယ်။';
    if (!isRegister && password.length === 0) found.password = 'စကားဝှက် ထည့်ပါ။';
    return found;
  }

  async function handleSubmit() {
    setMessage(null);
    const found = checkFields();
    setFieldErrors(found);
    if (Object.keys(found).length > 0) return;

    setBusy(true);
    try {
      const me = isRegister ? await register(email.trim(), username, password) : await login(email.trim(), password);
      router.replace(me.onboarding_completed ? '/home' : '/setup');
    } catch (error) {
      if (error instanceof ApiError && error.code === 'email_taken') setFieldErrors({ email: errorMessage(error) });
      else if (error instanceof ApiError && error.code === 'username_taken') setFieldErrors({ username: errorMessage(error) });
      else setMessage(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <View style={styles.logoTile}>
            <Logo size={70} />
          </View>
          <Text style={styles.appName}>急合</Text>
          <View style={styles.goldBar} />
          <RubyText ruby={TAGLINE} size={16} />
          <Text style={styles.taglineMy}>နေ့စဉ် လေ့လာမှု အသေးအဖွဲများ၊ ကြီးမားသော တိုးတက်မှု။</Text>
        </View>

        <View style={styles.tabs}>
          <Tab label="အကောင့်ဝင်မည်" active={!isRegister} onPress={() => switchMode('login')} />
          <Tab label="အကောင့်သစ်ဖွင့်မည်" active={isRegister} onPress={() => switchMode('register')} />
        </View>

        {isRegister && (
          <View style={styles.field}>
            <Text style={styles.label}>အသုံးပြုသူအမည်</Text>
            <TextInput
              style={styles.input}
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
              autoCorrect={false}
              placeholder="htet_pai"
              placeholderTextColor={colors.inkMuted}
            />
            {fieldErrors.username ? (
              <FieldError message={fieldErrors.username} />
            ) : (
              <Text style={styles.hint}>စာလုံး 3 မှ 20 အထိ၊ အင်္ဂလိပ်စာ၊ ဂဏန်းနှင့် _ သာ</Text>
            )}
          </View>
        )}

        <View style={styles.field}>
          <Text style={styles.label}>အီးမေးလ်</Text>
          <TextInput
            style={styles.input}
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
            autoCorrect={false}
            placeholder="you@example.com"
            placeholderTextColor={colors.inkMuted}
          />
          {fieldErrors.email && <FieldError message={fieldErrors.email} />}
        </View>

        <View style={styles.field}>
          <View style={styles.labelRow}>
            <Text style={styles.label}>စကားဝှက်</Text>
            {!isRegister && (
              <Pressable onPress={() => {}} hitSlop={8}>
                <Text style={styles.link}>မေ့နေပါသလား</Text>
              </Pressable>
            )}
          </View>
          <TextInput
            style={styles.input}
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            autoCapitalize="none"
            autoComplete={isRegister ? 'new-password' : 'current-password'}
          />
          {fieldErrors.password ? (
            <FieldError message={fieldErrors.password} />
          ) : (
            isRegister && <Text style={styles.hint}>အနည်းဆုံး စာလုံး 8 လုံး</Text>
          )}
        </View>

        {message && (
          <View style={styles.banner} accessibilityRole="alert">
            <Text style={styles.bannerText}>{message}</Text>
          </View>
        )}

        <Pressable
          onPress={handleSubmit}
          disabled={busy}
          style={({ pressed }) => [styles.primaryButton, (pressed || busy) && styles.pressed]}
        >
          {busy ? (
            <ActivityIndicator color={colors.onInk} />
          ) : (
            <Text style={styles.primaryButtonText}>{isRegister ? 'အကောင့်သစ်ဖွင့်မည်' : 'အကောင့်ဝင်မည်'}</Text>
          )}
        </Pressable>

        <View style={styles.dividerRow}>
          <View style={styles.dividerLine} />
          <Text style={styles.hint}>သို့မဟုတ်</Text>
          <View style={styles.dividerLine} />
        </View>

        {/* Later: replace with Google's official sign-in button. */}
        <Pressable
          onPress={() => {}}
          style={({ pressed }) => [styles.secondaryButton, pressed && styles.pressed]}
        >
          <Text style={styles.secondaryButtonText}>Google ဖြင့် ဝင်မည်</Text>
        </Pressable>

        <Text style={styles.terms}>
          ဆက်လက်ဆောင်ရွက်ခြင်းဖြင့် အသုံးပြုမှုစည်းမျဉ်းများ ကို လက်ခံပြီးဖြစ်ပါသည်။
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

function FieldError({ message }: { message: string }) {
  return (
    <Text accessibilityRole="alert" style={styles.fieldError}>
      {message}
    </Text>
  );
}

type TabProps = {
  label: string;
  active: boolean;
  onPress: () => void;
};

function Tab({ label, active, onPress }: TabProps) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="tab"
      accessibilityState={{ selected: active }}
      style={[styles.tab, active && styles.tabActive]}
    >
      <Text style={[styles.tabText, active && styles.tabTextActive]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.goldSoft,
  },
  content: {
    paddingHorizontal: 28,
    paddingBottom: spacing.xl,
    gap: spacing.md,
    width: '100%',
    maxWidth: 480,
    alignSelf: 'center',
  },
  header: {
    alignItems: 'center',
    gap: spacing.sm,
    paddingTop: spacing.xxl,
    paddingBottom: spacing.sm,
  },
  logoTile: {
    width: 92,
    height: 92,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: colors.goldDeep,
    borderRadius: radius.logo,
    backgroundColor: colors.background,
  },
  appName: {
    fontFamily: fonts.brand,
    fontSize: 32,
    lineHeight: 42,
    color: colors.brandRed,
  },
  goldBar: {
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.goldDeep,
  },
  taglineMy: {
    ...text.small,
    fontSize: 14,
    lineHeight: 24,
    color: colors.inkMuted,
    textAlign: 'center',
  },
  tabs: {
    flexDirection: 'row',
    borderBottomWidth: 1.5,
    borderBottomColor: colors.dividerWarm,
  },
  tab: {
    flex: 1,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    borderBottomWidth: 3,
    borderBottomColor: 'transparent',
    marginBottom: -1.5,
  },
  tabActive: {
    borderBottomColor: colors.ink,
  },
  tabText: {
    ...text.body,
    fontSize: 15,
    color: colors.inkMuted,
  },
  tabTextActive: {
    fontFamily: fonts.burmeseBold,
    color: colors.ink,
  },
  field: {
    gap: spacing.xs,
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  label: {
    ...text.label,
    color: colors.ink,
  },
  link: {
    ...text.small,
    fontSize: 14,
    color: colors.ink,
    textDecorationLine: 'underline',
  },
  input: {
    height: 50,
    paddingHorizontal: spacing.lg,
    borderWidth: 1.5,
    borderColor: colors.borderWarm,
    borderRadius: radius.control,
    backgroundColor: colors.background,
    fontFamily: fonts.burmese,
    fontSize: 16,
    color: colors.ink,
  },
  fieldError: {
    ...text.label,
    fontSize: 13,
    lineHeight: 23,
    color: colors.wrong,
  },
  banner: {
    padding: spacing.md,
    borderRadius: radius.control,
    backgroundColor: colors.wrongBg,
  },
  bannerText: {
    ...text.small,
    fontSize: 14,
    lineHeight: 25,
    color: '#9E2F29',
  },
  hint: {
    ...text.small,
    color: colors.inkMuted,
  },
  primaryButton: {
    height: 52,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: spacing.xs,
    borderRadius: radius.control,
    backgroundColor: colors.ink,
  },
  primaryButtonText: {
    fontFamily: fonts.burmeseBold,
    fontSize: 17,
    lineHeight: 28,
    color: colors.onInk,
  },
  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: colors.dividerWarm,
  },
  secondaryButton: {
    height: 52,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.borderWarm,
    borderRadius: radius.control,
    backgroundColor: colors.background,
  },
  secondaryButtonText: {
    fontFamily: fonts.burmeseBold,
    fontSize: 16,
    lineHeight: 26,
    color: colors.ink,
  },
  pressed: {
    opacity: 0.85,
  },
  terms: {
    ...text.small,
    color: colors.inkMuted,
    textAlign: 'center',
    marginTop: spacing.sm,
  },
});
